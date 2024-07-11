"""
Ingestion script — loads a sales CSV file into PostgreSQL raw.sales.

Usage:
    python ingestion/load_sales.py --file data/sample/sales_sample.csv
    python ingestion/load_sales.py --file /path/to/full_sales.csv --truncate
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── DB config from environment ──────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("DBT_HOST",     "localhost"),
    "port":     int(os.environ.get("DBT_PORT", "5432")),
    "dbname":   os.environ.get("DBT_DBNAME",   "sales_platform"),
    "user":     os.environ.get("DBT_USER",     "platform_user"),
    "password": os.environ.get("DBT_PASSWORD", ""),
}

CREATE_SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw.sales (
    "ORDER_ID"       BIGINT,
    "REGION"         VARCHAR(100),
    "COUNTRY"        VARCHAR(100),
    "ITEM_TYPE"      VARCHAR(100),
    "SALES_CHANNEL"  VARCHAR(50),
    "ORDER_PRIORITY" VARCHAR(10),
    "ORDER_DATE"     DATE,
    "SHIP_DATE"      DATE,
    "UNITS_SOLD"     INTEGER,
    "UNIT_PRICE"     NUMERIC(12, 2),
    "UNIT_COST"      NUMERIC(12, 2),
    "TOTAL_REVENUE"  NUMERIC(14, 2),
    "TOTAL_COST"     NUMERIC(14, 2),
    "TOTAL_PROFIT"   NUMERIC(14, 2),
    _ingested_at     TIMESTAMP DEFAULT NOW()
);
"""

TRUNCATE_SQL = "TRUNCATE TABLE raw.sales;"

INSERT_SQL = """
INSERT INTO raw.sales (
    "ORDER_ID", "REGION", "COUNTRY", "ITEM_TYPE", "SALES_CHANNEL",
    "ORDER_PRIORITY", "ORDER_DATE", "SHIP_DATE", "UNITS_SOLD",
    "UNIT_PRICE", "UNIT_COST", "TOTAL_REVENUE", "TOTAL_COST", "TOTAL_PROFIT"
) VALUES %s
ON CONFLICT DO NOTHING;
"""

EXPECTED_COLUMNS = {
    "Order ID", "Region", "Country", "Item Type", "Sales Channel",
    "Order Priority", "Order Date", "Ship Date", "Units Sold",
    "Unit Price", "Unit Cost", "Total Revenue", "Total Cost", "Total Profit",
}


def _parse_date(value: str) -> str | None:
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _coerce_row(row: dict) -> tuple:
    return (
        int(row.get("Order ID", 0) or 0),
        row.get("Region", "").strip(),
        row.get("Country", "").strip(),
        row.get("Item Type", "").strip(),
        row.get("Sales Channel", "").strip(),
        row.get("Order Priority", "").strip(),
        _parse_date(row.get("Order Date", "")),
        _parse_date(row.get("Ship Date", "")),
        int(row.get("Units Sold", 0) or 0),
        float(row.get("Unit Price", 0) or 0),
        float(row.get("Unit Cost", 0) or 0),
        float(row.get("Total Revenue", 0) or 0),
        float(row.get("Total Cost", 0) or 0),
        float(row.get("Total Profit", 0) or 0),
    )


def load(file_path: str, truncate: bool = False, batch_size: int = 1000) -> None:
    path = Path(file_path)
    if not path.exists():
        log.error("File not found: %s", path)
        sys.exit(1)

    log.info("Connecting to %s@%s:%s/%s",
             DB_CONFIG["user"], DB_CONFIG["host"],
             DB_CONFIG["port"], DB_CONFIG["dbname"])

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_SCHEMA_SQL)
                cur.execute(CREATE_TABLE_SQL)
                if truncate:
                    log.info("Truncating raw.sales before load")
                    cur.execute(TRUNCATE_SQL)

        log.info("Loading %s ...", path)
        rows_loaded = 0
        rows_skipped = 0
        batch: list[tuple] = []

        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            # Validate columns
            file_cols = set(reader.fieldnames or [])
            missing = EXPECTED_COLUMNS - file_cols
            if missing:
                log.warning("Missing expected columns: %s", missing)

            with conn:
                with conn.cursor() as cur:
                    for row in reader:
                        try:
                            batch.append(_coerce_row(row))
                        except (ValueError, TypeError) as exc:
                            rows_skipped += 1
                            log.debug("Skipping row (parse error): %s — %s", row, exc)

                        if len(batch) >= batch_size:
                            execute_values(cur, INSERT_SQL, batch)
                            rows_loaded += len(batch)
                            log.info("  %d rows loaded ...", rows_loaded)
                            batch = []

                    if batch:
                        execute_values(cur, INSERT_SQL, batch)
                        rows_loaded += len(batch)

        log.info("Done. Loaded: %d rows | Skipped: %d rows", rows_loaded, rows_skipped)

    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Load sales CSV into PostgreSQL raw.sales")
    parser.add_argument("--file",      required=True,      help="Path to the sales CSV file")
    parser.add_argument("--truncate",  action="store_true", help="Truncate raw.sales before loading")
    parser.add_argument("--batch-size", type=int, default=1000, dest="batch_size")
    args = parser.parse_args()

    load(args.file, truncate=args.truncate, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
