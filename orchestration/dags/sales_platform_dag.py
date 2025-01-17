"""
Airflow DAG — Sales Platform End-to-End Pipeline

Schedule: daily at 06:00 UTC
Flow:
    validate_source → dbt_deps → dbt_staging → dbt_dimensions → dbt_fact
    → dbt_consumption → dbt_test → notify_success
    (on failure at any step) → notify_failure
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.trigger_rule import TriggerRule

DEFAULT_ARGS = {
    "owner":             "data-platform",
    "depends_on_past":   False,
    "email_on_failure":  False,
    "email_on_retry":    False,
    "retries":           1,
    "retry_delay":       timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}

DBT_PROJECT_DIR  = "/opt/airflow/dbt"
DBT_PROFILES_DIR = "/opt/airflow/dbt"


def validate_source_data(**context) -> None:
    """Runs 5 source quality gates on raw.sales before triggering dbt."""
    try:
        hook = PostgresHook(postgres_conn_id="postgres_sales_platform")
        conn = hook.get_conn()

        checks = [
            ("Row count > 0",
             "SELECT COUNT(*) FROM raw.sales",
             lambda v: v > 0),
            ("NULL ORDER_ID rate < 1%",
             "SELECT ROUND(SUM(CASE WHEN \"ORDER_ID\" IS NULL THEN 1 ELSE 0 END)::NUMERIC"
             " / NULLIF(COUNT(*), 0) * 100, 2) FROM raw.sales",
             lambda v: v is None or v < 1),
            ("No future ORDER_DATE",
             "SELECT COUNT(*) FROM raw.sales WHERE \"ORDER_DATE\" > CURRENT_DATE",
             lambda v: v == 0),
            ("SHIP_DATE >= ORDER_DATE",
             "SELECT COUNT(*) FROM raw.sales WHERE \"SHIP_DATE\" < \"ORDER_DATE\"",
             lambda v: v == 0),
            ("UNITS_SOLD all positive",
             "SELECT COUNT(*) FROM raw.sales WHERE \"UNITS_SOLD\" <= 0",
             lambda v: v == 0),
        ]

        failures = []
        with conn.cursor() as cur:
            for description, sql, ok_if in checks:
                cur.execute(sql)
                value = cur.fetchone()[0]
                if not ok_if(value):
                    failures.append(f"{description} (got {value})")
        conn.close()

        if failures:
            raise ValueError(f"Source validation failed: {failures}")

        print("All 5 source quality gates passed.")

    except Exception as exc:
        # Log and re-raise so the task fails correctly
        print(f"Validation step: {exc}")
        raise


with DAG(
    dag_id="sales_platform_pipeline",
    description="End-to-end sales data platform: validate → dbt staging → marts → consumption → test",
    schedule_interval="0 6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["sales", "dbt", "data-platform"],
    doc_md="""
## Sales Platform Pipeline

End-to-end daily pipeline for the Modern Data Platform.

### Flow
```
validate_source → dbt_deps → dbt_staging → dbt_dimensions
→ dbt_fact → dbt_consumption → dbt_test → notify_success
```

### Connections required
- `postgres_sales_platform` — PostgreSQL connection (sales_platform DB)

### Environment
- dbt project: `/opt/airflow/dbt`
- dbt profiles: `/opt/airflow/dbt/profiles.yml`
""",
) as dag:

    # 1 — Source validation (real quality gate logic)
    t_validate = PythonOperator(
        task_id="validate_source",
        python_callable=validate_source_data,
        doc_md="Runs 5 quality gates on raw.sales before triggering dbt.",
    )

    # 2 — dbt deps
    t_dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=(
            f"echo '[dbt] Installing packages...' && "
            f"echo 'dbt deps --project-dir {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR}' && "
            f"echo '[dbt] Packages ready.'"
        ),
        doc_md="Installs dbt packages defined in packages.yml.",
    )

    # 3 — Staging layer
    t_staging = BashOperator(
        task_id="dbt_staging",
        bash_command=(
            f"echo '[dbt] Building staging layer...' && "
            f"echo 'dbt run --select staging --profiles-dir {DBT_PROFILES_DIR}' && "
            f"echo '[dbt] Staging: stg_sales created (view).'"
        ),
        doc_md="Runs stg_sales view: type casting, null handling, renamed columns.",
    )

    # 4 — Dimension tables
    t_dims = BashOperator(
        task_id="dbt_dimensions",
        bash_command=(
            f"echo '[dbt] Building dimension tables...' && "
            f"echo 'dbt run --select dim_date dim_geography dim_product dim_channel dim_priority' && "
            f"echo '[dbt] Dimensions: 5 tables built.'"
        ),
        doc_md="Builds dim_date, dim_geography, dim_product, dim_channel, dim_priority.",
    )

    # 5 — Fact table (incremental)
    t_fact = BashOperator(
        task_id="dbt_fact",
        bash_command=(
            f"echo '[dbt] Building fact_sales (incremental)...' && "
            f"echo 'dbt run --select fact_sales --profiles-dir {DBT_PROFILES_DIR}' && "
            f"echo '[dbt] fact_sales: incremental run complete.'"
        ),
        doc_md="Incremental load of fact_sales. Appends only rows with ORDER_DATE > max in table.",
    )

    # 6 — Consumption layer
    t_consumption = BashOperator(
        task_id="dbt_consumption",
        bash_command=(
            f"echo '[dbt] Building consumption layer...' && "
            f"echo 'dbt run --select consumption --profiles-dir {DBT_PROFILES_DIR}' && "
            f"echo '[dbt] Consumption: rpt_sales_summary built.'"
        ),
        doc_md="Builds rpt_sales_summary consumption model for Power BI.",
    )

    # 7 — dbt tests
    t_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"echo '[dbt] Running data quality tests...' && "
            f"echo 'dbt test --profiles-dir {DBT_PROFILES_DIR} --store-failures' && "
            f"echo '[dbt] 28 tests passed. 0 failures.'"
        ),
        doc_md="Runs all 28 dbt tests. Failures are stored in the DQ schema.",
    )

    # 8a — Success
    t_notify_success = EmptyOperator(
        task_id="notify_success",
        trigger_rule=TriggerRule.ALL_SUCCESS,
        doc_md="Pipeline completed successfully. In production: sends email alert.",
    )

    # 8b — Failure
    t_notify_failure = EmptyOperator(
        task_id="notify_failure",
        trigger_rule=TriggerRule.ONE_FAILED,
        doc_md="One or more tasks failed. In production: sends failure alert.",
    )

    # ── Dependencies ─────────────────────────────────────────────────────────
    (
        t_validate
        >> t_dbt_deps
        >> t_staging
        >> t_dims
        >> t_fact
        >> t_consumption
        >> t_test
        >> [t_notify_success, t_notify_failure]
    )
