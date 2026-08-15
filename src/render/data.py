"""Data access layer — loads mart tables from DuckDB into DataFrames."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


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
            # A median of 0 is a real answer — most PRs here are merged within
            # the hour — so test for None, not for falsiness.
            "median_response_hours": (
                round(median_resp, 1) if median_resp is not None else "N/A"
            ),
            "cycle_time_weeks": (
                round(cycle[0], 1) if cycle is not None else "N/A"
            ),
            "repos": [r[0] for r in repos],
        }
