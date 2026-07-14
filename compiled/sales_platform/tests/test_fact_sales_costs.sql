-- Asserts that derived financial metrics are internally consistent.
-- Any row returned = test failure.
SELECT
    ORDER_ID,
    UNITS_SOLD,
    UNIT_PRICE,
    UNIT_COST,
    TOTAL_REVENUE,
    TOTAL_COST,
    TOTAL_PROFIT
FROM "sales_platform"."marts"."fact_sales"
WHERE NOT (
    ROUND(TOTAL_REVENUE, 2) = ROUND(UNITS_SOLD * UNIT_PRICE, 2)
    AND ROUND(TOTAL_COST, 2)    = ROUND(UNITS_SOLD * UNIT_COST,  2)
    AND ROUND(TOTAL_PROFIT, 2)  = ROUND(TOTAL_REVENUE - TOTAL_COST, 2)
)