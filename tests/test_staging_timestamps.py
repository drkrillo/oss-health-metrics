"""Timestamps must land in the warehouse as the UTC that GitHub sent.

The API returns ``2026-03-01T09:00:00Z``.  ``read_csv_auto`` sniffs a column of
those as TIMESTAMPTZ, and a plain ``::timestamp`` cast then rebases it to
whatever zone the machine happens to be in — 06:00 in Buenos Aires, 09:00 on
the UTC runner that builds the published site.  Nothing crashes; every date on
the dashboard is just quietly wrong by the local offset, and events near
midnight bucket into the wrong day, week and month.

The fixture below is deliberately timed for that: 00:30 UTC is the previous
day anywhere west of Greenwich.
"""

from __future__ import annotations

import datetime

import pytest

from conftest import build_marts

TZ_CSVS = {
    "forks.csv": [
        "repo,author,forked_at",
        "acme/tz,alice,2026-03-02T00:30:00Z",
    ],
    "issues.csv": [
        "repo,number,title,state,author,labels,comments,created_at,closed_at,updated_at",
        "acme/tz,1,Just after midnight UTC,open,alice,,0,2026-03-02T00:30:00Z,,2026-03-02T00:30:00Z",
    ],
    "pull_requests.csv": [
        "repo,number,title,state,author,merged_at,created_at,closed_at,updated_at",
        "acme/tz,2,Merged just after midnight,closed,alice,2026-03-02T00:30:00Z,2026-03-01T09:00:00Z,2026-03-02T00:30:00Z,2026-03-02T00:30:00Z",
    ],
    "issue_comments.csv": [
        "repo,comment_id,issue_number,author,author_association,created_at,updated_at",
        "acme/tz,100,1,bob,NONE,2026-03-02T00:30:00Z,2026-03-02T00:30:00Z",
    ],
    "pr_reviews.csv": [
        "repo,pr_number,review_id,author,author_association,state,submitted_at",
        "acme/tz,2,500,bob,OWNER,APPROVED,2026-03-02T00:30:00Z",
    ],
}

MIDNIGHT_UTC = datetime.datetime(2026, 3, 2, 0, 30)


@pytest.fixture(scope="module")
def tz(tmp_path_factory):
    con = build_marts(tmp_path_factory.mktemp("tz"), TZ_CSVS)
    yield con
    con.close()


@pytest.mark.parametrize(
    ("view", "column"),
    [
        ("stg_forks", "forked_at"),
        ("stg_issues", "created_at"),
        ("stg_issue_comments", "created_at"),
        ("stg_pull_requests", "merged_at"),
        ("stg_pr_reviews", "submitted_at"),
    ],
)
def test_staging_keeps_the_time_github_sent(tz, view, column):
    assert tz.execute(f"SELECT max({column}) FROM {view}").fetchone()[0] == MIDNIGHT_UTC


def test_an_event_after_midnight_utc_stays_on_its_own_day(tz):
    """Rebasing to a western zone would file these under 2026-03-01.

    Every event here happens at 00:30 UTC on the 2nd except ``pr_opened``,
    which is the 09:00 control that should sit on the 1st either way.
    """
    days = tz.execute(
        "SELECT DISTINCT date_trunc('day', event_at)::date "
        "FROM fct_contributor_events WHERE event_type != 'pr_opened'"
    ).fetchall()
    assert {d[0] for d in days} == {datetime.date(2026, 3, 2)}


def test_the_clock_and_the_data_agree_on_what_utc_is(tz):
    """utc_now() is only right if staging is right too — they are one fix."""
    drift = tz.execute(
        "SELECT date_diff('second', utc_now(), now() AT TIME ZONE 'UTC')"
    ).fetchone()[0]
    assert abs(drift) <= 1
