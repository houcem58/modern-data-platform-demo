# Semantic Model — Sales Platform

## Source Table

`consumption.sales_performance` — pre-aggregated monthly grain, joining all five dimensions.

## Column Reference

| Column | Type | Description |
|---|---|---|
| YEAR | INTEGER | Calendar year |
| MONTH | INTEGER | Calendar month (1–12) |
| YEAR_MONTH | TEXT | e.g. `2024-03` |
| YEAR_QUARTER | TEXT | e.g. `2024-Q1` |
| REGION | TEXT | Geographic region |
| COUNTRY | TEXT | Country name |
| PRODUCT_CATEGORY | TEXT | Product category (e.g. Cosmetics, Electronics) |
| SALES_CHANNEL | TEXT | Offline / Online |
| ORDER_PRIORITY | TEXT | C / H / M / L |
| PRIORITY_LABEL | TEXT | Critical / High / Medium / Low |
| ORDER_COUNT | BIGINT | Number of orders in period |
| TOTAL_UNITS_SOLD | BIGINT | Sum of units sold |
| TOTAL_REVENUE | NUMERIC | Gross revenue |
| TOTAL_COST | NUMERIC | Total cost |
| TOTAL_PROFIT | NUMERIC | Revenue minus cost |
| AVG_UNIT_PRICE | NUMERIC | Average unit price |
| AVG_SHIPPING_DAYS | NUMERIC | Average fulfillment days |
| ROLLING_12M_REVENUE | NUMERIC | 12-month rolling revenue (window function) |
| ROLLING_3M_PROFIT | NUMERIC | 3-month rolling profit |
| MOM_REVENUE_GROWTH_PCT | NUMERIC | Month-over-month revenue growth % |
| MONTHLY_REVENUE_RANK | INTEGER | Revenue rank within month across all segments |
| MONTHLY_PROFIT_RANK | INTEGER | Profit rank within month |

## Relationships

All dimensions are embedded in the consumption grain — no additional joins needed in Power BI. The model is **flat/denormalized** for optimal query performance.

## Date Table

Power BI auto-generates a date table from `YEAR_MONTH`. For advanced time intelligence, create a dedicated Date table in Power BI:

```dax
DateTable = CALENDAR(DATE(2020,1,1), DATE(2026,12,31))
```

Mark it as a date table and relate to `sales_performance[YEAR_MONTH]` via a calculated column:

```dax
YearMonth = FORMAT([Date], "YYYY-MM")
```

## Suggested Hierarchies

- **Geography:** REGION → COUNTRY
- **Time:** YEAR → YEAR_QUARTER → YEAR_MONTH → MONTH
- **Product:** PRODUCT_CATEGORY (flat — no sub-categories in source)
