{{
  config(
    materialized     = 'incremental',
    unique_key       = 'ORDER_ID',
    on_schema_change = 'merge'
  )
}}

WITH source AS (
    SELECT
        s.order_id,
        s.units_sold,
        s.unit_price,
        s.unit_cost,
        s.order_date,
        s.ship_date,
        s.item_type,
        s.country,
        s.region,
        s.sales_channel,
        s.order_priority,
        TO_CHAR(s.order_date, 'YYYYMMDD')::INTEGER  AS order_date_key,
        TO_CHAR(s.ship_date,  'YYYYMMDD')::INTEGER  AS ship_date_key
    FROM {{ ref('stg_sales') }} s
    {% if is_incremental() %}
        WHERE GREATEST(s.order_date, s.ship_date) >= CURRENT_DATE - INTERVAL '30 days'
    {% endif %}
)

SELECT
    s.order_id                                                     AS ORDER_ID,
    s.units_sold                                                   AS UNITS_SOLD,
    s.unit_price                                                   AS UNIT_PRICE,
    s.unit_cost                                                    AS UNIT_COST,
    ROUND(s.units_sold * s.unit_price, 2)                         AS TOTAL_REVENUE,
    ROUND(s.units_sold * s.unit_cost,  2)                         AS TOTAL_COST,
    ROUND((s.units_sold * s.unit_price) - (s.units_sold * s.unit_cost), 2) AS TOTAL_PROFIT,

    dp.PRODUCT_ID,
    dg.GEOGRAPHY_ID,
    dc.CHANNEL_ID,
    dpr.PRIORITY_ID,
    dd_order.DATE_KEY   AS ORDER_DATE_KEY,
    dd_ship.DATE_KEY    AS SHIP_DATE_KEY,

    -- shipping lead time in days
    (s.ship_date - s.order_date)::INTEGER                         AS SHIPPING_DAYS

FROM source s

LEFT JOIN {{ ref('dim_product') }}   dp  ON s.item_type      = dp.PRODUCT_CATEGORY
LEFT JOIN {{ ref('dim_geography') }} dg  ON s.country        = dg.COUNTRY
                                        AND s.region         = dg.REGION
LEFT JOIN {{ ref('dim_channel') }}   dc  ON s.sales_channel  = dc.SALES_CHANNEL
LEFT JOIN {{ ref('dim_priority') }}  dpr ON s.order_priority = dpr.ORDER_PRIORITY
LEFT JOIN {{ ref('dim_date') }}      dd_order ON s.order_date_key = dd_order.DATE_KEY
LEFT JOIN {{ ref('dim_date') }}      dd_ship  ON s.ship_date_key  = dd_ship.DATE_KEY

WHERE dp.PRODUCT_ID    IS NOT NULL
  AND dg.GEOGRAPHY_ID  IS NOT NULL
  AND dc.CHANNEL_ID    IS NOT NULL
  AND dpr.PRIORITY_ID  IS NOT NULL
  AND dd_order.DATE_KEY IS NOT NULL
  AND dd_ship.DATE_KEY  IS NOT NULL
