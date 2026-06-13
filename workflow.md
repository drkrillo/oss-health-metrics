# oss-health-metrics — Workflow

## Estructura del proyecto

```
oss-health-metrics/
├── .env                    # GITHUB_TOKEN y GITHUB_TARGETS
├── requirements.txt        # Dependencias Python
├── src/                    # Código Python
│   ├── extract.py          # Orquestador: extrae todo y guarda CSVs
│   ├── transform.py        # CSVs → DuckDB (lee SQL, ejecuta en orden)
│   ├── github_client.py    # Cliente GitHub API con paginación y retry
│   ├── http_client.py      # Session factory con retry/backoff
│   └── log.py              # Logging centralizado
├── sql/                    # Queries SQL (separadas del código Python)
│   ├── staging/            # Lee CSVs, tipifica columnas (5 views)
│   │   ├── stg_issues.sql
│   │   ├── stg_pull_requests.sql
│   │   ├── stg_issue_comments.sql
│   │   ├── stg_pr_reviews.sql
│   │   └── stg_forks.sql
│   └── marts/              # Tablas analíticas (5 tables)
│       ├── fct_contributor_events.sql
│       ├── fct_response_times.sql
│       ├── fct_open_items.sql
│       ├── fct_weekly_pulse.sql
│       └── dim_contributors.sql
├── data/
│   ├── raw/                # CSVs crudos (output de extract.py, gitignored)
│   └── oss_health.duckdb   # Base DuckDB (gitignored)
├── BACKLOG.md              # Métricas, bibliografía, decisiones
└── workflow.md             # Este archivo
```

## Setup (una sola vez)

```bash
cd oss-health-metrics
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env: poner GITHUB_TOKEN y GITHUB_TARGETS
```

## Flujo completo

```bash
source .venv/bin/activate

# 1. Extraer datos de GitHub → CSVs
cd src && python extract.py && cd ..

# 2. Transformar CSVs → DuckDB
cd src && python transform.py && cd ..
```

## Consultar datos

```bash
source .venv/bin/activate
python3 << 'EOF'
import duckdb
con = duckdb.connect('data/oss_health.duckdb', read_only=True)
con.sql('SHOW TABLES').show()
con.sql('SELECT * FROM fct_contributor_events LIMIT 5').show()
EOF
```

## Tablas disponibles

| Tabla | Qué tiene | Rows aprox |
|-------|-----------|------------|
| `fct_contributor_events` | Un row por evento por persona (fork, comment, PR, merge, review) | ~414 |
| `fct_response_times` | Un row por PR + issue con tiempo a primer response | ~112 |
| `fct_open_items` | Items abiertos: quién tiene la pelota (maintainer o contributor) | variable |
| `fct_weekly_pulse` | Serie de tiempo semanal: WIP, throughput, cycle time (Little's Law) | ~semanas |
| `dim_contributors` | Resumen por persona: totales, fork delta, burst count, funnel stage | ~52 |

## Agregar una nueva fuente de datos

1. Agregar `get_xxx()` en `src/github_client.py`
2. Agregar `extract_xxx()` + `XXX_FIELDS` en `src/extract.py`
3. Agregar llamada en `extract_all()`
4. Crear `sql/staging/stg_xxx.sql` (usar `{source}` como placeholder para el CSV)
5. Agregar la entrada en `Transformer.STAGING` en `src/transform.py`
6. Correr flujo completo

## Agregar una nueva transformación

1. Crear `sql/marts/xxx.sql` (puede referenciar staging views y otras mart tables)
2. Agregar la entrada en `Transformer.MARTS` en `src/transform.py` (respetar orden)
3. `cd src && python transform.py`

## Convenciones

- `stg_` = staging view: lee CSV, tipifica, renombra
- `fct_` = fact table: eventos, actividades
- `dim_` = dimension: entidades (contributors)
