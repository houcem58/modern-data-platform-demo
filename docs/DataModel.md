# Data Model — Sales Platform Star Schema

## Star Schema Overview

```
                    ┌──────────────┐
                    │   dim_date   │
                    │  DATE_KEY PK │
                    └──────┬───────┘
                           │ ORDER_DATE_KEY / SHIP_DATE_KEY
         ┌─────────────────┼──────────────────────┐
         │                 │                      │
┌────────┴──────┐   ┌──────▼──────────┐   ┌──────┴──────────┐
│ dim_geography │   │   fact_sales    │   │   dim_product   │
│GEOGRAPHY_ID PK│◄──│  ORDER_ID PK    │──►│  PRODUCT_ID PK  │
│REGION         │   │  GEOGRAPHY_ID FK│   │PRODUCT_CATEGORY │
│COUNTRY        │   │  PRODUCT_ID FK  │   └─────────────────┘
└───────────────┘   │  CHANNEL_ID FK  │
                    │  PRIORITY_ID FK │   ┌─────────────────┐
┌───────────────┐   │  UNITS_SOLD     │   │  dim_channel    │
│ dim_priority  │   │  UNIT_PRICE     │◄──│  CHANNEL_ID PK  │
│ PRIORITY_ID PK│◄──│  UNIT_COST      │   │  SALES_CHANNEL  │
│ORDER_PRIORITY │   │  TOTAL_REVENUE  │   └─────────────────┘
│PRIORITY_LABEL │   │  TOTAL_COST     │
│PRIORITY_SORT  │   │  TOTAL_PROFIT   │
└───────────────┘   │  SHIPPING_DAYS  │
                    └─────────────────┘
```

## Table Definitions

### dim_date

| Column | Type | Description |
|---|---|---|
| DATE_KEY | INTEGER PK | YYYYMMDD integer key |
| FULL_DATE | DATE | Full date value |
| DAY | INTEGER | Day of month (1–31) |
| MONTH | INTEGER | Month (1–12) |
| MONTH_NAME | TEXT | January … December |
| QUARTER | INTEGER | Quarter (1–4) |
| YEAR | INTEGER | Calendar year |
| WEEK | INTEGER | ISO week number |
| DAY_OF_WEEK | INTEGER | 0=Sunday … 6=Saturday |
| DAY_NAME | TEXT | Monday … Sunday |
| IS_WEEKEND | BOOLEAN | True for Sat/Sun |
| YEAR_QUARTER | TEXT | e.g. `2024-Q1` |
| YEAR_MONTH | TEXT | e.g. `2024-03` |

### dim_geography

| Column | Type | Description |
|---|---|---|
| GEOGRAPHY_ID | INTEGER PK | Surrogate key |
| REGION | TEXT | Geographic region |
| COUNTRY | TEXT | Country name |

### dim_product

| Column | Type | Description |
|---|---|---|
| PRODUCT_ID | INTEGER PK | Surrogate key |
| PRODUCT_CATEGORY | TEXT | Product category |

### dim_channel

| Column | Type | Description |
|---|---|---|
| CHANNEL_ID | INTEGER PK | Surrogate key |
| SALES_CHANNEL | TEXT | Online / Offline |

### dim_priority

| Column | Type | Description |
|---|---|---|
| PRIORITY_ID | INTEGER PK | Surrogate key |
| ORDER_PRIORITY | TEXT | C / H / M / L |
| PRIORITY_LABEL | TEXT | Critical / High / Medium / Low |
| PRIORITY_SORT_ORDER | INTEGER | 1=Critical … 4=Low |

### fact_sales

| Column | Type | Description |
|---|---|---|
| ORDER_ID | BIGINT PK | Natural key from source |
| PRODUCT_ID | INTEGER FK | → dim_product |
| GEOGRAPHY_ID | INTEGER FK | → dim_geography |
| CHANNEL_ID | INTEGER FK | → dim_channel |
| PRIORITY_ID | INTEGER FK | → dim_priority |
| ORDER_DATE_KEY | INTEGER FK | → dim_date |
| SHIP_DATE_KEY | INTEGER FK | → dim_date |
| UNITS_SOLD | INTEGER | Units sold per order |
| UNIT_PRICE | NUMERIC(12,2) | Price per unit |
| UNIT_COST | NUMERIC(12,2) | Cost per unit |
| TOTAL_REVENUE | NUMERIC(14,2) | UNITS_SOLD × UNIT_PRICE |
| TOTAL_COST | NUMERIC(14,2) | UNITS_SOLD × UNIT_COST |
| TOTAL_PROFIT | NUMERIC(14,2) | TOTAL_REVENUE − TOTAL_COST |
| SHIPPING_DAYS | INTEGER | SHIP_DATE − ORDER_DATE |

### consumption.sales_performance

Monthly aggregation over all dimensions. See [Architecture.md](Architecture.md) and [analytics/semantic_model.md](../analytics/semantic_model.md) for full column list.

## Grain

| Layer | Grain |
|---|---|
| raw.sales | One row per order (append) |
| staging.stg_sales | One row per order (deduped) |
| marts.fact_sales | One row per order |
| consumption.sales_performance | One row per (year, month, region, country, product, channel, priority) |
