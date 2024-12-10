<div align="center">

# Modern Data Platform Demo

### PostgreSQL · dbt · Apache Airflow · Power BI · Docker

**Star schema · 9 data quality gates · dbt docs on GitHub Pages**

[![Pipeline](https://github.com/houcem58/modern-data-platform-demo/actions/workflows/pipeline.yml/badge.svg)](https://github.com/houcem58/modern-data-platform-demo/actions/workflows/pipeline.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![dbt](https://img.shields.io/badge/dbt-1.8-orange)](https://www.getdbt.com/)
[![Airflow](https://img.shields.io/badge/Airflow-2.9-green)](https://airflow.apache.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)

</div>

---

> End-to-end sales analytics platform — raw CSV ingestion through a 4-layer dbt pipeline
> to a Power BI semantic layer. Built to demonstrate how modern data engineering teams
> structure, test, and orchestrate analytics pipelines at scale.

---

## The Problem

Analytics teams operating data platforms without a structured transformation layer face
compounding pain: ad-hoc SQL queries duplicated across dashboards, no single source of
truth for revenue figures, no data quality enforcement, and pipelines that break silently
when source schemas change.

The result: finance teams distrust the numbers, engineering teams spend hours debugging
dashboard discrepancies, and product decisions are delayed waiting for "validated" extracts.

---

## The Solution

A production-grade, 4-layer data platform that:

- **Ingests** raw sales data with source-level quality validation (6 gates before anything touches the warehouse)
- **Transforms** through a dbt star schema — clean staging, conformed dimensions, incremental fact table
- **Serves** a consumption layer with pre-computed window functions (rolling revenue, MoM growth, ranking)
- **Orchestrates** a daily Airflow pipeline with email alerting on failure
- **Documents** the full data lineage via dbt-generated docs deployed to GitHub Pages

---

## Architecture

```
CSV / API
    │
    ▼  psycopg2 batch ingestion (ON CONFLICT)
┌──────────────┐
│  raw.sales   │  PostgreSQL 15
└──────┬───────┘
       │  dbt source()
       ▼
┌──────────────┐
│  stg_sales   │  Staging — clean, cast, dedup (ROW_NUMBER on ORDER_ID)
└──────┬───────┘
       │  dbt ref()
       ▼
┌─────────────────────────────────────────────────┐
│  dim_date · dim_geography · dim_product         │
│  dim_channel · dim_priority · fact_sales        │  Marts — star schema
└──────┬──────────────────────────────────────────┘
       │  dbt ref()
       ▼
┌──────────────────────┐
│  sales_performance   │  Consumption — monthly grain + window functions
└──────┬───────────────┘
       │  Import / DirectQuery
       ▼
┌────────────┐
│  Power BI  │  DAX measures · KPI cards · Maps · Trend charts
└────────────┘

All orchestrated by Apache Airflow (daily, 06:00 UTC)
```

See [docs/Architecture.md](docs/Architecture.md) for the full system design including orchestration and incremental strategies.

---

## Business Value

| Without This Platform | With This Platform |
|---|---|
| Revenue figures differ per dashboard | Single `sales_performance` view — one source of truth |
| Schema changes break queries silently | 9 data quality gates catch issues at ingestion |
| Analysts write custom SQL per report | Conformed dims and pre-computed window functions |
| No pipeline visibility | Airflow DAG with success/failure email alerting |
| Data lineage unknown | dbt-generated docs with full column-level lineage |

Designed for teams managing 1M+ transaction datasets where data quality enforcement and
pipeline observability are non-negotiable.

---

## Data Model

Star schema with 5 conformed dimensions:

```
dim_date ──────┐
dim_geography ─┤
dim_product ───┼── fact_sales
dim_channel ───┤
dim_priority ──┘
                └── sales_performance  (consumption grain)
```

See [docs/DataModel.md](docs/DataModel.md) for full schema definitions and column types.

---

## Data Quality Gates

| Gate | Layer |
|---|---|
| Row count > 0 | Source validation |
| NULL ORDER_ID < 1% | Source validation |
| NULL ORDER_DATE < 1% | Source validation |
| No future ORDER_DATE | Source validation |
| SHIP_DATE ≥ ORDER_DATE | Source validation |
| UNITS_SOLD all positive | Source validation |
| not_null / unique on order_id | dbt staging test |
| FK integrity — all 5 dimensions | dbt mart test |
| TOTAL_REVENUE = UNITS_SOLD × UNIT_PRICE | dbt singular test |

---

## Quick Start

### With Makefile

```bash
git clone https://github.com/houcem58/modern-data-platform-demo.git
cd modern-data-platform-demo
cp .env.example .env
make docker-up      # start PostgreSQL, Airflow, pgAdmin
make dbt-run        # run full dbt pipeline
make smoke-test     # validate all 4 schema layers
```

### Manual

```bash
git clone https://github.com/houcem58/modern-data-platform-demo.git
cd modern-data-platform-demo
cp .env.example .env
# Edit .env with your passwords

docker compose up airflow-init   # one-time DB setup + admin user creation
docker compose up -d             # start PostgreSQL, Airflow, pgAdmin
```

Services:
- **Airflow UI:** http://localhost:8080 (credentials from `.env`)
- **pgAdmin:** http://localhost:5050

```bash
pip install -r requirements.txt
python ingestion/load_sales.py --file data/sample/sales_sample.csv

cd dbt
dbt deps
dbt run
dbt test
```

Then trigger the daily pipeline via Airflow UI → DAGs → `sales_platform_pipeline` → **Trigger DAG**.

See [analytics/README.md](analytics/README.md) for Power BI connection setup.

---

## Airflow DAG

Daily pipeline at 06:00 UTC:

```
validate_source → dbt_deps → dbt_staging → dbt_dimensions
    → dbt_fact → dbt_consumption → dbt_test
        → notify_success / notify_failure
```

---

## Power BI Measures

Key DAX measures:

- **Total Revenue / Profit / Gross Margin %**
- **YoY Revenue Growth %** · **MoM Revenue Growth %**
- **Rolling 12M Revenue** · **Rolling 3M Profit**
- **YTD / QTD Revenue**
- **Online Revenue %** · **Avg Shipping Days**

See [analytics/dax_measures.md](analytics/dax_measures.md) for the full DAX library.

---

## Project Structure

```
modern-data-platform-demo/
├── dbt/                          # dbt project (sales_platform)
│   ├── models/
│   │   ├── staging/              # stg_sales — clean & dedup
│   │   ├── marts/                # star schema (5 dims + fact)
│   │   └── consumption/          # sales_performance — monthly grain
│   ├── tests/                    # financial integrity singular tests
│   ├── macros/                   # custom schema override
│   ├── dbt_project.yml
│   └── packages.yml
├── ingestion/
│   ├── load_sales.py             # CSV → raw.sales (batch, ON CONFLICT)
│   └── validate_source.py        # 6 quality gates, SystemExit(1) on fail
├── orchestration/
│   └── dags/
│       └── sales_platform_dag.py # Airflow DAG — full pipeline
├── analytics/
│   ├── README.md                 # Power BI connection guide
│   ├── semantic_model.md         # Column reference
│   └── dax_measures.md           # DAX measure library
├── docs/
│   ├── Architecture.md           # Full platform architecture and orchestration
│   ├── DataModel.md              # Star schema definitions and grain
│   └── BusinessCase.md           # Use cases and business value
├── scripts/
│   ├── init_db.sql               # PostgreSQL schema init
│   └── smoke_test.py             # End-to-end health check
├── data/sample/
│   └── sales_sample.csv          # 50-row synthetic sample
├── Makefile                      # Developer experience shortcuts
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── CHANGELOG.md
├── CONTRIBUTING.md
├── ROADMAP.md
├── SECURITY.md
└── LICENSE                       # Apache 2.0
```

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Storage | PostgreSQL | 15 |
| Transformation | dbt-postgres | 1.8 |
| Orchestration | Apache Airflow | 2.9 |
| Ingestion | Python + psycopg2 | 3.11 / 2.9.9 |
| Containerization | Docker Compose | v3.9 |
| Analytics | Power BI Desktop | 2024.06+ |
| CI/CD | GitHub Actions | — |

---

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/Architecture.md) | Full system design, orchestration, incremental strategies |
| [Data Model](docs/DataModel.md) | Star schema definitions, FK relationships, grain |
| [Business Case](docs/BusinessCase.md) | Target scenarios, ROI framing |
| [Analytics](analytics/README.md) | Power BI connection guide |
| [DAX Measures](analytics/dax_measures.md) | Full DAX measure library |
| [Roadmap](ROADMAP.md) | Planned enhancements |
| [Contributing](CONTRIBUTING.md) | How to contribute |
| [Changelog](CHANGELOG.md) | Version history |

---

## Author

**Houcem Hammami** — Technical Manager, AI & Data Engineering

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com/in/houcem-hammami)
[![Email](https://img.shields.io/badge/Email-houcem0508%40gmail.com-red)](mailto:houcem0508@gmail.com)

---

## License

Copyright 2026 Houcem Hammami. Licensed under the Apache License, Version 2.0 — see [LICENSE](LICENSE).
