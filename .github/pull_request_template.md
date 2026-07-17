## Summary

<!-- What does this PR change and why? -->

## Type of change

- [ ] Bug fix (pipeline failure, data quality issue)
- [ ] New dbt model or dimension
- [ ] Schema change (raw.sales or marts)
- [ ] Airflow DAG change
- [ ] Ingestion script change
- [ ] Performance improvement
- [ ] Documentation update
- [ ] Dependency update

## Data quality impact

<!-- If this touches a dbt model, paste `dbt test` output below -->

```
dbt test output here
```

## Checklist

- [ ] `make lint` passes
- [ ] `make dbt-test` passes with no new failures
- [ ] `make smoke-test` passes
- [ ] If schema changed: `docs/Architecture.md` updated
- [ ] If new model: model documented in `docs/Architecture.md` and tested in `schema.yml`
- [ ] If incremental strategy changed: ADR created in `docs/decisions/`
- [ ] Airflow SLAs unaffected (total pipeline < 20 min)
