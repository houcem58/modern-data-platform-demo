"""
Source validation — checks raw.sales row count, null rates, and date ranges.
Raises SystemExit(1) if any quality gate fails (used as an Airflow pre-check).
"""

from __future__ import annotations

import logging
import os
import sys

import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DB_CONFIG = {
    "host":     os.environ.get("DBT_HOST",     "localhost"),
    "port":     int(os.environ.get("DBT_PORT", "5432")),
    "dbname":   os.environ.get("DBT_DBNAME",   "sales_platform"),
    "user":     os.environ.get("DBT_USER",     "platform_user"),
    "password": os.environ.get("DBT_PASSWORD", ""),
}

CHECKS = [
    # (description, SQL, fail_if)
    (
        "Row count > 0",
        "SELECT COUNT(*) FROM raw.sales",
        lambda v: v == 0,
    ),
    (
        "NULL ORDER_ID rate < 1%",
        'SELECT ROUND(SUM(CASE WHEN "ORDER_ID" IS NULL THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) FROM raw.sales',
        lambda v: v is not None and v >= 1,
    ),
    (
        "NULL ORDER_DATE rate < 1%",
        'SELECT ROUND(SUM(CASE WHEN "ORDER_DATE" IS NULL THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) FROM raw.sales',
        lambda v: v is not None and v >= 1,
    ),
    (
        "No future ORDER_DATE",
        'SELECT COUNT(*) FROM raw.sales WHERE "ORDER_DATE" > CURRENT_DATE',
        lambda v: v > 0,
    ),
    (
        "SHIP_DATE >= ORDER_DATE (no negative lead time)",
        'SELECT COUNT(*) FROM raw.sales WHERE "SHIP_DATE" < "ORDER_DATE"',
        lambda v: v > 0,
    ),
    (
        "UNITS_SOLD all positive",
        'SELECT COUNT(*) FROM raw.sales WHERE "UNITS_SOLD" <= 0',
        lambda v: v > 0,
    ),
]


def validate() -> None:
    log.info("Connecting to sales_platform for source validation ...")
    conn = psycopg2.connect(**DB_CONFIG)
    failures: list[str] = []

    try:
        with conn.cursor() as cur:
            for description, sql, fail_if in CHECKS:
                cur.execute(sql)
                value = cur.fetchone()[0]
                if fail_if(value):
                    log.error("FAIL  [%s] — value: %s", description, value)
                    failures.append(description)
                else:
                    log.info("PASS  [%s] — value: %s", description, value)
    finally:
        conn.close()

    if failures:
        log.error("%d quality gate(s) failed: %s", len(failures), failures)
        sys.exit(1)

    log.info("All source validation checks passed.")


if __name__ == "__main__":
    validate()
