# Engineering Standards — Modern Data Platform

These standards apply to all contributions to the data platform. They encode working agreements
for maintainability, data quality, and operational reliability.

---

## dbt Model Standards

### Naming conventions

| Layer | Prefix | Example |
|---|---|---|
| Staging | `stg_` | `stg_sales` |
| Dimensions | `dim_` | `dim_geography` |
| Facts | `fact_` | `fact_sales` |
| Consumption | _(no prefix)_ | `sales_performance` |
| Staging schema | `staging` | |
| Marts schema | `marts` | |
| Consumption schema | `consumption` | |

### Model requirements

Every dbt model must have:
1. A `schema.yml` entry with `description` and at least one test
2. A corresponding entry in `docs/Architecture.md` (Incremental Strategy table)
3. Column descriptions for all output columns

**Fact models** must additionally have:
- An incremental strategy declared (`merge` or `delete+insert`)
- A unique key declared
- A `not_null` test on the unique key
- A `relationships` test to each dimension FK

### SQL style

- Use uppercase for SQL keywords: `SELECT`, `FROM`, `WHERE`, `GROUP BY`
- Use `ref()` for all cross-model references (never hardcode schema.table)
- Use `source()` for raw layer references
- No SELECT * — always name columns explicitly in consumption and fact models
- Comments on non-obvious business logic only; no "this selects revenue" comments

---

## Python Standards

### Ingestion scripts

- Environment-based DB config only — no hardcoded credentials
- Structured logging with `logging.getLogger(__name__)`
- `sys.exit(1)` on unrecoverable errors (Airflow integration requirement)
- All functions typed with return annotations
- Unit tests required for date parsing, coercion, and quality gate logic

### Quality gates

Every new quality gate in `validate_source.py` must:
1. Be added to the `CHECKS` list (not as a standalone query)
2. Have a unit test in `tests/test_validate_source.py`
3. Be documented in the quality gate table in `docs/Architecture.md`
4. Have a corresponding recovery procedure in `docs/Runbook.md`

---

## Data Quality Policy

### The no-silent-failure rule

Data quality failures must surface visibly. Never:
- Catch exceptions and continue silently
- Log at DEBUG level for data errors that affect row counts
- Use `ON CONFLICT DO NOTHING` without logging the skip count

Currently `load_sales.py` uses `ON CONFLICT DO NOTHING`. Any row that conflicts is silently
skipped. Future work: log the skip count at INFO level so ingestion runs show actual vs.
expected row counts.

### Test coverage requirement

Every dbt model in marts or consumption must have:
- At minimum: `not_null` + `unique` on the primary key
- For fact tables: `relationships` tests on all FK columns
- For consumption models: a `dbt_utils.at_least_one` test on the row count

---

## Airflow DAG Standards

### Task naming

Tasks must be named after the dbt model they run or the Python operation they execute:
- `validate_source` (not `check_data`)
- `dbt_staging` (not `run_staging`)
- `notify_success` (not `send_email`)

### SLA policy

Each task has a declared SLA (see Runbook). If a task consistently exceeds its SLA:
1. Open a GitHub issue with the `performance` label
2. Profile the slow query or dbt model
3. Add an index or refactor before the next release

### Retry policy

- `validate_source`: 0 retries (data error should halt immediately)
- `dbt_*`: 1 retry with 5-minute delay (transient DB connection issues)
- `notify_*`: 2 retries with 1-minute delay (email delivery issues)

---

## Commit and PR Standards

```
<type>(<scope>): <short summary>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `ci`, `chore`

Scopes: `ingestion`, `staging`, `dims`, `fact`, `consumption`, `airflow`, `ci`, `docs`

Examples:
```
feat(dims): add dim_channel with incremental append strategy

fix(ingestion): log skip count when ON CONFLICT DO NOTHING fires

test(validate): add unit tests for future ORDER_DATE gate

docs(lineage): add column-level lineage for TOTAL_REVENUE
```

**PR requirements:**
- `make lint` passes
- `make dbt-test` passes (or dbt test output included with explanation for failures)
- `make smoke-test` passes
- PR template filled out completely
- `docs/Architecture.md` updated if schema changed

---

## Release Process

1. Update `CHANGELOG.md` — move Unreleased to new version
2. Run `make dbt-run && make dbt-test` to confirm clean state
3. Create GitHub Release with version tag (`v1.x.0`)
4. Release notes include: what changed, dbt model list, any breaking changes
5. Breaking changes (schema change, new required env var) → major version bump
