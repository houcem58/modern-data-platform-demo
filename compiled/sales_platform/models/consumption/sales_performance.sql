

WITH fact_base AS (
    SELECT *
    FROM "sales_platform"."marts"."fact_sales"
    
),

enriched AS (
    SELECT
        f.ORDER_ID,
        f.UNITS_SOLD,
        f.UNIT_PRICE,
        f.UNIT_COST,
        f.TOTAL_REVENUE,
        f.TOTAL_COST,
        f.TOTAL_PROFIT,
        f.SHIPPING_DAYS,

        dp.PRODUCT_CATEGORY,
        dg.REGION,
        dg.COUNTRY,
        dc.SALES_CHANNEL,
        dpr.ORDER_PRIORITY,
        dpr.PRIORITY_LABEL,
        dpr.PRIORITY_SORT_ORDER,

        dd.YEAR,
        dd.MONTH,
        dd.MONTH_NAME,
        dd.QUARTER,
        dd.YEAR_QUARTER,
        dd.YEAR_MONTH,
        dd.IS_WEEKEND
    FROM fact_base f
    JOIN "sales_platform"."marts"."dim_product"   dp  ON f.PRODUCT_ID   = dp.PRODUCT_ID
    JOIN "sales_platform"."marts"."dim_geography" dg  ON f.GEOGRAPHY_ID = dg.GEOGRAPHY_ID
    JOIN "sales_platform"."marts"."dim_channel"   dc  ON f.CHANNEL_ID   = dc.CHANNEL_ID
    JOIN "sales_platform"."marts"."dim_priority"  dpr ON f.PRIORITY_ID  = dpr.PRIORITY_ID
    JOIN "sales_platform"."marts"."dim_date"      dd  ON f.ORDER_DATE_KEY = dd.DATE_KEY
),

aggregated AS (
    SELECT
        YEAR,
        MONTH,
        MONTH_NAME,
        QUARTER,
        YEAR_QUARTER,
        YEAR_MONTH,
        PRODUCT_CATEGORY,
        REGION,
        COUNTRY,
        SALES_CHANNEL,
        ORDER_PRIORITY,
        PRIORITY_LABEL,
        PRIORITY_SORT_ORDER,

        COUNT(DISTINCT ORDER_ID)              AS ORDER_COUNT,
        SUM(UNITS_SOLD)                       AS TOTAL_UNITS_SOLD,
        SUM(TOTAL_REVENUE)                    AS TOTAL_REVENUE,
        SUM(TOTAL_COST)                       AS TOTAL_COST,
        SUM(TOTAL_PROFIT)                     AS TOTAL_PROFIT,
        AVG(UNIT_PRICE)                       AS AVG_UNIT_PRICE,
        AVG(UNIT_COST)                        AS AVG_UNIT_COST,
        AVG(SHIPPING_DAYS)                    AS AVG_SHIPPING_DAYS,

        ROUND(
            SUM(TOTAL_PROFIT) / NULLIF(SUM(TOTAL_REVENUE), 0) * 100,
            2
        )                                     AS GROSS_MARGIN_PCT

    FROM enriched
    GROUP BY
        YEAR, MONTH, MONTH_NAME, QUARTER,
        YEAR_QUARTER, YEAR_MONTH,
        PRODUCT_CATEGORY, REGION, COUNTRY,
        SALES_CHANNEL, ORDER_PRIORITY,
        PRIORITY_LABEL, PRIORITY_SORT_ORDER
),

with_window_metrics AS (
    SELECT
        *,

        -- Rolling 12-month revenue by product category
        SUM(TOTAL_REVENUE) OVER (
            PARTITION BY PRODUCT_CATEGORY
            ORDER BY YEAR, MONTH
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        )                                     AS ROLLING_12M_REVENUE,

        -- Rolling 3-month profit by region
        SUM(TOTAL_PROFIT) OVER (
            PARTITION BY REGION
            ORDER BY YEAR, MONTH
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        )                                     AS ROLLING_3M_PROFIT,

        -- Month-over-month revenue growth %
        ROUND(
            (TOTAL_REVENUE - LAG(TOTAL_REVENUE) OVER (
                PARTITION BY PRODUCT_CATEGORY, REGION, SALES_CHANNEL
                ORDER BY YEAR, MONTH
            )) / NULLIF(LAG(TOTAL_REVENUE) OVER (
                PARTITION BY PRODUCT_CATEGORY, REGION, SALES_CHANNEL
                ORDER BY YEAR, MONTH
            ), 0) * 100,
            2
        )                                     AS MOM_REVENUE_GROWTH_PCT,

        -- Revenue rank within month (by product category)
        RANK() OVER (
            PARTITION BY YEAR, MONTH
            ORDER BY TOTAL_REVENUE DESC
        )                                     AS MONTHLY_REVENUE_RANK,

        -- Profit rank within month
        RANK() OVER (
            PARTITION BY YEAR, MONTH
            ORDER BY TOTAL_PROFIT DESC
        )                                     AS MONTHLY_PROFIT_RANK

    FROM aggregated
)

SELECT * FROM with_window_metrics
ORDER BY YEAR, MONTH, PRODUCT_CATEGORY, REGION