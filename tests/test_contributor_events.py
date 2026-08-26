"""Every event has to be openable, not just locatable.

A timeline saying somebody posted three comments forty seconds apart is a number.
One where each of the three is a link the reader can follow lets them read the
comments and judge for themselves.  The difference is the comment and review id
GitHub returns for free, which this mart used to drop before the render layer
ever saw it.

Shared-fixture ids: comments 100 (alice, issue 1) and 101 (bob, issue 1),
review 500 (dave, PR 2).
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def events(marts) -> list[dict]:
    rows = marts.execute(
        "SELECT author, event_type, item_number, event_id, event_url "
        "FROM fct_contributor_events ORDER BY event_at"
    ).fetchall()
    return [
        {"author": r[0], "type": r[1], "item": r[2], "id": r[3], "url": r[4]}
        for r in rows
    ]


def _one(events, author: str, event_type: str) -> dict:
    matches = [e for e in events if e["author"] == author and e["type"] == event_type]
    assert len(matches) == 1, f"expected exactly one {event_type} by {author}"
    return matches[0]


def test_a_comment_links_to_the_comment_and_not_just_the_thread(events):
    comment = _one(events, "alice", "comment")
    assert comment["id"] == 100
    assert comment["url"] == (
        "https://github.com/acme/widget/issues/1#issuecomment-100"
    )


def test_a_review_links_to_the_review(events):
    review = _one(events, "dave", "review")
    assert review["id"] == 500
    assert review["url"] == (
        "https://github.com/acme/widget/pull/2#pullrequestreview-500"
    )


def test_pull_requests_link_under_pull_and_issues_under_issues(events):
    assert _one(events, "carol", "pr_opened")["url"].endswith("/pull/3")
    opened = {e["item"]: e["url"] for e in events if e["type"] == "issue_opened"}
    assert opened[1].endswith("/issues/1")


def test_a_merge_points_at_the_pull_request(events):
    assert _one(events, "alice", "pr_merged")["url"].endswith("/pull/2")


def test_events_without_an_id_of_their_own_still_link_to_their_item(events):
    """Only comments and reviews carry an id; the rest are the item itself."""
    for event in events:
        if event["type"] in ("issue_opened", "pr_opened", "pr_merged"):
            assert event["id"] is None
            assert event["url"] is not None


def test_a_fork_has_nowhere_honest_to_point(events):
    """The fork is a repo, and it may since have been renamed."""
    fork = _one(events, "bob", "fork")
    assert fork["url"] is None


def test_no_url_is_left_half_built(events):
    """A null id concatenated into a string yields NULL, not a broken anchor."""
    for event in events:
        assert event["url"] is None or "None" not in event["url"]
        assert event["url"] is None or event["url"].startswith("https://github.com/")
