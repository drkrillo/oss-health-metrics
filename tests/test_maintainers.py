"""Who counts as the team, and the two places that answer has to reach.

GitHub hands back no roster, so it is derived from the association it stamps on
comments and reviews.  Two marts depend on getting the same answer:
fct_open_items, to tell response debt from the team's own backlog, and
dim_contributors, to keep maintainers out of the behavioural ranking they would
otherwise sit on top of.

In the shared fixture ``dave`` reviews as OWNER; alice and bob only ever speak
as NONE.
"""

from __future__ import annotations

import pandas as pd

from render.charts.contributors import build_velocity_signals


def test_the_roster_is_who_spoke_with_write_access(marts):
    roster = marts.execute("SELECT author FROM dim_maintainers").fetchall()
    assert [r[0] for r in roster] == ["dave"]


def test_having_contributed_before_does_not_make_you_a_maintainer(marts):
    """GitHub's CONTRIBUTOR means "has landed a change here", not push access.

    Reading it as a role would promote every returning contributor onto the
    team and empty out the response-debt count.
    """
    assert marts.execute(
        "SELECT count(*) FROM dim_maintainers WHERE author IN ('alice', 'bob')"
    ).fetchone()[0] == 0


def test_the_flag_reaches_the_contributor_dimension(marts):
    flags = dict(marts.execute(
        "SELECT author, is_maintainer FROM dim_contributors"
    ).fetchall())
    assert flags["dave"] is True
    assert flags["alice"] is False
    assert flags["carol"] is False


def test_open_items_and_contributors_agree_on_the_roster(marts):
    """The two used to derive it separately, which is one edit from drifting."""
    from_items = marts.execute(
        "SELECT DISTINCT opened_by FROM fct_open_items WHERE opened_by_maintainer"
    ).fetchall()
    from_dim = marts.execute(
        "SELECT author FROM dim_contributors WHERE is_maintainer"
    ).fetchall()
    assert {r[0] for r in from_items} <= {r[0] for r in from_dim}


# -- the ranking ------------------------------------------------------------

def _contributor(author: str, **overrides) -> dict:
    row = dict(
        author=author, is_maintainer=False, minutes_fork_to_first_action=60,
        burst_events=0, total_events=5, min_seconds_between_events=300,
        prs_opened=1, prs_merged=0, comments_made=1, reviews_given=0,
        funnel_stage="pr_opened",
    )
    row.update(overrides)
    return row


def test_the_velocity_chart_leaves_maintainers_out(marts):
    """A maintainer's pace sits far enough out to flatten everyone else.

    On the real repo the owner had 70 closely spaced events against 4 for the
    next account, which squashes the rest of the population into one corner.
    """
    df = pd.DataFrame([
        _contributor("owner", is_maintainer=True, burst_events=70,
                     minutes_fork_to_first_action=1),
        _contributor("fast", burst_events=3,
                     minutes_fork_to_first_action=0),
        _contributor("ordinary", burst_events=0),
    ])
    plotted = {
        n for t in build_velocity_signals(df).data
        for n in (t.hovertext if t.hovertext is not None else [])
    }
    assert plotted == {"fast", "ordinary"}


def test_a_repo_of_nothing_but_maintainers_says_no_data(marts):
    df = pd.DataFrame([_contributor("owner", is_maintainer=True)])
    fig = build_velocity_signals(df)
    assert fig.data == ()
    assert "No fork-to-action data" in fig.layout.annotations[0].text
