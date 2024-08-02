# DAX Measures — Sales Platform

All measures are defined on `sales_performance` (the consumption table).

---

## Core Revenue & Profit

```dax
Total Revenue =
SUM(sales_performance[TOTAL_REVENUE])

Total Cost =
SUM(sales_performance[TOTAL_COST])

Total Profit =
SUM(sales_performance[TOTAL_PROFIT])

Gross Margin % =
DIVIDE([Total Profit], [Total Revenue], 0)

Total Orders =
SUM(sales_performance[ORDER_COUNT])

Total Units Sold =
SUM(sales_performance[TOTAL_UNITS_SOLD])
```

---

## Time Intelligence

```dax
-- Year-over-Year Revenue Growth
YoY Revenue Growth % =
VAR CurrentYear = [Total Revenue]
VAR PriorYear =
    CALCULATE(
        [Total Revenue],
        SAMEPERIODLASTYEAR('DateTable'[Date])
    )
RETURN DIVIDE(CurrentYear - PriorYear, PriorYear, BLANK())

-- Month-over-Month Revenue Growth
MoM Revenue Growth % =
AVERAGE(sales_performance[MOM_REVENUE_GROWTH_PCT])

-- Rolling 12-Month Revenue
Rolling 12M Revenue =
AVERAGE(sales_performance[ROLLING_12M_REVENUE])

-- Rolling 3-Month Profit
Rolling 3M Profit =
AVERAGE(sales_performance[ROLLING_3M_PROFIT])

-- Year-to-Date Revenue
YTD Revenue =
TOTALYTD([Total Revenue], 'DateTable'[Date])

-- Quarter-to-Date Revenue
QTD Revenue =
TOTALQTD([Total Revenue], 'DateTable'[Date])
```

---

## Rankings & Benchmarks

```dax
-- Average Revenue per Order
Avg Revenue per Order =
DIVIDE([Total Revenue], [Total Orders], 0)

-- Average Shipping Days
Avg Shipping Days =
AVERAGEX(
    sales_performance,
    sales_performance[AVG_SHIPPING_DAYS]
)

-- Top N Products by Revenue (used as filter)
Top 5 Products =
RANKX(
    ALL(sales_performance[PRODUCT_CATEGORY]),
    [Total Revenue],
    ,
    DESC,
    DENSE
) <= 5

-- Online vs Offline Revenue Split %
Online Revenue % =
DIVIDE(
    CALCULATE([Total Revenue], sales_performance[SALES_CHANNEL] = "Online"),
    [Total Revenue],
    0
)
```

---

## KPI Formatting

```dax
-- Margin % formatted
Gross Margin % Display =
FORMAT([Gross Margin %], "0.0%")

-- Revenue formatted (millions)
Revenue (M) =
FORMAT([Total Revenue] / 1000000, "#,##0.0") & "M"

-- MoM badge color (for conditional formatting)
MoM Color =
IF([MoM Revenue Growth %] >= 0, "#2E7D32", "#C62828")
```

---

## Segment Comparisons

```dax
-- Region revenue as % of total
Region Revenue % =
DIVIDE(
    [Total Revenue],
    CALCULATE([Total Revenue], ALL(sales_performance[REGION])),
    0
)

-- Priority revenue split
Critical Priority Revenue % =
DIVIDE(
    CALCULATE([Total Revenue], sales_performance[ORDER_PRIORITY] = "C"),
    [Total Revenue],
    0
)
```
