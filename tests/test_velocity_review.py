"""The velocity panel renders text other people wrote, on a published page.

Two things it must never do: mangle text that came from GitHub, and let text
that came from GitHub run as code.  Issue titles and account logins are written
by whoever opened the issue or made the account.

The rest of these pin the reading: a gap belongs between two events, a missing
signal is not a small one, and no row may exist without the timeline behind it.
"""

from __future__ import annotations

import json
import re

import pytest

from conftest import FIXTURE_CSVS, build_marts
from render.data import DashboardData
from render.timeline import (
    BURST_SECONDS,
    _fmt_gap,
    _fmt_minutes,
    script_json,
    velocity_review_panel,
)


def _account(author: str, key: str | None = None, **overrides) -> dict:
    row = dict(
        key=key or f"acme/widget|{author}", repo="acme/widget", author=author,
        total_events=3, burst_events=0, min_gap=300, fork_to_action=60,
        prs_opened=1, prs_merged=0, stage="pr_opened",
        profile=f"https://github.com/{author}",
    )
    row.update(overrides)
    return row


def _event(at: str, gap: int | None, **overrides) -> dict:
    row = dict(
        at=at, type="comment", item=1, detail="Something",
        url="https://github.com/acme/widget/issues/1#issuecomment-1", gap=gap,
    )
    row.update(overrides)
    return row


ACCOUNTS = [
    _account("fast", fork_to_action=0, burst_events=2, min_gap=4),
    _account("slow", fork_to_action=4000, min_gap=90000),
    _account("neverforked", fork_to_action=None, min_gap=None),
]
TIMELINES = {
    "acme/widget|fast": [
        _event("2026-03-01 10:00:00", None, type="fork", url=None, item=None),
        _event("2026-03-01 10:00:04", 4),
        _event("2026-03-01 10:00:08", 4),
    ],
    "acme/widget|slow": [
        _event("2026-03-01 10:00:00", None),
        _event("2026-03-05 10:00:00", 345600),
    ],
    "acme/widget|neverforked": [
        _event("2026-03-01 10:00:00", None),
        _event("2026-03-01 11:00:00", 3600),
    ],
}


def _payload(html: str) -> dict:
    return json.loads(re.search(r"var D = (\{.*?\});\n", html, re.S).group(1))


# -- untrusted text ---------------------------------------------------------

def test_a_title_cannot_close_the_script_block_it_is_embedded_in():
    """The published-page version of an XSS: the title is somebody else's."""
    payload = {"detail": "</script><script>alert(1)</script>"}
    assert "</script>" not in script_json(payload)
    assert json.loads(script_json(payload).replace("<\\/", "</")) == payload


def test_the_panel_embeds_a_hostile_title_without_breaking_out():
    hostile = dict(TIMELINES)
    hostile["acme/widget|fast"] = [
        _event("2026-03-01 10:00:00", None, detail="</script><script>alert(1)</script>")
    ]
    html = velocity_review_panel("uid", ACCOUNTS, hostile)
    # Exactly one script block, so nothing closed it early.
    assert html.count("</script>") == 1


def test_a_hostile_login_is_escaped_in_the_table():
    """Inside the JSON the raw string is inert; in the markup it is not."""
    html = velocity_review_panel("uid", [_account("<img src=x onerror=alert(1)>")], {})
    markup = html.split("<script>")[0]
    assert "<img src=x" not in markup
    assert "&lt;img src=x" in markup


def test_the_client_side_escaper_covers_attributes_too():
    """esc() feeds both body text and href="…", so it has to handle quotes.

    Serialising a text node escapes < > & and stops there, which is enough for
    one of those two places.
    """
    html = velocity_review_panel("uid", ACCOUNTS, TIMELINES)
    assert "&quot;" in html and "&#39;" in html


# -- reading the numbers ----------------------------------------------------

def test_a_gap_is_never_rounded_up_into_zero():
    """A four-second gap shown as "0m" reads as a rounding artefact."""
    assert _fmt_gap(4) == "4s"
    assert _fmt_gap(0) == "0s"
    assert _fmt_gap(59) == "59s"
    assert _fmt_gap(60) == "1m"
    assert _fmt_gap(3600) == "1h"
    assert _fmt_gap(86400) == "1d"


def test_a_missing_signal_reads_as_missing_not_as_zero():
    assert _fmt_gap(None) == "—"
    assert _fmt_minutes(None) == "—"
    assert _fmt_minutes(0) == "0s"


def test_the_burst_threshold_matches_the_column_that_counts_them():
    """dim_contributors.burst_events counts gaps under a minute."""
    assert BURST_SECONDS == 60


# -- structure --------------------------------------------------------------

def test_every_row_has_the_timeline_behind_it():
    html = velocity_review_panel("uid", ACCOUNTS, TIMELINES)
    rows = re.findall(r'<tr data-key="([^"]+)"', html)
    payload = _payload(html)
    assert len(rows) == len(ACCOUNTS)
    assert all(key in payload["timelines"] for key in rows)


def test_the_panel_wires_the_script_to_its_own_ids():
    html = velocity_review_panel("velocity", ACCOUNTS, TIMELINES)
    assert 'id="velocity"' in html
    assert 'id="velocity-detail"' in html


def test_the_repo_is_named_only_when_more_than_one_is_in_play():
    one = velocity_review_panel("uid", ACCOUNTS, TIMELINES)
    assert "tl-repo" not in one
    several = velocity_review_panel("uid", ACCOUNTS, TIMELINES, multi_repo=True)
    assert "tl-repo" in several


def test_an_empty_review_explains_itself_instead_of_rendering_a_dead_panel():
    html = velocity_review_panel("uid", [], {})
    assert "<table" not in html
    assert "No non-maintainer account" in html


# -- the data layer ---------------------------------------------------------

@pytest.fixture(scope="module")
def dash(tmp_path_factory) -> DashboardData:
    base = tmp_path_factory.mktemp("velocity")
    build_marts(base, FIXTURE_CSVS).close()
    data = DashboardData(base / "test.duckdb")
    yield data
    data.close()


def test_maintainers_are_left_out_of_the_review(dash):
    accounts, _ = dash.velocity_review()
    # dave reviews as OWNER, so the roster picks him up.
    assert "dave" not in {a["author"] for a in accounts}


def test_an_account_with_no_gap_to_show_is_left_out(dash):
    """A timeline is about the gaps, and one event has none."""
    accounts, timelines = dash.velocity_review(min_events=4)
    assert {a["author"] for a in accounts} == {"alice"}
    assert all(len(timelines[a["key"]]) >= 4 for a in accounts)


def test_accounts_that_never_forked_sort_last_not_fastest(dash):
    """A null delta is not a zero one, and zero is the top of this list."""
    accounts, _ = dash.velocity_review()
    deltas = [a["fork_to_action"] for a in accounts]
    measured = [d for d in deltas if d is not None]
    assert deltas == measured + [None] * (len(deltas) - len(measured))
    assert None in deltas, "erin never forked, so she has no delta"


def test_each_event_carries_the_link_to_itself(dash):
    _, timelines = dash.velocity_review()
    events = [e for t in timelines.values() for e in t]
    assert events, "fixture should produce events"
    for event in events:
        if event["type"] != "fork":
            assert event["url"].startswith("https://github.com/")


def test_the_gap_between_consecutive_events_is_carried_through(dash):
    """carol forked and opened a PR 30 seconds later, the whole point."""
    _, timelines = dash.velocity_review()
    carol = timelines["acme/widget|carol"]
    assert carol[0]["gap"] is None, "the first event has nothing to compare to"
    assert carol[1]["gap"] == 30
