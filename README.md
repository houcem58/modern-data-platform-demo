# Modern Data Platform

[![Pipeline](https://github.com/houcem58/modern-data-platform-demo/actions/workflows/pipeline.yml/badge.svg)](https://github.com/houcem58/modern-data-platform-demo/actions/workflows/pipeline.yml)

> End-to-end sales analytics platform — PostgreSQL · dbt · Apache Airflow · Power BI

A production-grade data platform that ingests raw sales data, transforms it through a star schema, orchestrates daily pipelines, and serves a semantic analytics layer to Power BI.

---

## Architecture

```
CSV / API
    │
    ▼  psycopg2 batch ingestion
┌──────────────┐
│  raw.sales   │  PostgreSQL 15
└──────┬───────┘
       │  dbt source()
       ▼
┌──────────────┐
│  stg_sales   │  Staging — clean, cast, dedup
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

---

## Tech Stack

| Component | Technology |
|---|---|
| Database | PostgreSQL 15 |
| Transformation | dbt-postgres 1.8 |
| Orchestration | Apache Airflow 2.9 |
| Ingestion | Python 3.11 + psycopg2 |
| Containerization | Docker Compose v3.9 |
| Analytics | Power BI Desktop |

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/houcem58/modern-data-platform-demo.git
cd modern-data-platform-demo
cp .env.example .env
# Edit .env with your passwords and SMTP credentials
```

### 2. Start the stack

```bash
docker compose up airflow-init   # one-time DB setup + admin user creation
docker compose up -d             # start PostgreSQL, Airflow, pgAdmin
```

Services:
- **Airflow UI:** http://localhost:8080 (user/pass from `.env`)
- **pgAdmin:** http://localhost:5050

### 3. Load sample data

```bash
pip install psycopg2-binary
python ingestion/load_sales.py --file data/sample/sales_sample.csv
```

### 4. Run dbt transforms

```bash
pip install dbt-postgres
cd dbt
dbt deps
dbt run
dbt test
```

### 5. Trigger the pipeline

In Airflow UI → DAGs → `sales_platform_pipeline` → **Trigger DAG**

Or via CLI:
```bash
airflow dags trigger sales_platform_pipeline
```

### 6. Connect Power BI

See [analytics/README.md](analytics/README.md) for step-by-step Power BI setup.

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
│   ├── Architecture.md           # Full platform architecture
│   └── DataModel.md              # Star schema documentation
├── scripts/
│   ├── init_db.sql               # PostgreSQL schema init
│   └── smoke_test.py             # End-to-end health check
├── data/sample/
│   └── sales_sample.csv          # 50-row synthetic sample
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── LICENSE                       # Apache 2.0
```

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

See [docs/DataModel.md](docs/DataModel.md) for full schema definitions.

---

## Data Quality

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

## Airflow DAG

Daily pipeline at 06:00 UTC:

```
validate_source → dbt_deps → dbt_staging → dbt_dimensions
    → dbt_fact → dbt_consumption → dbt_test
        → notify_success / notify_failure
```

---

## Power BI Measures

Key DAX measures included:

- **Total Revenue / Profit / Gross Margin %**
- **YoY Revenue Growth %**
- **MoM Revenue Growth %**
- **Rolling 12M Revenue**
- **Rolling 3M Profit**
- **YTD / QTD Revenue**
- **Online Revenue %**
- **Avg Shipping Days**

See [analytics/dax_measures.md](analytics/dax_measures.md).

---

## Smoke Test

Verify the full stack after deployment:

```bash
python scripts/smoke_test.py
```

Checks all 4 schema layers (raw → staging → marts → consumption) plus financial integrity and FK constraints.

---

## License

Apache License 2.0 — Copyright 2026 Houcem Hammami

---

## Author

**Houcem Hammami**  
Technical Manager — AI, Data Engineering & Digital Transformation  
[GitHub](https://github.com/houcem58) · [LinkedIn](https://www.linkedin.com/in/houcem-hammami)
