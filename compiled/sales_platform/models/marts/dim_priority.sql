

WITH source AS (
    SELECT DISTINCT
        order_priority
    FROM "sales_platform"."staging"."stg_sales"
    WHERE order_priority IS NOT NULL AND order_priority <> ''
)

SELECT
    ROW_NUMBER() OVER (ORDER BY order_priority) AS PRIORITY_ID,
    order_priority                               AS ORDER_PRIORITY,
    CASE order_priority
        WHEN 'C' THEN 'Critical'
        WHEN 'H' THEN 'High'
        WHEN 'M' THEN 'Medium'
        WHEN 'L' THEN 'Low'
        ELSE order_priority
    END                                          AS PRIORITY_LABEL,
    CASE order_priority
        WHEN 'C' THEN 1
        WHEN 'H' THEN 2
        WHEN 'M' THEN 3
        WHEN 'L' THEN 4
        ELSE 99
    END                                          AS PRIORITY_SORT_ORDER
FROM source