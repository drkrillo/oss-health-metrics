"""Contributor counts: total vs active, per window.

Total is everyone with any activity; active drops fork-only people (a fork is
not a contribution under CHAOSS). So active can never exceed total, and a
window can never hold more people than all-time.

Every person in the shared fixture does more than fork, so it can't show the
fork-only exclusion — that case gets its own tiny transform.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def counts(marts) -> dict:
    rows = marts.execute(
        "SELECT window_key, total_contributors, active_contributors "
        "FROM fct_contributor_counts"
    ).fetchall()
    return {w: {"total": t, "active": a} for w, t, a in rows}


def test_all_window_matches_hand_count(counts):
    # Fixture people: alice, bob, carol, dave, erin — all five did something
    # beyond forking (carol opened a PR), so total and active are both 5.
    assert counts["all"]["total"] == 5
    assert counts["all"]["active"] == 5


def test_active_never_exceeds_total(counts):
    for row in counts.values():
        assert row["active"] <= row["total"]


def test_no_window_holds_more_than_all_time(counts):
    for row in counts.values():
        assert row["total"] <= counts["all"]["total"]
        assert row["active"] <= counts["all"]["active"]


def _build(tmp_path: Path, csvs: dict) -> duckdb.DuckDBPyConnection:
    raw = tmp_path / "raw"
    raw.mkdir()
    for name, lines in csvs.items():
        (raw / name).write_text("\n".join(lines) + "\n")
    from transform import Transformer

    db = tmp_path / "t.duckdb"
    Transformer(db_path=db, raw_dir=raw, sql_dir=ROOT / "sql").run()
    return duckdb.connect(str(db), read_only=True)


def test_a_fork_only_person_counts_as_total_but_not_active(tmp_path):
    # nova only forks; kai forks and opens+merges a PR. Total = 2, active = 1.
    csvs = {
        "forks.csv": [
            "repo,author,forked_at",
            "acme/w,nova,2026-05-01T08:00:00Z",
            "acme/w,kai,2026-05-01T08:00:00Z",
        ],
        "issues.csv": [
            "repo,number,title,state,author,labels,comments,created_at,closed_at,updated_at",
        ],
        "pull_requests.csv": [
            "repo,number,title,state,author,merged_at,created_at,closed_at,updated_at",
            "acme/w,1,Fix,closed,kai,2026-05-02T10:00:00Z,2026-05-02T09:00:00Z,2026-05-02T10:00:00Z,2026-05-02T10:00:00Z",
        ],
        "issue_comments.csv": [
            "repo,comment_id,issue_number,author,author_association,created_at,updated_at",
        ],
        "pr_reviews.csv": [
            "repo,pr_number,review_id,author,author_association,state,submitted_at",
        ],
    }
    con = _build(tmp_path, csvs)
    total, active = con.execute(
        "SELECT total_contributors, active_contributors "
        "FROM fct_contributor_counts WHERE window_key = 'all'"
    ).fetchone()
    con.close()
    assert total == 2
    assert active == 1
