"""Fork-to-first-action is a bot signal, so its scale has to mean something.

A negative delta reads on the chart as the fastest contributor in the repo,
when it actually means the fork was never what triggered the activity.
"""

from __future__ import annotations


def _fork_deltas(marts) -> dict[str, int | None]:
    rows = marts.execute(
        "SELECT author, minutes_fork_to_first_action FROM dim_contributors"
    ).fetchall()
    return dict(rows)


def test_delta_is_never_negative(marts):
    negative = marts.execute(
        "SELECT author, minutes_fork_to_first_action FROM dim_contributors "
        "WHERE minutes_fork_to_first_action < 0"
    ).fetchall()
    assert not negative, f"acted before forking but counted as fast: {negative}"


def test_activity_before_the_fork_does_not_count(marts):
    deltas = _fork_deltas(marts)
    # alice commented on 2026-02-10, forked at 10:00 and opened a PR at 10:30.
    # Only the PR is after the fork.
    assert deltas["alice"] == 30
    # carol forked at 10:00:00 and opened a PR at 10:00:30 — same minute.
    assert deltas["carol"] == 0


def test_forking_without_coming_back_has_no_delta(marts):
    deltas = _fork_deltas(marts)
    # bob only ever commented before forking, so there is nothing to measure.
    assert deltas["bob"] is None
    # dave never forked at all.
    assert deltas["dave"] is None
