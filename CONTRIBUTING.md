# Contributing

Thanks for taking a look. This document covers how to run the project, how it is
laid out, and how to add to it.

## Requirements

- **Python 3.10 or newer.** The code uses `X | None` type syntax.
- A **GitHub personal access token**. A classic token with no scopes is enough
  for public repositories; it lifts the API budget from 60 requests/hour to
  5,000.

## Setup

Run once:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env`:

```
GITHUB_TOKEN=<your token>
GITHUB_REPO=owner/repo
```

`GITHUB_REPO` is a single `owner/repo`. One repository per warehouse. The marts
aggregate over everything the CSVs hold, so mixing repositories produces numbers
that belong to no project in particular.

## Running the pipeline

Three stages, all from the repository root. Each writes what the next one reads,
so run them in order:

```bash
source .venv/bin/activate

# 1. GitHub API -> data/raw/*.csv
PYTHONPATH=src python src/extract.py

# 2. CSVs -> data/oss_health.duckdb
PYTHONPATH=src python src/transform.py

# 3. DuckDB -> output/*.html
PYTHONPATH=src python -m src.render
```

Open `output/index.html` in a browser to see the result.

Only stage 1 touches the network. While working on a mart or a chart, re-run
stages 2 and 3 alone and leave the CSVs in place. Extraction is the slow part,
since reviews cost one API call per pull request.

## Tests

```bash
source .venv/bin/activate
python -m pytest -q
```

They are not about coverage. They cover the invariants a metric can violate
while still running clean and looking plausible, which are exactly the ones that
get published as if they were true:

- `test_funnel.py`: funnel stages are nested. When they stop being nested the
  conversions still render and stop meaning anything.
- `test_dim_contributors.py`: the fork-to-first-action delta is never negative.
- `test_response_times.py`: a merge counts as a first response, a close without
  a merge does not.
- `test_open_items.py`: response debt is told apart from the team's own backlog.
- `test_staging_timestamps.py`: timestamps enter the warehouse as the UTC GitHub
  sent, not rebased into the machine's local zone.
- `test_maintainers.py`: the maintainer roster is derived consistently, and
  maintainers stay out of behavioural rankings.
- `test_velocity_review.py`: text written by third parties cannot execute on the
  published page.

The SQL tests run the real `Transformer` over a small dataset (`FIXTURE_CSVS` in
`tests/conftest.py`) using the queries in `sql/`, so breaking a mart fails here.
Several tests assert exact totals over that shared fixture; if your case needs a
differently shaped repository, build your own with `build_marts()` rather than
adding rows to the shared one.

## Layout

```
oss-health-metrics/
├── src/
│   ├── extract.py          # orchestrates extraction, writes CSVs
│   ├── transform.py        # CSVs -> DuckDB; owns execution order
│   ├── github_client.py    # GitHub API client, pagination and rate limits
│   ├── http_client.py      # session factory with retry/backoff
│   ├── log.py              # logging setup
│   └── render/
│       ├── __init__.py     # page composition
│       ├── data.py         # mart accessors
│       ├── html.py         # page shell, KPI cards, Plotly wrappers
│       ├── theme.py        # colours, CSS, layout defaults
│       ├── timeline.py     # velocity review panel
│       └── charts/         # one builder per chart, each returns a go.Figure
├── sql/
│   ├── staging/            # read CSVs, cast columns (5 views)
│   └── marts/              # analytical tables (10 tables)
├── tests/
├── data/
│   ├── raw/                # CSVs from extract.py (gitignored)
│   └── oss_health.duckdb   # database (gitignored)
├── output/                 # generated dashboard, published via GitHub Pages
├── METRICS.md              # metric definitions, sources, design decisions
└── CONTRIBUTING.md         # this file
```

### Naming

- `stg_`: staging view. Reads a CSV, casts types, renames columns.
- `fct_`: fact table. Events and activity.
- `dim_`: dimension. Entities such as contributors and maintainers.

### Tables

| Table | What it holds | Rows on `drkrillo/good-first-issues` |
|-------|---------------|--------------------------------------|
| `fct_contributor_events` | one row per event per person, with a link to the event | 632 |
| `fct_response_times` | one row per PR/issue with time to first response | 149 |
| `fct_weekly_pulse` | weekly WIP, throughput and cycle time (Little's Law) | 125 |
| `dim_contributors` | per-person summary: totals, fork delta, bursts, funnel stage | 82 |
| `fct_response_time_summary` | median time to first response by window and item type | 12 |
| `fct_open_items` | open items and who owes the next move | 8 |
| `fct_contributor_absence` | bus factor per window and definition | 8 |
| `fct_change_request_flow` | opened/closed/merged and closure ratio per window | 4 |
| `fct_contributor_counts` | total and active contributors per window | 4 |
| `dim_maintainers` | who has write access, derived from `author_association` | 2 |

## Querying the database directly

```bash
source .venv/bin/activate
python -c "
import duckdb
con = duckdb.connect('data/oss_health.duckdb', read_only=True)
con.sql('SHOW TABLES').show()
con.sql('SELECT * FROM fct_open_items').show()
"
```

## Adding a data source

1. Add `get_x()` to `src/github_client.py`.
2. Add `extract_x()` and `X_FIELDS` to `src/extract.py`.
3. Call it from `extract_all()`.
4. Create `sql/staging/stg_x.sql`, using `{source}` as the placeholder for the
   CSV. Cast timestamps with `::timestamptz AT TIME ZONE 'UTC'`. See
   `stg_issues.sql` for why a plain `::timestamp` is wrong.
5. Register it in `Transformer.STAGING` in `src/transform.py`.
6. Run the full pipeline.

## Adding a metric

1. Create `sql/marts/fct_x.sql`. It may reference staging views and other marts.
   Read the clock through `utc_now()` rather than `current_timestamp`, which is
   timezone-aware and would be compared against naive UTC values.
2. Register it in `Transformer.MARTS` in `src/transform.py`. **Order matters**:
   the list executes top to bottom, so a mart must come after everything it
   selects from.
3. Add an accessor to `src/render/data.py`.
4. Add a builder in `src/render/charts/`, returning a `go.Figure`, and export it
   from `src/render/charts/__init__.py`.
5. Place it on a page in `src/render/__init__.py`. A new page also needs an entry
   in `_PAGES` there and one in `NAV` in `src/render/html.py`.
6. Add a test for the invariant that would break silently.
7. Document it in `METRICS.md`: what it measures, the formal definition it
   follows, and what this implementation decides where the definition is silent.

Step 7 is not paperwork. Most of these metrics come from CHAOSS definitions that
leave real questions open, and the answers this project picked are the part worth
reviewing.

## Style

- SQL lives in `sql/`, never inline in Python.
- Chart builders are pure: they take a DataFrame and return a figure.
- Comments explain why, not what. If a line looks wrong until you know the
  history, write the history down.
