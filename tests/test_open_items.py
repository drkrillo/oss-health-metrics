"""Who has the ball is about response debt, not about who spoke last.

Reading only the last actor's role misfiles every item a maintainer opened.  A
maintainer commenting on their own issue looks identical to a maintainer
replying to a contributor, so the item used to flip to "contributor": it turned
green and left the "Waiting on Maintainer" count even though nobody had been
handed anything.  On a real repo that was five of eight open items.

This repo is shaped around the ownership combinations rather than around
activity, so every branch of the classification has a row.  It is separate from
the shared fixture because several other tests assert exact totals over that
one, and adding items here would move their numbers.
"""

from __future__ import annotations

import duckdb
import pytest

from conftest import build_marts

#: - ``maint``    speaks as OWNER, so the roster derivation picks them up
#: - ``newbie``   and ``outsider`` are NONE throughout
#: - items 1-7 are open; 8 is closed and must not appear at all
OPEN_ITEM_CSVS = {
    "forks.csv": [
        "repo,author,forked_at",
        "acme/gadget,newbie,2026-03-01T08:00:00Z",
    ],
    "issues.csv": [
        "repo,number,title,state,author,labels,comments,created_at,closed_at,updated_at",
        "acme/gadget,1,Outsider asks and nobody answers,open,outsider,,0,2026-03-01T09:00:00Z,,2026-03-01T09:00:00Z",
        "acme/gadget,2,Maintainer backlog nobody touched,open,maint,,0,2026-03-02T09:00:00Z,,2026-03-02T09:00:00Z",
        "acme/gadget,3,Maintainer thinking aloud,open,maint,,1,2026-03-03T09:00:00Z,,2026-03-03T10:00:00Z",
        "acme/gadget,4,Maintainer answers a newcomer,open,maint,,2,2026-03-04T09:00:00Z,,2026-03-04T11:00:00Z",
        "acme/gadget,7,One outsider helps another,open,outsider,,1,2026-03-07T09:00:00Z,,2026-03-07T10:00:00Z",
        "acme/gadget,8,Already handled,closed,outsider,,0,2026-02-01T09:00:00Z,2026-02-02T09:00:00Z,2026-02-02T09:00:00Z",
    ],
    "pull_requests.csv": [
        "repo,number,title,state,author,merged_at,created_at,closed_at,updated_at",
        "acme/gadget,5,Reviewed and waiting on the author,open,newbie,,2026-03-05T09:00:00Z,,2026-03-05T10:00:00Z",
        "acme/gadget,6,Author already pushed back,open,newbie,,2026-03-06T09:00:00Z,,2026-03-06T12:00:00Z",
    ],
    "issue_comments.csv": [
        "repo,comment_id,issue_number,author,author_association,created_at,updated_at",
        "acme/gadget,100,3,maint,OWNER,2026-03-03T10:00:00Z,2026-03-03T10:00:00Z",
        "acme/gadget,101,4,newbie,NONE,2026-03-04T10:00:00Z,2026-03-04T10:00:00Z",
        "acme/gadget,102,4,maint,OWNER,2026-03-04T11:00:00Z,2026-03-04T11:00:00Z",
        "acme/gadget,103,7,newbie,NONE,2026-03-07T10:00:00Z,2026-03-07T10:00:00Z",
        "acme/gadget,104,6,newbie,NONE,2026-03-06T12:00:00Z,2026-03-06T12:00:00Z",
    ],
    "pr_reviews.csv": [
        "repo,pr_number,review_id,author,author_association,state,submitted_at",
        "acme/gadget,5,500,maint,OWNER,CHANGES_REQUESTED,2026-03-05T10:00:00Z",
        "acme/gadget,6,501,maint,OWNER,CHANGES_REQUESTED,2026-03-06T10:00:00Z",
    ],
}


@pytest.fixture(scope="module")
def items(tmp_path_factory) -> dict[int, dict]:
    con: duckdb.DuckDBPyConnection = build_marts(
        tmp_path_factory.mktemp("open_items"), OPEN_ITEM_CSVS
    )
    rows = con.execute(
        "SELECT item_number, waiting_on, opened_by, opened_by_maintainer, "
        "last_actor, outside_interactions, hours_waiting "
        "FROM fct_open_items"
    ).fetchall()
    con.close()
    return {
        r[0]: {
            "waiting_on": r[1], "opened_by": r[2], "opened_by_maintainer": r[3],
            "last_actor": r[4], "outside": r[5], "hours_waiting": r[6],
        }
        for r in rows
    }


def test_closed_items_are_not_open_items(items):
    assert set(items) == {1, 2, 3, 4, 5, 6, 7}


# -- the team owes a reply --------------------------------------------------

def test_an_outsider_item_nobody_answered_is_response_debt(items):
    # #1: opened by an outsider, not one word back.  The whole point of the
    # metric: this is the newcomer who never hears anything.
    assert items[1]["waiting_on"] == "maintainer"
    assert items[1]["last_actor"] is None


def test_an_outsider_speaking_last_puts_the_ball_back_on_the_team(items):
    # #6: the maintainer requested changes, the author answered.
    assert items[6]["waiting_on"] == "maintainer"
    assert items[6]["last_actor"] == "newbie"


def test_a_third_party_answering_still_leaves_the_team_to_act(items):
    # #7: one outsider replied to another.  Nobody on the team has looked.
    assert items[7]["waiting_on"] == "maintainer"


# -- the outsider owes the next move ----------------------------------------

def test_a_review_hands_the_ball_to_the_author(items):
    # #5: the author never commented, so the only outsider signal is that they
    # opened the PR.  That still counts as somebody to hand it to.
    assert items[5]["waiting_on"] == "contributor"
    assert items[5]["outside"] == 0


def test_a_maintainer_answering_a_newcomer_hands_the_ball_over(items):
    # #4: maintainer opened it, a newcomer joined, the maintainer replied.
    assert items[4]["waiting_on"] == "contributor"
    assert items[4]["opened_by_maintainer"] is True
    assert items[4]["outside"] == 1


# -- nobody is being kept waiting -------------------------------------------

def test_an_untouched_maintainer_issue_is_backlog_not_debt(items):
    # #2: the team's own issue, no replies.  Used to inflate the maintainer
    # KPI with the maintainer's own to-do list.
    assert items[2]["waiting_on"] == "nobody"
    assert items[2]["opened_by_maintainer"] is True


def test_a_maintainer_talking_to_themselves_hands_the_ball_to_no_one(items):
    # #3: the regression this whole change is about.  Commenting on your own
    # issue used to read as a handoff to a contributor who was never there.
    assert items[3]["waiting_on"] == "nobody"
    assert items[3]["last_actor"] == "maint"
    assert items[3]["outside"] == 0


# -- clock ------------------------------------------------------------------

def test_waiting_hours_are_measured_in_utc(items):
    """Both ends of the subtraction have to be UTC, and it is easy to fix one.

    Staging used to rebase GitHub's ``Z`` timestamps into the session's zone
    while the clock stayed local, so the two errors cancelled and the hours
    came out right by accident.  Correcting either side on its own reintroduces
    the offset, which is what this pins.
    """
    import datetime

    opened = datetime.datetime(2026, 3, 1, 9, 0, tzinfo=datetime.timezone.utc)
    expected = (
        datetime.datetime.now(datetime.timezone.utc) - opened
    ).total_seconds() / 3600
    # Within an hour of the true UTC delta; a timezone slip is at least 3.
    assert abs(items[1]["hours_waiting"] - expected) < 1
