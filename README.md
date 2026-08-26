<div align="center">

# oss-health-metrics

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Community health metrics for a GitHub repository, built as static files. Implements
[CHAOSS](https://chaoss.community) metric definitions over Python and DuckDB, and
renders a dashboard you can host on GitHub Pages.

**No server, no database to run, no SaaS.**

</div>

---

## The question it answers

A maintainer can see stars and open issue counts. What they cannot see is whether
anybody is waiting on them, whether newcomers who show up ever come back, and how
much of the project rests on one person.

Those are the questions this measures.

## Live dashboard

**[→ drkrillo.github.io/oss-health-metrics](https://drkrillo.github.io/oss-health-metrics/)**

Regenerated weekly against [drkrillo/good-first-issues](https://github.com/drkrillo/good-first-issues).

---

## What it measures

| page | question |
|---|---|
| **Waiting On You** | which open items owe somebody a reply, and for how long |
| **Weekly Pulse** | WIP, throughput and cycle time as a time series (Little's Law) |
| **Time to First Response** | median hours to a first human reply, by window and item type |
| **Contributors** | the funnel from fork to repeat contributor, and per-account velocity |

Four CHAOSS metrics are implemented directly: Time to First Response, Contributor
Absence Factor, Change Request Duration and Closure Ratio, and Contributor
Conversion Rate.

### Three definitional decisions worth knowing

Implementing a metric definition means deciding what it does not say. These three
changed the numbers enough to be worth stating up front:

**A merge counts as a first response.** Counting only comments dropped 64 of 114
pull requests — the fastest ones — and published the median of what was left.

**Conversion levels are not nested.** CHAOSS developer levels D0/D1/D2 describe
independent cohorts: somebody can comment without ever forking, or land a merge
without a single comment. Accumulating them sums disjoint populations.

**Response debt is not the same as ownership.** An item a maintainer opened and
nobody answered is backlog, not somebody being kept waiting. Reading only the last
actor's role misfiles every one of them.

## Against other tools

| | this | GitHub Insights | issue-metrics | OpenSauced |
|---|---|---|---|---|
| Who has the ball, per open item | yes | no | no | no |
| Contributor timeline, 6 event types | yes | commits only | no | no |
| Time to first response as a trend | yes | no | snapshot | no |
| Little's Law / cycle time | yes | no | no | no |
| Contributor funnel | yes | no | no | partial |
| Per-account velocity signals | yes | no | no | no |
| Runs with no infrastructure | yes | n/a | yes | no, SaaS |

---

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set GITHUB_TOKEN and GITHUB_REPO
```

Then run the three stages:

```bash
PYTHONPATH=src python src/extract.py      # GitHub API  -> data/raw/*.csv
PYTHONPATH=src python src/transform.py    # CSVs        -> data/oss_health.duckdb
PYTHONPATH=src python -m src.render       # DuckDB      -> output/*.html
```

`GITHUB_REPO` is one `owner/repo`. A dashboard describes a single repository: every
mart aggregates over whatever is in the CSVs, so two repositories in one warehouse
would share a funnel, a median and a bus factor that describe neither of them.

## How it works

Three stages, and none of them knows about the others.

```
extract.py     GitHub REST, paginated, rate-limit aware   ->  CSV
transform.py   staging views -> mart tables (DuckDB)      ->  .duckdb
render/        DuckDB -> Plotly + hand-written HTML       ->  output/*.html
```

SQL lives in `sql/`, never inside Python. Staging views type the raw CSVs; ten mart
tables hold the metrics. Adding a metric means adding a `.sql` file and a chart
builder — see [workflow.md](workflow.md).

## Tests

```bash
python -m pytest -q
```

88 tests. They do not chase coverage: each one pins an invariant a metric can
violate while still rendering a plausible chart. The SQL tests run the real
`Transformer` over a small fixture repository using the production queries, so
breaking a mart fails here.

## License

Apache-2.0. See [LICENSE](LICENSE).
