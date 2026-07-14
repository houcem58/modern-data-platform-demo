

WITH source AS (
    SELECT DISTINCT
        sales_channel
    FROM "sales_platform"."staging"."stg_sales"
    WHERE sales_channel IS NOT NULL AND sales_channel <> ''
)

SELECT
    ROW_NUMBER() OVER (ORDER BY sales_channel) AS CHANNEL_ID,
    sales_channel                               AS SALES_CHANNEL
FROM source