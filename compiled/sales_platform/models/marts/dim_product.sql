

WITH source AS (
    SELECT DISTINCT
        item_type
    FROM "sales_platform"."staging"."stg_sales"
    WHERE item_type IS NOT NULL AND item_type <> ''
)

SELECT
    ROW_NUMBER() OVER (ORDER BY item_type) AS PRODUCT_ID,
    item_type                               AS PRODUCT_CATEGORY
FROM source