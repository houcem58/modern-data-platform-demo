# Power BI — Sales Platform Analytics Layer

## Overview

The analytics layer connects Power BI to the consumption schema in PostgreSQL. The semantic model is built on top of `consumption.sales_performance`, the pre-aggregated mart that joins all five dimensions.

## Prerequisites

- Power BI Desktop (June 2024 or later)
- PostgreSQL ODBC driver: **psqlODBC 16.x** (64-bit)
- `consumption.sales_performance` view populated by dbt

## Connection Setup

1. Open Power BI Desktop → **Get Data** → **PostgreSQL database**
2. Server: `localhost:5432` (or Docker host IP)
3. Database: `sales_platform`
4. Data connectivity mode: **Import** (for small/medium datasets) or **DirectQuery** (for large datasets with real-time needs)
5. Advanced options → SQL: leave blank (select tables/views in navigator)
6. In the navigator, select: `consumption.sales_performance`

## Import vs DirectQuery

| Mode | Best for | Refresh |
|---|---|---|
| Import | < 1 GB, faster visuals | Scheduled (Power BI Service) |
| DirectQuery | Large datasets, real-time | Live query on each interaction |

For this platform (global sales, ~500K rows/year), **Import + daily scheduled refresh** is recommended.

## Semantic Model Structure

See [semantic_model.md](semantic_model.md) for full table/column definitions.

## Key Measures

See [dax_measures.md](dax_measures.md) for all DAX measure definitions.

## Recommended Report Pages

| Page | Key Visuals |
|---|---|
| Executive Overview | KPI cards (Revenue, Profit, Margin%), MoM trend line, Top 5 markets |
| Geographic Performance | Filled map by COUNTRY, bar chart by REGION |
| Product Analysis | Revenue/profit by PRODUCT_CATEGORY, channel mix |
| Time Intelligence | Rolling 12M revenue, YoY growth waterfall, seasonal heatmap |
| Channel & Priority | Channel revenue split, order priority distribution |

## Scheduled Refresh (Power BI Service)

1. Publish report to Power BI Service
2. Configure **On-premises data gateway** (or cloud PostgreSQL endpoint)
3. Dataset settings → **Scheduled refresh** → Daily at 07:00 UTC (1 hour after Airflow DAG)
