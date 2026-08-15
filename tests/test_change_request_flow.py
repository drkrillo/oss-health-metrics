"""Change-request flow invariants: CHAOSS Duration and Closure Ratio.

Both are published as headline numbers, so the quiet failure modes matter:

- counting a merge as something other than a close (a merge IS a close)
- a closure ratio that does not equal closed / opened
- duration measured over the wrong population (it is merges only, per CHAOSS)

Windows are trailing from today, so exact expectations live on ``all``; the
rest are structural.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def flow(marts) -> dict:
    rows = marts.execute(
        "SELECT window_key, opened, closed, merged, closure_ratio, "
        "median_merge_minutes FROM fct_change_request_flow"
    ).fetchall()
    return {
        w: {"opened": o, "closed": c, "merged": m, "ratio": r, "median": md}
        for w, o, c, m, r, md in rows
    }


def test_all_window_matches_hand_count(flow):
    # Fixture PRs: #2 alice merged, #5 erin merged, #6 erin closed-no-merge,
    # #3 carol still open. So 4 opened, 3 closed, 2 merged, ratio 3/4 = 0.75.
    row = flow["all"]
    assert row["opened"] == 4
    assert row["closed"] == 3
    assert row["merged"] == 2
    assert row["ratio"] == 0.75


def test_duration_is_the_median_over_merged_only(flow):
    # #2 opened 10:30 merged next day 12:00 = 1530 min; #5 opened 09:00 merged
    # 10:00 = 60 min. Median of the two merges = 795 min.
    assert flow["all"]["median"] == 795


def test_a_merge_is_always_a_close(flow):
    for row in flow.values():
        assert row["merged"] <= row["closed"]


def test_closure_ratio_is_closed_over_opened(flow):
    for row in flow.values():
        if row["opened"] > 0:
            assert row["ratio"] == round(row["closed"] / row["opened"], 2)
        else:
            assert row["ratio"] is None


def test_duration_is_null_when_no_merges(flow):
    for row in flow.values():
        if row["merged"] == 0:
            assert row["median"] is None
