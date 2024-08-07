"""
End-to-end smoke test — verifies the full platform stack is healthy.

Checks performed:
  1. PostgreSQL: raw.sales has rows
  2. Staging:    staging.stg_sales has rows and no NULL order_ids
  3. Marts:      all 5 dimension tables and fact_sales are populated
  4. Consumption: sales_performance has rows
  5. Data quality: TOTAL_PROFIT integrity in fact_sales

Exit 0 = all green | Exit 1 = at least one failure
"""

from __future__ import annotations

import os
import sys

import psycopg2

DB_CONFIG = {
    "host":     os.environ.get("DBT_HOST",     "localhost"),
    "port":     int(os.environ.get("DBT_PORT", "5432")),
    "dbname":   os.environ.get("DBT_DBNAME",   "sales_platform"),
    "user":     os.environ.get("DBT_USER",     "platform_user"),
    "password": os.environ.get("DBT_PASSWORD", "platform_password"),
}

CHECKS = [
    # (label, SQL, expect_fn)
    ("raw.sales populated",
     "SELECT COUNT(*) FROM raw.sales",
     lambda v: v > 0),

    ("staging.stg_sales populated",
     "SELECT COUNT(*) FROM staging.stg_sales",
     lambda v: v > 0),

    ("staging.stg_sales no NULL order_id",
     "SELECT COUNT(*) FROM staging.stg_sales WHERE order_id IS NULL",
     lambda v: v == 0),

    ("marts.dim_date populated",
     "SELECT COUNT(*) FROM marts.dim_date",
     lambda v: v > 0),

    ("marts.dim_geography populated",
     "SELECT COUNT(*) FROM marts.dim_geography",
     lambda v: v > 0),

    ("marts.dim_product populated",
     "SELECT COUNT(*) FROM marts.dim_product",
     lambda v: v > 0),

    ("marts.dim_channel populated",
     "SELECT COUNT(*) FROM marts.dim_channel",
     lambda v: v > 0),

    ("marts.dim_priority populated",
     "SELECT COUNT(*) FROM marts.dim_priority",
     lambda v: v > 0),

    ("marts.fact_sales populated",
     "SELECT COUNT(*) FROM marts.fact_sales",
     lambda v: v > 0),

    ("consumption.sales_performance populated",
     "SELECT COUNT(*) FROM consumption.sales_performance",
     lambda v: v > 0),

    ("fact_sales financial integrity",
     """
     SELECT COUNT(*) FROM marts.fact_sales
     WHERE NOT (
         ROUND(TOTAL_REVENUE, 2) = ROUND(UNITS_SOLD * UNIT_PRICE, 2)
         AND ROUND(TOTAL_COST, 2) = ROUND(UNITS_SOLD * UNIT_COST, 2)
         AND ROUND(TOTAL_PROFIT, 2) = ROUND(TOTAL_REVENUE - TOTAL_COST, 2)
     )
     """,
     lambda v: v == 0),

    ("fact_sales no orphan product FK",
     """
     SELECT COUNT(*) FROM marts.fact_sales f
     LEFT JOIN marts.dim_product p ON f.PRODUCT_ID = p.PRODUCT_ID
     WHERE p.PRODUCT_ID IS NULL
     """,
     lambda v: v == 0),
]


def main() -> None:
    print("Connecting to sales_platform ...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except Exception as exc:
        print(f"[FAIL] Cannot connect: {exc}")
        sys.exit(1)

    passed = 0
    failed = 0

    with conn:
        with conn.cursor() as cur:
            for label, sql, ok_if in CHECKS:
                try:
                    cur.execute(sql)
                    value = cur.fetchone()[0]
                    if ok_if(value):
                        print(f"  [PASS] {label} (value={value})")
                        passed += 1
                    else:
                        print(f"  [FAIL] {label} (value={value})")
                        failed += 1
                except Exception as exc:
                    print(f"  [ERROR] {label}: {exc}")
                    failed += 1

    conn.close()
    print(f"\nResult: {passed} passed, {failed} failed.")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
