# Runbook — Modern Data Platform

This document covers daily operations, pipeline management, and recovery procedures for
the modern data platform (PostgreSQL + dbt + Airflow + Power BI).

---

## Quick Reference

| Command | Purpose |
|---|---|
| `make docker-up` | Start PostgreSQL + Airflow |
| `make load-data` | Load sample CSV into raw.sales |
| `make dbt-run` | Run full dbt transformation |
| `make dbt-test` | Run dbt data quality tests |
| `make smoke-test` | Run source validation quality gates |
| `make lint` | Run ruff linter |

---

## Normal Daily Operations

### Pipeline execution order

The Airflow DAG runs automatically at 06:00 UTC. Manual trigger:

```bash
# From Airflow UI: DAGs → modern_data_platform → Trigger DAG
# Or via CLI:
docker exec -it airflow-webserver airflow dags trigger modern_data_platform
```

**Expected task sequence and SLA:**

| Task | Expected duration | SLA |
|---|---|---|
| `validate_source` | < 5 s | 30 s |
| `dbt_deps` | < 30 s | 2 min |
| `dbt_staging` | < 60 s | 5 min |
| `dbt_dimensions` (5 parallel) | < 90 s | 5 min |
| `dbt_fact` | < 2 min | 10 min |
| `dbt_consumption` | < 2 min | 10 min |
| `dbt_test` | < 3 min | 15 min |
| `notify_success` | < 5 s | 30 s |

Total expected runtime: 10–15 minutes.

---

## Source Data Loading

### Load new CSV data:

```bash
python ingestion/load_sales.py --file /path/to/sales_data.csv
```

**For full reload (replaces all data):**
```bash
python ingestion/load_sales.py --file /path/to/sales_data.csv --truncate
```

**Validate before running dbt:**
```bash
python ingestion/validate_source.py
```

Expected output (all PASS):
```
PASS  [Row count > 0]                               value: 100000
PASS  [NULL ORDER_ID rate < 1%]                     value: 0.00
PASS  [NULL ORDER_DATE rate < 1%]                   value: 0.00
PASS  [No future ORDER_DATE]                        value: 0
PASS  [SHIP_DATE >= ORDER_DATE (no negative lead time)]  value: 0
PASS  [UNITS_SOLD all positive]                     value: 0
All source validation checks passed.
```

---

## Failure Modes

### `validate_source` fails — Row count = 0

**Cause:** `raw.sales` table is empty. Data was not loaded before the pipeline ran.

**Recovery:**
1. Load the data: `python ingestion/load_sales.py --file data/sample/sales_sample.csv`
2. Re-trigger the Airflow DAG from the failed task (not from the beginning)

---

### `dbt_staging` fails — `unique` or `not_null` test

**Symptom:** dbt test failure on `stg_sales.order_id`.

**Diagnosis:**
```bash
# Check for duplicate ORDER_IDs in raw.sales
docker exec -it postgres psql -U platform_user -d sales_platform -c \
  'SELECT "ORDER_ID", COUNT(*) FROM raw.sales GROUP BY "ORDER_ID" HAVING COUNT(*) > 1 LIMIT 20;'
```

**Common cause:** Source CSV contains duplicate ORDER_IDs (legitimate re-sends from ERP).

**Resolution:** The `stg_sales` model uses `ROW_NUMBER() OVER (PARTITION BY order_id)` to
deduplicate — verify this logic ran. If not, run `dbt run --select stg_sales --full-refresh`.

---

### `dbt_fact` fails — FK violation on dimension tables

**Symptom:** dbt test `relationships` test fails between `fact_sales` and a dimension table.

**Diagnosis:**
```bash
# Check for orphaned dimension keys
docker exec -it postgres psql -U platform_user -d sales_platform -c \
  'SELECT f."GEOGRAPHY_ID" FROM marts.fact_sales f LEFT JOIN marts.dim_geography g ON f."GEOGRAPHY_ID" = g."GEOGRAPHY_ID" WHERE g."GEOGRAPHY_ID" IS NULL LIMIT 10;'
```

**Common cause:** New region/country in the source data not yet in `dim_geography`.

**Resolution:** Run `dbt run --select dim_geography --full-refresh` to rebuild the dimension,
then re-run `dbt run --select fact_sales`.

---

### `ON CONFLICT DO NOTHING` — investigating silently skipped rows

The `INSERT ... ON CONFLICT DO NOTHING` in `load_sales.py` will silently skip rows if
`ORDER_ID` already exists in `raw.sales`. To audit skipped rows:

```sql
-- Count rows in source CSV vs raw.sales
-- If counts differ, rows were skipped
SELECT COUNT(*) FROM raw.sales WHERE _ingested_at >= NOW() - INTERVAL '1 hour';
```

To force-update existing rows: use `--truncate` flag with `load_sales.py`.

---

### Power BI shows stale data

**Symptom:** Power BI dashboard not reflecting today's data.

**Diagnosis steps:**
1. Confirm Airflow DAG ran successfully today (check Airflow UI → DAG Runs)
2. Confirm `sales_performance` model was refreshed:
   ```sql
   SELECT MAX(YEAR), MAX(MONTH) FROM consumption.sales_performance;
   ```
3. In Power BI Desktop: Home → Refresh (Import mode) or verify DirectQuery connection

**Common cause:** DAG failed silently. Check `notify_failure` email task.

---

## Data Quality Reference

| Check | Location | Failure action |
|---|---|---|
| Row count > 0 | `validate_source.py` | Pipeline halts before dbt |
| NULL ORDER_ID < 1% | `validate_source.py` | Pipeline halts |
| No future dates | `validate_source.py` | Pipeline halts |
| SHIP_DATE ≥ ORDER_DATE | `validate_source.py` | Pipeline halts |
| not_null / unique (order_id) | `dbt test` | Task fails, stored in failures schema |
| FK integrity (all dims) | `dbt test` | Task fails, stored in failures schema |
| Financial integrity | `dbt test` (singular) | Task fails |

---

## Database Connection Reference

| Parameter | Default value | Override via |
|---|---|---|
| Host | `localhost` | `DBT_HOST` env var |
| Port | `5432` | `DBT_PORT` env var |
| Database | `sales_platform` | `DBT_DBNAME` env var |
| User | `platform_user` | `DBT_USER` env var |
| Password | *(empty)* | `DBT_PASSWORD` env var |

---

## Escalation

If a dbt model fails and cannot be diagnosed:
1. Open a GitHub issue with label `pipeline-failure`
2. Attach: dbt error message, output of `dbt test --store-failures`, row count from `raw.sales`
3. If affecting Power BI reports, label additionally as `reporting-impact`
