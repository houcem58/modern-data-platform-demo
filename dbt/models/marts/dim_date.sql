{{
  config(
    materialized  = 'incremental',
    unique_key    = 'DATE_KEY',
    on_schema_change = 'sync'
  )
}}

WITH date_spine AS (
    SELECT order_date AS date_col FROM {{ ref('stg_sales') }} WHERE order_date IS NOT NULL
    UNION
    SELECT ship_date  AS date_col FROM {{ ref('stg_sales') }} WHERE ship_date  IS NOT NULL
),

distinct_dates AS (
    SELECT DISTINCT date_col FROM date_spine
    {% if is_incremental() %}
        WHERE date_col > (SELECT COALESCE(MAX(FULL_DATE), '1900-01-01'::DATE) FROM {{ this }})
    {% endif %}
)

SELECT
    TO_CHAR(date_col, 'YYYYMMDD')::INTEGER              AS DATE_KEY,
    date_col                                             AS FULL_DATE,
    EXTRACT(DAY   FROM date_col)::INTEGER                AS DAY,
    EXTRACT(MONTH FROM date_col)::INTEGER                AS MONTH,
    TO_CHAR(date_col, 'Month')                           AS MONTH_NAME,
    EXTRACT(QUARTER FROM date_col)::INTEGER              AS QUARTER,
    EXTRACT(YEAR  FROM date_col)::INTEGER                AS YEAR,
    EXTRACT(WEEK  FROM date_col)::INTEGER                AS WEEK_OF_YEAR,
    EXTRACT(DOW   FROM date_col)::INTEGER                AS DAY_OF_WEEK,
    TO_CHAR(date_col, 'Day')                             AS DAY_NAME,
    CASE WHEN EXTRACT(DOW FROM date_col) IN (0, 6)
         THEN TRUE ELSE FALSE END                        AS IS_WEEKEND,
    EXTRACT(YEAR FROM date_col)::TEXT || '-Q'
        || EXTRACT(QUARTER FROM date_col)::TEXT          AS YEAR_QUARTER,
    EXTRACT(YEAR FROM date_col)::TEXT || '-'
        || LPAD(EXTRACT(MONTH FROM date_col)::TEXT, 2, '0') AS YEAR_MONTH
FROM distinct_dates
