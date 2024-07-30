"""
Airflow DAG — Sales Platform End-to-End Pipeline

Schedule: daily at 06:00 UTC
Flow:
    validate_source → dbt_staging → dbt_marts → dbt_consumption → dbt_test → notify_success
    (on failure at any step) → notify_failure

Requires:
    - Apache Airflow 2.6+
    - apache-airflow-providers-postgres
    - apache-airflow-providers-dbt-cloud (or dbt CLI via BashOperator)
    - Connections: postgres_sales_platform, dbt_cli
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.email import EmailOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.trigger_rule import TriggerRule

# ── Default args ────────────────────────────────────────────────────────────
DEFAULT_ARGS = {
    "owner":            "data-platform",
    "depends_on_past":  False,
    "email_on_failure": True,
    "email_on_retry":   False,
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}

DBT_PROJECT_DIR = "/opt/airflow/dbt"
DBT_PROFILES_DIR = "/opt/airflow/dbt"

# ── Validation task ──────────────────────────────────────────────────────────
def validate_source_data(**context) -> None:
    """Runs source quality gates against raw.sales before triggering dbt."""
    hook = PostgresHook(postgres_conn_id="postgres_sales_platform")
    conn = hook.get_conn()

    checks = [
        ("Row count > 0",
         "SELECT COUNT(*) FROM raw.sales",
         lambda v: v > 0),
        ("NULL ORDER_ID rate < 1%",
         'SELECT ROUND(SUM(CASE WHEN "ORDER_ID" IS NULL THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) FROM raw.sales',
         lambda v: v is None or v < 1),
        ("No future ORDER_DATE",
         'SELECT COUNT(*) FROM raw.sales WHERE "ORDER_DATE" > CURRENT_DATE',
         lambda v: v == 0),
        ("SHIP_DATE >= ORDER_DATE",
         'SELECT COUNT(*) FROM raw.sales WHERE "SHIP_DATE" < "ORDER_DATE"',
         lambda v: v == 0),
        ("UNITS_SOLD all positive",
         'SELECT COUNT(*) FROM raw.sales WHERE "UNITS_SOLD" <= 0',
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


# ── DAG definition ───────────────────────────────────────────────────────────
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
validate_source → dbt_staging → dbt_marts → dbt_consumption → dbt_test → notify_success
```

### Connections required
- `postgres_sales_platform` — PostgreSQL connection (sales_platform DB)

### Environment
- DBT_PROJECT_DIR: `/opt/airflow/dbt`
- dbt profiles: `/opt/airflow/dbt/profiles.yml`
""",
) as dag:

    # 1. Source validation
    t_validate = PythonOperator(
        task_id="validate_source",
        python_callable=validate_source_data,
        doc_md="Runs 5 quality gates on raw.sales before triggering dbt.",
    )

    # 2. dbt deps (install packages)
    t_dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt deps --profiles-dir {DBT_PROFILES_DIR}"
        ),
    )

    # 3. Staging layer
    t_staging = BashOperator(
        task_id="dbt_staging",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt run --select staging --profiles-dir {DBT_PROFILES_DIR} "
            f"--vars '{{\"execution_date\": \"{{{{ ds }}}}\"}}'  "
        ),
    )

    # 4. Dimension tables
    t_dims = BashOperator(
        task_id="dbt_dimensions",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt run --select dim_date dim_geography dim_product dim_channel dim_priority "
            f"--profiles-dir {DBT_PROFILES_DIR}"
        ),
    )

    # 5. Fact table (incremental)
    t_fact = BashOperator(
        task_id="dbt_fact",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt run --select fact_sales --profiles-dir {DBT_PROFILES_DIR}"
        ),
    )

    # 6. Consumption layer (incremental)
    t_consumption = BashOperator(
        task_id="dbt_consumption",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt run --select consumption --profiles-dir {DBT_PROFILES_DIR}"
        ),
    )

    # 7. dbt tests
    t_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt test --profiles-dir {DBT_PROFILES_DIR} "
            f"--store-failures"
        ),
    )

    # 8a. Success notification
    t_notify_success = EmailOperator(
        task_id="notify_success",
        to=["houcem0508@gmail.com"],
        subject="[Sales Platform] ✅ Pipeline succeeded — {{ ds }}",
        html_content="""
<h3>Sales Platform Pipeline — SUCCESS</h3>
<p>Execution date: <b>{{ ds }}</b></p>
<p>All dbt models completed and tests passed.</p>
""",
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )

    # 8b. Failure notification
    t_notify_failure = EmailOperator(
        task_id="notify_failure",
        to=["houcem0508@gmail.com"],
        subject="[Sales Platform] ❌ Pipeline FAILED — {{ ds }}",
        html_content="""
<h3>Sales Platform Pipeline — FAILURE</h3>
<p>Execution date: <b>{{ ds }}</b></p>
<p>Check the Airflow logs for details.</p>
""",
        trigger_rule=TriggerRule.ONE_FAILED,
    )

    # ── Dependencies ─────────────────────────────────────────────────────────
    t_validate >> t_dbt_deps >> t_staging >> t_dims >> t_fact >> t_consumption >> t_test
    t_test >> [t_notify_success, t_notify_failure]
