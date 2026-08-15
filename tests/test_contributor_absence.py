"""Contributor Absence Factor (bus factor) invariants.

The bus factor is the smallest number of contributors whose combined activity
reaches 50% of the total. It is published as a single scary number, so the ways
it can be quietly wrong all matter:

- counting the wrong events (forks are not contributions; strict is code only)
- crossing the 50% line at the wrong rank
- a window reporting more activity than a strictly larger window contains

Windows are trailing from *today*, so anything but ``all`` depends on the wall
clock and can't carry exact expectations in a fixture with fixed dates. The
exact numbers here are asserted on ``all``; the rest are structural.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def absence(marts) -> dict:
    rows = marts.execute(
        "SELECT window_key, definition, bus_factor, total_contributors, "
        "total_contributions FROM fct_contributor_absence"
    ).fetchall()
    return {
        (w, d): {"bus": bus, "contributors": c, "contributions": n}
        for w, d, bus, c, n in rows
    }


def test_all_normal_matches_hand_count(absence):
    # Non-fork events per author: dave 3 (2 issues + 1 review), alice 3
    # (comment + PR + merge), erin 3 (2 PRs + 1 merge), bob 1, carol 1 = 11.
    # Ranked ties break by author: alice(3), dave(3) → cum 6 ≥ 5.5 at rank 2.
    row = absence[("all", "normal")]
    assert row["contributions"] == 11
    assert row["contributors"] == 5
    assert row["bus"] == 2


def test_all_strict_counts_only_code_work(absence):
    # Strict = PRs opened + merged + reviews: erin 3, alice 2, carol 1, dave 1 = 7.
    row = absence[("all", "strict")]
    assert row["contributions"] == 7
    assert row["contributors"] == 4
    assert row["bus"] == 2


def test_strict_is_a_subset_of_normal(absence):
    # Code work can never total more than all non-fork activity.
    assert absence[("all", "strict")]["contributions"] <= absence[("all", "normal")]["contributions"]


def test_bus_factor_is_within_bounds(absence):
    # At least one person, never more than everyone.
    for row in absence.values():
        assert 1 <= row["bus"] <= row["contributors"]


def test_no_window_exceeds_all_time(absence):
    # A trailing window is a subset of all-time, so it can't hold more activity.
    for (window, definition), row in absence.items():
        assert row["contributions"] <= absence[("all", definition)]["contributions"]
