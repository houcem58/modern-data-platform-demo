# ADR-001 — Star Schema vs. Operational Data Store (ODS) Architecture

**Status:** Accepted  
**Date:** 2025-06-01  
**Author:** Houcem Hammami  
**Reviewers:** —  

---

## Context

The data platform must serve two consumer types:

1. **Power BI reports** — analytical queries aggregating millions of rows by region, product,
   channel, and time period. Read-heavy. Latency-tolerant (seconds to minutes acceptable).

2. **Operational monitoring** — row-level access to recent transactions for order management.
   Read-heavy on recent data. Low cardinality queries.

Two primary warehouse patterns were evaluated:

**Option A — Operational Data Store (ODS)**  
A single wide table mirroring the source schema, lightly cleaned. All columns from `raw.sales`
retained. Power BI queries run against the ODS directly.

**Option B — Kimball Star Schema (chosen)**  
Source data normalized into dimension tables (geography, product, channel, date, priority)
and a central fact table (`fact_sales`). A consumption model (`sales_performance`) pre-joins
all dimensions for analytics.

---

## Decision

**Adopted: Option B — Kimball star schema with dbt incremental models.**

---

## Rationale

### Query performance at analytics scale

Power BI uses DirectQuery or Import mode on the consumption layer. Star schema enables:
- Columnar pruning: a "revenue by region" query touches only `REGION`, `TOTAL_REVENUE`
- Aggregation at the `sales_performance` grain eliminates per-query GROUP BY over fact_sales
- Pre-computed window functions (rolling 12M revenue, MoM growth) execute once at load,
  not on every dashboard open

An ODS forces Power BI to aggregate the full raw table on every query, which degrades
substantially beyond 5M rows.

### DAX semantic model alignment

Power BI's DAX engine is optimized for star schema relationships. Dimension tables map
directly to DAX relationships. Measures like `Total Revenue`, `Gross Margin %`, and
`Rolling 12M` are expressible as simple DAX measures against a pre-joined fact table.

An ODS requires complex DAX FILTER + CALCULATE patterns to achieve the same results,
increasing report maintenance complexity.

### Data quality enforcement at the staging layer

The star schema pipeline introduces a mandatory `stg_sales` staging step with dbt tests
(not_null, unique on ORDER_ID). An ODS approach pushes quality enforcement to the report
layer, where failures are invisible to data engineers and visible only as wrong report numbers.

### Incremental strategy

`fact_sales` uses `incremental (merge on ORDER_ID)`, which:
- Handles late-arriving orders correctly
- Idempotent: re-running the dbt job never duplicates rows
- Efficient: only changed/new rows are processed on each run

An ODS with a TRUNCATE-LOAD pattern is simpler but re-processes the full dataset daily,
increasing compute cost and extending the daily load window.

---

## Consequences

**Positive:**
- Power BI query latency sub-second on the `sales_performance` consumption model
- Data quality enforced at the staging layer, not the report layer
- Each dimension is independently manageable (new geography added without touching fact)
- dbt tests catch FK violations before they reach Power BI

**Negative:**
- Higher initial modeling investment than ODS
- Adding a new metric requires a dbt model change, not just a Power BI measure
- The `sales_performance` delete+insert strategy has a brief window where data is unavailable

**Mitigation:**
- The Airflow DAG runs at 06:00 UTC when report usage is minimal
- `dbt test --store-failures` captures failures to a separate schema for triage

---

## Alternatives Rejected

| Alternative | Rejection reason |
|---|---|
| ODS (Option A) | Poor Power BI performance at scale; no quality enforcement layer |
| Data Vault 2.0 | Higher modeling complexity; better suited for multi-source enterprise DW |
| Delta Lake / Lakehouse | Requires Spark infrastructure; over-engineered for single-source sales platform |
| Snowflake schema | Additional join complexity for no meaningful normalization benefit at this data volume |

---

## Review Trigger

- If source data expands to > 5 sources (Data Vault 2.0 or Lakehouse pattern becomes appropriate)
- If near-real-time analytics (< 5 min latency) is required (streaming aggregation needed)
- If the dbt model count exceeds 20 (schema registry and contract testing justified)
