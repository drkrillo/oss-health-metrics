"""Data access layer, loads mart tables from DuckDB into DataFrames."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


def _opt_int(value) -> int | None:
    """Cast to int, keeping SQL NULL and pandas NA as None.

    A missing signal has to stay missing all the way to the page: rendering a
    null fork-to-action delta as 0 would put somebody who never forked at the
    top of a list sorted by how fast people act.
    """
    return None if value is None or pd.isna(value) else int(value)


def _fmt_duration(minutes: float | None) -> str:
    """Format a minute count as the largest sensible unit: m / h / d."""
    if minutes is None:
        return "—"
    if minutes < 60:
        return f"{round(minutes)}m"
    if minutes < 1440:
        return f"{minutes / 60:.1f}h"
    return f"{minutes / 1440:.1f}d"


class DashboardData:
    """Read-only connection to the DuckDB analytical store."""

    def __init__(self, db_path: Path) -> None:
        self.con = duckdb.connect(str(db_path), read_only=True)

    def close(self) -> None:
        self.con.close()

    def query(self, sql: str) -> pd.DataFrame:
        return self.con.execute(sql).fetchdf()

    # -- mart accessors -----------------------------------------------------

    @property
    def weekly_pulse(self) -> pd.DataFrame:
        return self.query("SELECT * FROM fct_weekly_pulse ORDER BY week_start")

    @property
    def response_times(self) -> pd.DataFrame:
        return self.query("SELECT * FROM fct_response_times ORDER BY created_at")

    @property
    def open_items(self) -> pd.DataFrame:
        return self.query("SELECT * FROM fct_open_items ORDER BY hours_waiting DESC")

    @property
    def contributor_events(self) -> pd.DataFrame:
        return self.query("SELECT * FROM fct_contributor_events ORDER BY event_at")

    @property
    def contributors(self) -> pd.DataFrame:
        return self.query("SELECT * FROM dim_contributors")

    def contributor_absence(self) -> dict:
        """Bus factor for every (window, definition), nested for the KPI card.

        Shape: {window_key: {definition: {"bus": int|None, "top_pct": float}}}
        so the card can switch client-side without a server.
        """
        rows = self.con.execute(
            "SELECT window_key, definition, bus_factor, top_contributor_pct "
            "FROM fct_contributor_absence"
        ).fetchall()
        out: dict = {}
        for window_key, definition, bus, top_pct in rows:
            out.setdefault(window_key, {})[definition] = {
                "bus": int(bus) if bus is not None else None,
                "top_pct": float(top_pct) if top_pct is not None else None,
            }
        return out

    def change_request_flow(self) -> tuple[dict, dict]:
        """Two window-keyed card dicts: (duration, closure_ratio).

        Values are preformatted for :func:`windowed_kpi_card`.
        """
        rows = self.con.execute(
            "SELECT window_key, opened, closed, merged, closure_ratio, median_merge_minutes "
            "FROM fct_change_request_flow"
        ).fetchall()
        duration: dict = {}
        closure: dict = {}
        for window_key, opened, closed, merged, ratio, minutes in rows:
            duration[window_key] = {
                "value": _fmt_duration(minutes),
                "sub": f"median over {int(merged)} merged" if minutes is not None else "no merges",
            }
            closure[window_key] = {
                "value": f"{ratio:.2f}×" if ratio is not None else "—",
                "sub": f"{int(closed)} closed / {int(opened)} opened",
            }
        return duration, closure

    def response_time_summary(self) -> dict:
        """Median TtFR nested by window then item type, for the 2D KPI card.

        Shape: {window_key: {type_key: {"value": str, "sub": str}}}.
        """
        rows = self.con.execute(
            "SELECT window_key, type_key, n_items, median_hours "
            "FROM fct_response_time_summary"
        ).fetchall()
        out: dict = {}
        for window_key, type_key, n_items, median_hours in rows:
            out.setdefault(window_key, {})[type_key] = {
                "value": _fmt_duration(median_hours * 60 if median_hours is not None else None),
                "sub": f"median over {int(n_items)}",
            }
        return out

    def contributor_counts(self) -> dict:
        """Total vs active contributor counts, nested by window then kind.

        Shape: {window_key: {"total"|"active": {"value": str, "sub": str}}}.
        """
        rows = self.con.execute(
            "SELECT window_key, total_contributors, active_contributors "
            "FROM fct_contributor_counts"
        ).fetchall()
        out: dict = {}
        for window_key, total, active in rows:
            lurkers = int(total) - int(active)
            out[window_key] = {
                "total": {"value": str(int(total)), "sub": f"{lurkers} fork/lurk only"},
                "active": {"value": str(int(active)), "sub": "made a contribution"},
            }
        return out

    def velocity_review(self, min_events: int = 2) -> tuple[list[dict], dict]:
        """Accounts ranked by raw velocity, plus every event behind each one.

        Maintainers are excluded for the same reason the velocity scatter
        excludes them: their volume and pace sit far from everyone else and
        compress the rest.  Accounts with a single event are excluded too, a
        timeline is about the gaps, and one event has none.

        There is deliberately no composite score.  The ordering is one visible
        column, the rest are shown next to it, and the reader is the one who
        draws conclusions.

        Returns ``(accounts, timelines)``, where timelines is keyed by
        ``"repo|author"`` and embedded whole so the panel can switch between
        accounts with no server behind it.
        """
        accounts = self.con.execute(
            "SELECT repo, author, total_events, burst_events, "
            "       min_seconds_between_events, minutes_fork_to_first_action, "
            "       prs_opened, prs_merged, funnel_stage "
            "FROM dim_contributors "
            "WHERE NOT is_maintainer AND total_events >= ? "
            # Fastest fork-to-action first; accounts that never forked have no
            # delta at all and sort last rather than sorting as instant.
            "ORDER BY minutes_fork_to_first_action IS NULL, "
            "         minutes_fork_to_first_action, burst_events DESC",
            [min_events],
        ).fetchdf()

        keys = [f"{r.repo}|{r.author}" for r in accounts.itertuples()]
        rows = [
            {
                "key": key,
                "repo": r.repo,
                "author": r.author,
                "total_events": int(r.total_events),
                "burst_events": int(r.burst_events),
                "min_gap": _opt_int(r.min_seconds_between_events),
                "fork_to_action": _opt_int(r.minutes_fork_to_first_action),
                "prs_opened": int(r.prs_opened),
                "prs_merged": int(r.prs_merged),
                "stage": r.funnel_stage,
                "profile": f"https://github.com/{r.author}",
            }
            for key, r in zip(keys, accounts.itertuples())
        ]

        events = self.con.execute(
            "SELECT repo, author, event_at, event_type, item_number, detail, "
            "       event_url, seconds_since_prev_event "
            "FROM fct_contributor_events "
            "ORDER BY repo, author, event_at"
        ).fetchdf()

        wanted = set(keys)
        timelines: dict[str, list[dict]] = {key: [] for key in keys}
        for e in events.itertuples():
            key = f"{e.repo}|{e.author}"
            if key not in wanted:
                continue
            timelines[key].append({
                "at": e.event_at.strftime("%Y-%m-%d %H:%M:%S"),
                "type": e.event_type,
                "item": _opt_int(e.item_number),
                "detail": None if pd.isna(e.detail) else str(e.detail)[:80],
                "url": None if pd.isna(e.event_url) else e.event_url,
                "gap": _opt_int(e.seconds_since_prev_event),
            })
        return rows, timelines

    def kpis(self) -> dict:
        """Aggregate KPI values for the overview cards."""
        total = self.con.execute(
            "SELECT count(distinct author) FROM dim_contributors"
        ).fetchone()[0]
        waiting = self.con.execute(
            "SELECT count(*) FROM fct_open_items WHERE waiting_on = 'maintainer'"
        ).fetchone()[0]
        median_resp = self.con.execute(
            "SELECT median(hours_to_first_response) FROM fct_response_times "
            "WHERE hours_to_first_response IS NOT NULL"
        ).fetchone()[0]
        cycle = self.con.execute(
            "SELECT cycle_time_weeks FROM fct_weekly_pulse "
            "WHERE cycle_time_weeks IS NOT NULL ORDER BY week_start DESC LIMIT 1"
        ).fetchone()
        repos = self.con.execute(
            "SELECT DISTINCT repo FROM fct_weekly_pulse"
        ).fetchall()
        return {
            "total_contributors": total,
            "waiting_on_maintainer": waiting,
            # A median of 0 is a real answer, most PRs here are merged within
            # the hour, so test for None, not for falsiness.
            "median_response_hours": (
                round(median_resp, 1) if median_resp is not None else "N/A"
            ),
            "cycle_time_weeks": (
                round(cycle[0], 1) if cycle is not None else "N/A"
            ),
            "repos": [r[0] for r in repos],
        }
