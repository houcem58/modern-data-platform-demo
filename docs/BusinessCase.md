# Business Case — Modern Data Platform

## Problem Statement

Analytics teams without a structured transformation layer operate in a fragmented state:
revenue figures vary by dashboard, data quality issues surface in board meetings rather
than at ingestion, and engineers spend 40-60% of their time debugging discrepancies
rather than building new capabilities.

Common failure modes:

- Finance asks for Q3 revenue. Three dashboards return three different numbers. Two analysts
  spend a day tracing which SQL is "correct." None are authoritative.
- An upstream ERP export changes a column format. The ingestion script silently loads nulls.
  The damage surfaces two weeks later in a monthly report.
- A new analyst needs the "shipping days" metric. They write it from scratch. It's the
  fourth version in the company. None of them agree on whether weekends count.
- Pipeline failures send no alerts. The 06:00 refresh failed. No one notices until 14:00.

## Target Environments

**1. Mid-sized Retail / E-Commerce Analytics Teams**
Teams with 2-5 analysts running reports on 100K-10M transaction datasets who need a
single source of truth with auditable transformation logic.

**2. Finance Data Infrastructure**
Finance teams that need revenue and margin figures to reconcile across multiple reporting
surfaces — dashboards, PowerPoint, regulatory filings.

**3. Platform Team Demonstrating dbt Adoption**
Engineering teams evaluating dbt as their transformation standard who need a reference
implementation showing the full pattern: staging → marts → consumption → BI layer.

## What This Platform Provides

| Capability | Implementation |
|---|---|
| Single source of truth | `consumption.sales_performance` — one view, all BI tools |
| Data quality enforcement | 9 gates across source + dbt layers |
| Pipeline observability | Airflow DAG + email alerting on failure/success |
| Metric standardisation | 10 pre-computed DAX measures in semantic model |
| Data lineage | dbt docs with full column-level lineage |
| Incremental updates | Fact table merge strategy — only processes new orders |
| Full-stack reproducibility | `docker compose up` starts entire stack |

## Technology Decisions

### Why dbt?

dbt enforces version-controlled, tested, documented SQL transforms. Every model has tests.
Every column in the consumption layer has documentation. A new analyst can understand the
full data lineage from `dbt docs serve` in 10 minutes — not 10 days of tribal knowledge.

### Why Airflow?

Airflow gives the pipeline observable state. DAG runs are logged, failures alert, and
the dependency graph is explicit. A cron job gives you none of this.

### Why a Star Schema?

Conformed dimensions (dim_date, dim_geography, dim_product, dim_channel, dim_priority)
allow any combination of dimensions to be used in any report without re-writing SQL.
This is the standard BI layer pattern for a reason.

### Why Power BI?

Power BI is the dominant BI tool in enterprise (Microsoft ecosystem). The semantic model
approach — building DAX measures on top of the consumption layer — means the same measure
definition is shared across all reports. One change propagates everywhere.
