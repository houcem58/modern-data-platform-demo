# Contributing

Thank you for your interest in contributing to the Modern Data Platform Demo.

## Ways to Contribute

- **Bug reports** — open an issue with steps to reproduce and expected vs actual behavior
- **New dbt models** — add a staging, mart, or consumption model with tests and documentation
- **Data quality gates** — extend `validate_source.py` with additional source checks
- **DAX measures** — add to `analytics/dax_measures.md` with full syntax and business definition
- **Documentation** — improve any doc under `docs/` or the main README

## Development Setup

```bash
git clone https://github.com/houcem58/modern-data-platform-demo.git
cd modern-data-platform-demo
cp .env.example .env

# Start the stack
docker compose up airflow-init
docker compose up -d

# Install Python deps
pip install -r requirements.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

## Code Standards

### Python

- Type hints on all function parameters and return values
- `ruff check` must pass (except E501 for long strings)
- No print statements in library code — use proper return values
- `validate_source.py` gates must raise `SystemExit(1)` on failure (not return False)

### dbt

- Every new model must have a corresponding entry in `schema.yml`
- Every column in `schema.yml` must have a `description`
- Every model must have at least `not_null` and `unique` tests on its primary key
- Incremental models must document their `unique_key` and `incremental_strategy`
- Follow existing naming conventions: `stg_*` for staging, `dim_*`/`fact_*` for marts

### SQL

- Column names in UPPER_CASE (dbt convention for this project)
- CTE-based structure: source CTE → transform CTE → final SELECT
- No subqueries where a CTE would be clearer

## Adding a New dbt Model

1. Add the SQL in the appropriate `models/` subfolder
2. Add a schema entry in the corresponding `schema.yml` with tests and descriptions
3. If incremental: document `unique_key` and `incremental_strategy` in a YAML comment
4. Run `dbt test --select your_model_name` locally before opening a PR
5. Update `CHANGELOG.md` under `[Unreleased]`

## Pull Request Process

1. Branch from `main` with a descriptive name (`feat/dim-vendor`, `fix/null-order-id-gate`)
2. Keep commits atomic and descriptive
3. All CI checks must pass: lint, dbt compile, DAG validate, docker-validate, integration
4. Update `CHANGELOG.md` under `[Unreleased]`
5. PRs require one reviewer approval before merge

## Reporting Issues

When filing a bug:
- Component (dbt / Airflow / ingestion / Power BI)
- Docker Compose version and OS
- Full error message and stack trace
- Steps to reproduce from a clean `docker compose up`
