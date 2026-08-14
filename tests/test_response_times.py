"""Attending a PR by merging it is a response, and has to be counted as one.

Counting only comments and reviews drops every PR merged without discussion,
which are the fastest ones — so the metric ends up describing the slow tail and
calling it the median.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def prs(marts) -> dict[int, dict]:
    rows = marts.execute(
        "SELECT item_number, first_response_type, hours_to_first_response, "
        "first_response_at FROM fct_response_times WHERE item_type = 'pr'"
    ).fetchall()
    return {
        r[0]: {"type": r[1], "hours": r[2], "at": r[3]} for r in rows
    }


def test_a_merge_with_no_discussion_counts_as_the_first_response(prs):
    # PR #5: opened 09:00, merged 10:00, nobody said a word.
    assert prs[5]["type"] == "merge"
    assert prs[5]["hours"] == 1


def test_an_earlier_review_still_wins_over_the_merge(prs):
    # PR #2: reviewed at 11:00 on the 2nd, merged an hour later.
    assert prs[2]["type"] == "review"


def test_closed_without_merge_or_engagement_stays_unanswered(prs):
    # PR #6 was closed a day later with no comment, no review, no merge.
    # We cannot tell who closed it, so it counts as never answered.
    assert prs[6]["at"] is None
    assert prs[6]["type"] is None
    assert prs[6]["hours"] is None


def test_an_open_pr_nobody_touched_stays_unanswered(prs):
    assert prs[3]["at"] is None
