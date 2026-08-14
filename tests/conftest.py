"""Test fixtures: import path, and a real DuckDB built from a tiny dataset."""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from transform import Transformer  # noqa: E402  — needs the path above

#: A repo small enough to reason about by hand, shaped around the cases that
#: have broken the marts:
#:
#: - ``alice``  was active before forking AND after it (the fork-to-action
#:   delta used to go negative for people like her)
#: - ``bob``    forked after commenting once and never came back
#: - ``carol``  forked and opened a PR 30 seconds later
#: - ``dave``   is the maintainer: never forks, reviews and opens issues
#:
#: Timestamps are UTC with the ``Z`` suffix, exactly as the GitHub API returns
#: them, so staging is exercised on realistic input.
FIXTURE_CSVS = {
    "forks.csv": [
        "repo,author,forked_at",
        "acme/widget,alice,2026-03-01T10:00:00Z",
        "acme/widget,bob,2026-03-01T10:00:00Z",
        "acme/widget,carol,2026-03-01T10:00:00Z",
    ],
    "issues.csv": [
        "repo,number,title,state,author,labels,comments,created_at,closed_at,updated_at",
        "acme/widget,1,Broken thing,open,dave,bug,1,2026-02-01T09:00:00Z,,2026-02-01T09:00:00Z",
        "acme/widget,4,Old thing,closed,dave,,0,2026-01-01T09:00:00Z,2026-01-15T09:00:00Z,2026-01-15T09:00:00Z",
    ],
    "pull_requests.csv": [
        "repo,number,title,state,author,merged_at,created_at,closed_at,updated_at",
        "acme/widget,2,Fix it,closed,alice,2026-03-02T12:00:00Z,2026-03-01T10:30:00Z,2026-03-02T12:00:00Z,2026-03-02T12:00:00Z",
        "acme/widget,3,Another,open,carol,,2026-03-01T10:00:30Z,,2026-03-01T10:00:30Z",
    ],
    "issue_comments.csv": [
        "repo,comment_id,issue_number,author,author_association,created_at,updated_at",
        "acme/widget,100,1,alice,NONE,2026-02-10T08:00:00Z,2026-02-10T08:00:00Z",
        "acme/widget,101,1,bob,NONE,2026-02-15T09:00:00Z,2026-02-15T09:00:00Z",
    ],
    "pr_reviews.csv": [
        "repo,pr_number,review_id,author,author_association,state,submitted_at",
        "acme/widget,2,500,dave,OWNER,APPROVED,2026-03-02T11:00:00Z",
    ],
}


@pytest.fixture(scope="session")
def marts(tmp_path_factory) -> duckdb.DuckDBPyConnection:
    """Run the real transform over FIXTURE_CSVS and hand back a connection.

    Uses the production SQL from ``sql/`` rather than a copy, so a query that
    regresses fails here.
    """
    base = tmp_path_factory.mktemp("marts")
    raw_dir = base / "raw"
    raw_dir.mkdir()
    for name, lines in FIXTURE_CSVS.items():
        (raw_dir / name).write_text("\n".join(lines) + "\n")

    db_path = base / "test.duckdb"
    Transformer(db_path=db_path, raw_dir=raw_dir, sql_dir=ROOT / "sql").run()

    con = duckdb.connect(str(db_path), read_only=True)
    yield con
    con.close()
