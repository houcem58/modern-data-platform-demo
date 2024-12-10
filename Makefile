.PHONY: docker-up docker-down dbt-run dbt-test smoke-test lint install help

PYTHON := python
DBT := dbt

help:
	@echo "Available targets:"
	@echo "  make install      Install Python dependencies"
	@echo "  make lint         Run ruff linter"
	@echo "  make docker-up    Start PostgreSQL, Airflow, pgAdmin"
	@echo "  make docker-down  Stop all services"
	@echo "  make dbt-run      Run full dbt pipeline"
	@echo "  make dbt-test     Run dbt tests"
	@echo "  make smoke-test   Run end-to-end smoke test"
	@echo "  make load-data    Load sample sales data"

install:
	pip install -r requirements.txt

lint:
	pip install ruff --quiet
	ruff check ingestion/ scripts/ orchestration/ --ignore E501,E402

docker-up:
	docker compose up airflow-init
	docker compose up -d
	@echo "Services:"
	@echo "  Airflow: http://localhost:8080"
	@echo "  pgAdmin: http://localhost:5050"

docker-down:
	docker compose down

load-data:
	$(PYTHON) ingestion/load_sales.py --file data/sample/sales_sample.csv

dbt-run:
	cd dbt && $(DBT) deps && $(DBT) run

dbt-test:
	cd dbt && $(DBT) test

smoke-test:
	$(PYTHON) scripts/smoke_test.py
