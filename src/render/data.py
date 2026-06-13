"""Data access layer — loads mart tables from DuckDB into DataFrames."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


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
            "median_response_hours": round(median_resp, 1) if median_resp else "N/A",
            "cycle_time_weeks": round(cycle[0], 1) if cycle else "N/A",
            "repos": [r[0] for r in repos],
        }
