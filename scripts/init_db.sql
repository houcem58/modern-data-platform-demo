-- Sales Platform — PostgreSQL initialization script
-- Executed once on first container start (docker-entrypoint-initdb.d)

-- ── Databases ────────────────────────────────────────────────────────────────
-- The Airflow DB is already created by POSTGRES_DB env var.
-- Create the sales platform DB separately.
CREATE DATABASE sales_platform;

-- ── Users ────────────────────────────────────────────────────────────────────
CREATE USER platform_user WITH PASSWORD 'platform_password';
CREATE USER airflow     WITH PASSWORD 'airflow_password';

-- ── Sales platform grants ─────────────────────────────────────────────────────
\connect sales_platform

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS consumption;

GRANT ALL PRIVILEGES ON DATABASE sales_platform TO platform_user;
GRANT ALL PRIVILEGES ON SCHEMA raw         TO platform_user;
GRANT ALL PRIVILEGES ON SCHEMA staging     TO platform_user;
GRANT ALL PRIVILEGES ON SCHEMA marts       TO platform_user;
GRANT ALL PRIVILEGES ON SCHEMA consumption TO platform_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw         GRANT ALL ON TABLES TO platform_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging     GRANT ALL ON TABLES TO platform_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA marts       GRANT ALL ON TABLES TO platform_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA consumption GRANT ALL ON TABLES TO platform_user;

-- Raw sales table (populated by ingestion/load_sales.py)
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

CREATE INDEX IF NOT EXISTS idx_raw_sales_order_id   ON raw.sales ("ORDER_ID");
CREATE INDEX IF NOT EXISTS idx_raw_sales_order_date ON raw.sales ("ORDER_DATE");

-- ── Airflow DB grants ─────────────────────────────────────────────────────────
\connect airflow
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
