# Roadmap

## Current Status — v1.2.0

Production-grade 4-layer dbt pipeline with Airflow orchestration, Power BI semantic layer,
Docker stack, 9 data quality gates, and dbt docs on GitHub Pages.

---

## Near-Term (v1.3.x)

### dbt Exposures

Add a `docs/exposures.yml` to declare which dashboards and reports consume which models.
This closes the lineage graph from source CSV all the way to Power BI report page.

### Row-Level Data Quality Metrics

Add a `dbt_utils.expression_is_true` check per column on `fact_sales` for financial
accuracy (margin % within plausible bounds, shipping days within reasonable range).
Store results via `dbt test --store-failures` for auditability.

### Alerting via Slack

Add a Slack notification operator alongside the existing EmailOperator in the Airflow DAG.
Failure alerts should include: DAG run ID, failed task, error summary, link to logs.

---

## Medium-Term (v2.x)

### Additional Sales Dimensions

Extend the star schema with:
- `dim_customer` (customer segment, acquisition date, lifetime value tier)
- `dim_promotion` (promotion code, discount type, campaign)

These require source schema changes but the incremental merge strategy handles them cleanly.

### dbt Snapshots for SCD Type 2

Add dbt snapshots on `dim_geography` and `dim_product` to track historical attribute changes.
Required for accurate historical reporting when product categories or regions are reorganised.

### Great Expectations Integration

Replace the custom `validate_source.py` gates with Great Expectations for richer profiling,
HTML validation reports, and a data quality checkpoint that integrates with Airflow.

### Looker / Metabase Alternative

Add a Metabase semantic layer configuration as an alternative to Power BI, making the
platform accessible to teams not in the Microsoft ecosystem.

---

## Long-Term (v3.x)

### Cloud-Native Variant

Terraform modules for:
- AWS: RDS PostgreSQL + MWAA (Managed Airflow) + S3 data lake
- GCP: Cloud SQL + Cloud Composer + BigQuery

Same dbt models, same data quality gates — different infrastructure.

### dbt Semantic Layer (MetricFlow)

Migrate DAX measures to dbt Semantic Layer / MetricFlow so metrics are defined once
in dbt and consumed by any BI tool — not just Power BI.

---

## Won't Do

- Real customer data — all data in this repo is synthetic or public domain
- Proprietary BI tool configurations beyond Power BI (Tableau, Qlik) — too vendor-specific
