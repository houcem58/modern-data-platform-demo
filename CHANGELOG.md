# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [1.2.0] — 2026-01-20

### Added
- `docs/BusinessCase.md` — target environments, technology decision rationale
- `CONTRIBUTING.md` — contributor guide, code standards, model extension guide
- `SECURITY.md` — vulnerability reporting process
- `ROADMAP.md` — planned enhancements and future directions
- `Makefile` — developer shortcuts (`make docker-up`, `make dbt-run`, `make smoke-test`)
- `.pre-commit-config.yaml` — ruff + sqlfluff + pre-commit-hooks
- `.dockerignore` — exclude dev artifacts from Docker build context
- README restructured: The Problem → The Solution → Business Value sections added

### Changed
- README now opens with problem/solution narrative before architecture
- Badges moved to top of README under project header

---

## [1.1.0] — 2025-12-20

### Added
- Unified `pipeline.yml` replacing ci.yml + cd.yml
- `deploy-docs` job: generates dbt docs and deploys to GitHub Pages on main push
- `concurrency` group to cancel stale runs
- Docker image publish to GHCR on main push
- `docker-validate` job: validates `docker compose config` on every PR

### Changed
- Replaced `workflow_run` trigger with direct `push: branches: [main]`

### Fixed
- CD was always "skipped" due to `workflow_run` trigger completing even on CI failure

---

## [1.0.0] — 2025-11-05

### Added
- 4-layer dbt pipeline: staging → marts (star schema) → consumption
- Star schema: `dim_date`, `dim_geography`, `dim_product`, `dim_channel`, `dim_priority`, `fact_sales`
- `sales_performance` consumption model: monthly grain, window functions (rolling 12M revenue, MoM growth, rankings)
- `validate_source.py` — 6 source quality gates with SystemExit(1) on failure
- Airflow DAG: daily 06:00 UTC, 7 tasks, email notification on success/failure
- Power BI semantic model, DAX measure library (10 measures), page templates
- Docker Compose stack: PostgreSQL 15, Airflow 2.9, pgAdmin
- `smoke_test.py` — end-to-end validation across all 4 schema layers
- dbt singular test: financial integrity (TOTAL_REVENUE = UNITS_SOLD × UNIT_PRICE)
- 50-row synthetic sample dataset
- Apache 2.0 license
