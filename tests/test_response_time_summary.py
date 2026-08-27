"""Time to First Response summary invariants, and the bot-exclusion rule.

The summary feeds a single headline number per (item type x window), so the
quiet failures are: an ``all`` type that isn't PRs + issues, a window that
reports more items than all-time, and, the point of the CHAOSS bot filter , 
a bot comment counting as the first response.

The bot case can't ride the shared fixture: adding a bot contributor would move
the exact counts other tests assert. It gets its own tiny transform.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def summary(marts) -> dict:
    rows = marts.execute(
        "SELECT window_key, type_key, n_items, median_hours "
        "FROM fct_response_time_summary"
    ).fetchall()
    return {(w, t): {"n": n, "median": m} for w, t, n, m in rows}


def test_all_type_is_prs_plus_issues(summary):
    # PR #2 and #5 answered, issue #1 answered → 2 + 1 = 3.
    assert summary[("all", "pr")]["n"] == 2
    assert summary[("all", "issue")]["n"] == 1
    assert summary[("all", "all")]["n"] == (
        summary[("all", "pr")]["n"] + summary[("all", "issue")]["n"]
    )


def test_median_present_exactly_when_items_exist(summary):
    for row in summary.values():
        assert (row["median"] is not None) == (row["n"] > 0)


def test_no_window_holds_more_than_all_time(summary):
    for (window, type_key), row in summary.items():
        assert row["n"] <= summary[("all", type_key)]["n"]


# --- bot exclusion (isolated transform) ------------------------------------

def _build(tmp_path: Path, csvs: dict) -> duckdb.DuckDBPyConnection:
    raw = tmp_path / "raw"
    raw.mkdir()
    for name, lines in csvs.items():
        (raw / name).write_text("\n".join(lines) + "\n")
    from transform import Transformer

    db = tmp_path / "t.duckdb"
    Transformer(db_path=db, raw_dir=raw, sql_dir=ROOT / "sql").run()
    return duckdb.connect(str(db), read_only=True)


def test_a_bot_comment_is_not_the_first_response(tmp_path):
    # Issue #1 by maria: a bot comments at 09:05, a human at 15:00. The bot must
    # not count, so the first response is the human's, 6 hours, not 0.
    csvs = {
        "forks.csv": ["repo,author,forked_at", "acme/w,zoe,2026-05-01T08:00:00Z"],
        "issues.csv": [
            "repo,number,title,state,author,labels,comments,created_at,closed_at,updated_at",
            "acme/w,1,Thing,open,maria,,2,2026-05-01T09:00:00Z,,2026-05-01T09:00:00Z",
        ],
        "pull_requests.csv": [
            "repo,number,title,state,author,merged_at,created_at,closed_at,updated_at",
            "acme/w,2,Fix,closed,zoe,2026-05-02T10:00:00Z,2026-05-02T09:00:00Z,2026-05-02T10:00:00Z,2026-05-02T10:00:00Z",
        ],
        "issue_comments.csv": [
            "repo,comment_id,issue_number,author,author_association,created_at,updated_at",
            "acme/w,10,1,github-actions[bot],NONE,2026-05-01T09:05:00Z,2026-05-01T09:05:00Z",
            "acme/w,11,1,juan,NONE,2026-05-01T15:00:00Z,2026-05-01T15:00:00Z",
        ],
        "pr_reviews.csv": [
            "repo,pr_number,review_id,author,author_association,state,submitted_at",
        ],
    }
    con = _build(tmp_path, csvs)
    row = con.execute(
        "SELECT first_response_type, hours_to_first_response "
        "FROM fct_response_times WHERE item_type = 'issue' AND item_number = 1"
    ).fetchone()
    con.close()
    assert row[0] == "comment"
    assert row[1] == 6
