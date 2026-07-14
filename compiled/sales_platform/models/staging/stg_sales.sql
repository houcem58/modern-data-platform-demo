

WITH base AS (
    SELECT
        COALESCE(TRIM("REGION"), '')                    AS region,
        COALESCE(TRIM("COUNTRY"), '')                   AS country,
        COALESCE(TRIM("ITEM_TYPE"), '')                 AS item_type,
        COALESCE(TRIM("SALES_CHANNEL"), '')             AS sales_channel,
        COALESCE(TRIM("ORDER_PRIORITY"), '')            AS order_priority,
        COALESCE("ORDER_DATE"::DATE, '1900-01-01'::DATE) AS order_date,
        COALESCE("ORDER_ID"::BIGINT, 0)                 AS order_id,
        COALESCE("SHIP_DATE"::DATE, '1900-01-01'::DATE)  AS ship_date,
        COALESCE("UNITS_SOLD"::INTEGER, 0)              AS units_sold,
        COALESCE("UNIT_PRICE"::NUMERIC(12,2), 0)        AS unit_price,
        COALESCE("UNIT_COST"::NUMERIC(12,2), 0)         AS unit_cost,
        COALESCE("TOTAL_REVENUE"::NUMERIC(14,2), 0)     AS total_revenue,
        COALESCE("TOTAL_COST"::NUMERIC(14,2), 0)        AS total_cost,
        COALESCE("TOTAL_PROFIT"::NUMERIC(14,2), 0)      AS total_profit
    FROM "sales_platform"."raw"."sales"
),

deduped AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY order_id
               ORDER BY order_date DESC
           ) AS row_num
    FROM base
)

SELECT
    region,
    country,
    item_type,
    sales_channel,
    order_priority,
    order_date,
    order_id,
    ship_date,
    units_sold,
    unit_price,
    unit_cost,
    total_revenue,
    total_cost,
    total_profit
FROM deduped
WHERE row_num = 1
  AND order_id > 0
  AND order_date > '1900-01-01'::DATE