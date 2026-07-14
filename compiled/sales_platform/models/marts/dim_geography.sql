

WITH source AS (
    SELECT DISTINCT
        region,
        country
    FROM "sales_platform"."staging"."stg_sales"
    WHERE region  IS NOT NULL AND region  <> ''
      AND country IS NOT NULL AND country <> ''
)

SELECT
    ROW_NUMBER() OVER (ORDER BY region, country)  AS GEOGRAPHY_ID,
    region                                         AS REGION,
    country                                        AS COUNTRY
FROM source