"""Render static HTML dashboard pages from DuckDB mart tables.

Usage:
    PYTHONPATH=src python -m src.render
"""

from __future__ import annotations

import logging
from pathlib import Path

from log import setup_logging

from .charts import (
    build_community_activity,
    build_contributor_scatter,
    build_contributor_timeline,
    build_bot_signals,
    build_funnel,
    build_open_items,
    build_response_times,
    build_weekly_pulse,
)
from .data import DashboardData
from .html import (
    NAV,
    clickable_plotly_div,
    contributor_absence_card,
    kpi_card,
    page_shell,
    plotly_div,
    reset_div_counter,
    time_series_div,
    windowed_kpi_card,
    windowed_kpi_card_2d,
)
from .theme import COLORS

logger = logging.getLogger("oss.render")


# ---------------------------------------------------------------------------
# Page renderers
# ---------------------------------------------------------------------------

def render_index(data: DashboardData) -> str:
    kpis = data.kpis()
    repo_label = ", ".join(kpis["repos"]) if kpis["repos"] else "No data"
    duration, closure = data.change_request_flow()

    body = f"""
<header>
    <h1>{repo_label}</h1>
    <p>OSS Health Dashboard</p>
</header>

<div class="kpi-row">
    {windowed_kpi_card_2d("cnt", "Contributors", data.contributor_counts(),
        secondary=[("total", "Total"), ("active", "Active")],
        color=COLORS["primary"])}
    {kpi_card(kpis["waiting_on_maintainer"], "Waiting on Maintainer", COLORS["danger"])}
    {windowed_kpi_card_2d("ttfr", "Time to First Response", data.response_time_summary(),
        secondary=[("all", "All"), ("pr", "PRs"), ("issue", "Issues")],
        color=COLORS["accent"])}
    {windowed_kpi_card("crd", "Change Request Duration", duration, color=COLORS["purple"])}
    {windowed_kpi_card("crr", "Change Request Closure Ratio", closure, color=COLORS["success"])}
    {contributor_absence_card(data.contributor_absence())}
</div>

<div class="chart-section">
    <div class="section-header">
        <h2>Weekly Pulse &mdash; Little's Law</h2>
        <a class="detail-link" href="weekly_pulse.html">View detail &rarr;</a>
    </div>
    {time_series_div(build_weekly_pulse(data.weekly_pulse), default_months=1)}
</div>

<div class="two-col">
    <div class="chart-section">
        <div class="section-header">
            <h2>Who Has The Ball</h2>
            <a class="detail-link" href="open_items.html">View detail &rarr;</a>
        </div>
        {clickable_plotly_div(build_open_items(data.open_items), "open-items-index")}
    </div>
    <div class="chart-section">
        <div class="section-header">
            <h2>Contributor Funnel</h2>
            <a class="detail-link" href="contributors.html">View detail &rarr;</a>
        </div>
        {plotly_div(build_funnel(data.contributors))}
    </div>
</div>

<div class="chart-section">
    <div class="section-header">
        <h2>Time to First Response</h2>
        <a class="detail-link" href="response_times.html">View detail &rarr;</a>
    </div>
    {time_series_div(build_response_times(data.response_times))}
</div>

<div class="chart-section">
    <div class="section-header">
        <h2>Community Activity</h2>
        <a class="detail-link" href="contributors.html">View detail &rarr;</a>
    </div>
    {time_series_div(build_community_activity(data.contributor_events), default_months=1)}
</div>
"""
    return page_shell(f"{repo_label} — OSS Health", body, NAV)


def render_weekly_pulse(data: DashboardData) -> str:
    body = f"""
<header>
    <h1>Weekly Pulse &mdash; Little's Law</h1>
    <p>Flow view: WIP and throughput per week. Cycle time here is a derived
    <em>estimate</em> (WIP / throughput); the canonical cycle time is the CHAOSS
    Change Request Duration shown on the overview.</p>
</header>
<div class="chart-section">
    {time_series_div(build_weekly_pulse(data.weekly_pulse))}
</div>
"""
    return page_shell("Weekly Pulse — OSS Health", body, NAV)


def render_response_times(data: DashboardData) -> str:
    body = f"""
<header>
    <h1>Time to First Response</h1>
    <p>Monthly <em>median</em> hours from a PR/issue being opened to the first
    response from a real person (author's own actions and bots excluded),
    split by activity type — the CHAOSS-recommended trend view.</p>
</header>
<div class="chart-section">
    {time_series_div(build_response_times(data.response_times))}
</div>
"""
    return page_shell("Response Times — OSS Health", body, NAV)


def render_open_items(data: DashboardData) -> str:
    body = f"""
<header>
    <h1>Who Has The Ball</h1>
    <p>Every open PR and issue — who needs to act next, and how long they've been waiting.</p>
</header>
<div class="chart-section">
    {clickable_plotly_div(build_open_items(data.open_items), "open-items-detail")}
</div>
"""
    return page_shell("Open Items — OSS Health", body, NAV)


def render_contributors(data: DashboardData) -> str:
    body = f"""
<header>
    <h1>Contributors</h1>
    <p>Funnel, behavior landscape, bot signals, and individual timelines.</p>
</header>

<div class="chart-section">
    <h2>Contributor Funnel</h2>
    <p style="color:{COLORS['secondary']};font-size:0.85rem;margin-bottom:12px">
        CHAOSS Conversion Rate developer levels. D0 = forked, D1 = issue /
        comment / review, D2 = opened &amp; merged a PR. Each bar is an
        independent cohort; the percentage is the conversion from the level
        above.</p>
    {plotly_div(build_funnel(data.contributors))}
</div>

<div class="two-col">
    <div class="chart-section">
        <h2>Contributor Landscape</h2>
        {plotly_div(build_contributor_scatter(data.contributors))}
    </div>
    <div class="chart-section">
        <h2>Bot/Agent Detection Signals</h2>
        {plotly_div(build_bot_signals(data.contributors))}
    </div>
</div>

<div class="chart-section">
    <h2>Contributor Journey Timeline</h2>
    {time_series_div(build_contributor_timeline(data.contributor_events))}
</div>
"""
    return page_shell("Contributors — OSS Health", body, NAV)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

_PAGES = [
    ("index.html", render_index),
    ("weekly_pulse.html", render_weekly_pulse),
    ("response_times.html", render_response_times),
    ("open_items.html", render_open_items),
    ("contributors.html", render_contributors),
]


def main() -> None:
    setup_logging()
    base = Path(__file__).resolve().parent.parent.parent
    db_path = base / "data" / "oss_health.duckdb"
    output_dir = base / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading data from %s", db_path)
    data = DashboardData(db_path)
    reset_div_counter()

    for filename, renderer in _PAGES:
        logger.info("Rendering %s...", filename)
        html = renderer(data)
        (output_dir / filename).write_text(html, encoding="utf-8")
        logger.info("  Saved %s (%.1f KB)", filename, len(html) / 1024)

    data.close()
    logger.info("Done. All pages saved to %s", output_dir)
