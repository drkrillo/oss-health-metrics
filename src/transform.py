"""Transform raw CSVs into analytical tables using DuckDB.

Reads CSVs from data/raw/, creates staging views and mart tables
in a local DuckDB database. SQL lives in sql/ — this module just
orchestrates execution order and wires CSV paths into staging views.
"""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

logger = logging.getLogger("oss.transform")


class Transformer:
    """Reads raw CSVs and builds analytical tables in DuckDB.

    Parameters
    ----------
    db_path:
        Path to the DuckDB database file.
    raw_dir:
        Directory containing the raw CSV files.
    sql_dir:
        Directory containing the .sql files (with staging/ and marts/ subdirs).
    """

    # Staging views: (view_name, sql_file, csv_file)
    STAGING = [
        ("stg_issues",         "staging/stg_issues.sql",         "issues.csv"),
        ("stg_pull_requests",  "staging/stg_pull_requests.sql",  "pull_requests.csv"),
        ("stg_issue_comments", "staging/stg_issue_comments.sql", "issue_comments.csv"),
        ("stg_pr_reviews",     "staging/stg_pr_reviews.sql",     "pr_reviews.csv"),
        ("stg_forks",          "staging/stg_forks.sql",          "forks.csv"),
    ]

    # Mart tables in dependency order: (table_name, sql_file)
    MARTS = [
        ("fct_contributor_events", "marts/fct_contributor_events.sql"),
        ("fct_response_times",     "marts/fct_response_times.sql"),
        ("fct_open_items",         "marts/fct_open_items.sql"),
        ("fct_weekly_pulse",       "marts/fct_weekly_pulse.sql"),
        ("dim_contributors",       "marts/dim_contributors.sql"),
        ("fct_contributor_absence", "marts/fct_contributor_absence.sql"),
    ]

    def __init__(self, db_path: Path, raw_dir: Path, sql_dir: Path) -> None:
        self._db_path = db_path
        self._raw_dir = raw_dir
        self._sql_dir = sql_dir
        self._con: duckdb.DuckDBPyConnection | None = None

    # -- lifecycle -------------------------------------------------------------

    def _connect(self) -> duckdb.DuckDBPyConnection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._con = duckdb.connect(str(self._db_path))
        return self._con

    def _close(self) -> None:
        if self._con:
            self._con.close()
            self._con = None

    # -- helpers ---------------------------------------------------------------

    def _read_sql(self, relpath: str) -> str:
        """Read a .sql file from the sql/ directory."""
        return (self._sql_dir / relpath).read_text()

    def _run_table(self, name: str, sql: str) -> None:
        """Execute a CREATE TABLE AS statement and log the row count."""
        assert self._con is not None
        self._con.execute(f"DROP TABLE IF EXISTS {name}")
        self._con.execute(f"CREATE TABLE {name} AS\n{sql}")
        count = self._con.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        logger.info("  %-30s %d rows", name, count)

    def _run_view(self, name: str, sql: str) -> None:
        """Execute a CREATE VIEW statement."""
        assert self._con is not None
        self._con.execute(f"DROP VIEW IF EXISTS {name}")
        self._con.execute(f"CREATE VIEW {name} AS\n{sql}")
        logger.info("  %-30s (view)", name)

    # -- pipeline --------------------------------------------------------------

    def _create_staging(self) -> None:
        """Create staging views that read and type-cast raw CSVs."""
        logger.info("Creating staging views...")
        for view_name, sql_file, csv_file in self.STAGING:
            sql = self._read_sql(sql_file)
            csv_path = self._raw_dir / csv_file
            sql = sql.format(source=f"read_csv_auto('{csv_path}')")
            self._run_view(view_name, sql)

    def _create_marts(self) -> None:
        """Create mart tables from staging views."""
        logger.info("Creating mart tables...")
        for table_name, sql_file in self.MARTS:
            sql = self._read_sql(sql_file)
            self._run_table(table_name, sql)

    # -- public API ------------------------------------------------------------

    def run(self) -> None:
        """Execute the full transform pipeline: staging views then mart tables."""
        logger.info("Connecting to %s", self._db_path)
        self._connect()
        try:
            self._create_staging()
            self._create_marts()
            logger.info("Done. All tables created in %s", self._db_path)
        finally:
            self._close()


# -- CLI entrypoint ------------------------------------------------------------

def main() -> None:
    from log import setup_logging
    setup_logging()

    base = Path(__file__).resolve().parent.parent
    transformer = Transformer(
        db_path=base / "data" / "oss_health.duckdb",
        raw_dir=base / "data" / "raw",
        sql_dir=base / "sql",
    )
    transformer.run()


if __name__ == "__main__":
    main()
