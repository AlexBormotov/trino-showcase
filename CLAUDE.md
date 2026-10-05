# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

Stages 1 (sources and federation), 2 (canonical model), 3 (semantic layer), 4 (security) and 5 (Superset) are done; see `tasks/todo.md` for the current stage and `tasks/done/` for finished ones. Decisions: `docs/adr/`. `docs/PLAN.md` is the source of truth for scope, stack versions, tenant drift and the MVP definition of done; read it before planning any stage. `README.md` is the public face and holds the "Production evolution" section (Starburst, AWS Lake Formation); keep it in sync when the architecture changes. Everything below describes the target design. Update this file as pieces get built, and remove the "planned" notes once a command actually works.

## Working rules

- Plan before any non-trivial task. Keep the current stage's task list in `tasks/todo.md`, and record user corrections in `tasks/lessons.md`. Read `tasks/lessons.md` at session start.
- A task is done only when a runnable check passes: a query result, `dbt build`, a pytest, or a manifest comparison.
- Everything committed is in English: code, docs, ADRs, commit messages. The repository becomes public after the MVP.

## Purpose

Portfolio PoC that mirrors a federated data and semantic layer architecture for a multi-tenant healthcare platform at small scale:
1. Trino federated querying.
2. Semantic layer: Apache Ossie (ex-Open Semantic Interchange) YAML, converted to dbt MetricFlow and pushed to Superset.
3. Multi-tenancy, row-level security, PHI column masking, query audit.

Every design choice should be explainable as a trade-off. Record non-obvious decisions as ADRs in `docs/adr/`.

## Domain scenario

Synthetic multi-tenant healthcare SaaS: several "client clinics", each with its own database, its own schema conventions and history with schema drift. They are queried **in place** through Trino (no central consolidation), mapped to one canonical model, and expose consistent metrics.

| Tenant | Engine (Trino catalog) | Deliberate quirks |
|---|---|---|
| `clinic_a` | PostgreSQL (`pg_clinic_a`) | Schema v1 until 2023-12-31, v2 after: renamed columns, `DD.MM.YYYY` dates as `varchar` in v1, gender `M/F/1/2`; patient change log |
| `clinic_b` | MySQL (`mysql_clinic_b`) | camelCase, soft deletes, money in cents until 2023-06-30, local diagnosis codes + lookup to SNOMED; patient snapshot with `updated_at` |
| `clinic_c` | Iceberg on RustFS via Polaris (`iceberg`) | Archive tenant, Parquet by month, missing months, prefixed codes and text-only diagnoses |

Source data: Synthea CSV export (run in a container), reshaped by a Python seeder that injects drift, duplicates, nulls and missing months on purpose. The seeder writes a manifest of what it injected; tests treat the manifest as expected values, so any change to injection must update the manifest in the same change.

## Target architecture

```
sources (pg / mysql / iceberg)  ->  Trino catalogs  ->  dbt-trino
   staging/<tenant>/<schema_version>   (views)
   canonical/                          (union over tenants, tenant_id column, views by default)
   marts/                              (fct_encounter, fct_claim, dim_patient: row-level flags)
-> semantic/clinic_analytics.yaml (Ossie) -> semantic/compile.py -> target/semantic_manifest.json -> mf
                                         -> semantic/superset_sync.py -> Superset datasets, metrics, dashboard
```

Key ideas, which require reading several parts together:

- **Transforms are dbt macros** (`macros/transforms/`, e.g. `parse_date_dmy`, `gender_code`, `cents_to_amount`), so the same rule is reused across tenants and schema versions.
- **Staging** (`models/staging/<tenant>/stg_<tenant>__[<version>_]<table>.sql`): one view per source table and schema version, already in canonical column names, types and order. Canonical models `UNION ALL` staging with `select *`, so **every staging model of an entity must keep the same column order**.
- **Canonical model** (`models/canonical/`): `patient`, `encounter`, `diagnosis`, `claim`, all views stored in Polaris (`iceberg.canonical`). Keys are hashes of business keys (`<entity>_hk`, macro `hash_key`); `patient_hk` is durable across versions, `patient_version_hk` identifies an SCD2 version. Every row carries `tenant_id`, `source_system`, `source_schema_version`. `patient` keeps SCD2 history (`valid_from_ts`/`valid_to_ts`/`is_current`), replayed from the `clinic_a` change log; snapshot tenants have one open version. See ADR 0002.
- **Federation first, materialize by exception.** Canonical models are views. Materializing to Iceberg is a measured decision (EXPLAIN ANALYZE before/after, ADR), not a default.
- **Oracles.** `data/manifest.json` holds `expected` (clean Synthea truth per tenant) and `injected` (what drift was added). `tests/integration/test_canonical.py` requires the canonical model to equal `expected`, and orphan counts to equal `injected`. dbt relationship tests on `clinic_c` orphans are `warn` by design. Never loosen a reconciliation assertion to make it pass: find which transform is wrong.
- **One metric definition.** Metrics live only in `semantic/clinic_analytics.yaml` (Ossie); `docs/metrics.md` explains them. MetricFlow and Superset receive generated definitions (Superset via sqlglot translation, ADR 0005); never hand-write metric SQL in marts or BI. Marts hold only row-level flags (`readmitted_30d`, `denied_claim`, ...) that Ossie aggregates, because Ossie expressions cannot span rows. `tests/integration/test_metrics.py` checks every metric against the manifest or independent SQL; `tests/unit/test_semantic.py` checks the Ossie round trip.
- **Security** (`infra/trino/rules.json`, ADR 0004): file-based access control, deny by default, first matching rule wins. Analysts (`tenant_a_analyst`, `cross_tenant_analyst`) see only `iceberg.canonical|marts|semantic`, with PHI masks; `tenant_a_analyst` also gets `tenant_id = 'clinic_a'`. **A new model in `canonical` or `marts` is invisible to analysts until it gets a rule for each analyst role; add masks if it has PHI columns, and a filter if it has `tenant_id`.** Trino reads sources as read-only `trino_reader`. Every query is audited to MySQL `trino_audit` (catalog `audit`, admin only). There is no authentication: the user name is trusted as sent. Rules are read at startup: restart Trino after editing.
- **Users in code**: dbt, MetricFlow and the tests run as `admin`; `tests/integration/test_security.py` uses the analyst roles. Superset impersonates its logged-in user towards Trino; Superset logins are `admin`/`admin`, and each analyst's password equals the user name (throwaway local values).
- **Seeder** (`seed/`): `build.py` is pure pandas (Synthea frames -> tenant dialects + injected drift, unit-tested on tiny fixtures), `load.py` writes PostgreSQL via COPY, MySQL via batched inserts, and Iceberg via PyIceberg straight to Polaris (not through Trino). Tenant DDL lives in `infra/tenants/*.sql`. Integration tests compare Trino counts with `data/manifest.json`.
- **Stack bootstrap** is ordered by compose health checks: `polaris-bootstrap` (realm + root credentials in PostgreSQL) and `create-bucket` must finish before Polaris starts; `polaris-setup` (`infra/polaris/setup.sh`, creates catalog `lake` on `s3://warehouse/lake`) must finish before Trino starts. Both are idempotent, so `poe up` is safe to rerun. Changing catalog properties in `setup.sh` takes effect only on a fresh volume (`poe reset`).
- v2 adds a metadata-driven mapping registry (`mappings/<tenant>.yml` generating staging models), profiling and reconciliation; see `docs/PLAN.md`.

## Planned commands

Local stack runs on Docker Desktop. Python tooling is uv + Python 3.12; tasks run through poethepoet. Host ports are shifted to avoid other local stacks: Trino 18080, PostgreSQL 15432, MySQL 13306, RustFS 19000/19001, Polaris 18181/18182. Inside the compose network services use their standard ports. Stack credentials in `docker-compose.yml` and `infra/` are throwaway local values.

```bash
uv sync                                   # Python deps (dbt, MetricFlow, seeder)
uv run poe up                             # docker compose up -d --wait (works)
uv run poe down / uv run poe reset        # stop / stop and drop volumes (works)
uv run poe synthea                        # Synthea in a container -> data/synthea/csv (slow, ~5 min; works)
uv run poe seed                           # build tenant tables, write data/manifest.json, load all stores (works)
uv run dbt build                          # models + tests; profiles.yml is in the repo root (works)
uv run dbt build --select staging.clinic_a+   # one tenant and everything downstream (works)
uv run poe semantic                       # dbt parse + Ossie -> target/semantic_manifest.json (works)
PYTHONIOENCODING=utf-8 uv run mf query --metrics encounter_count --group-by encounter__tenant_id   # (works)
uv run poe superset                        # publish Ossie datasets/metrics/charts to Superset, http://localhost:18088 (works)
uv run pytest                             # all tests; integration ones need the stack up and a seed (works)
uv run pytest tests/unit                   # unit tests only; no stack or seed needed (works)
uv run pytest tests/unit/test_build.py::test_clinic_b_money_is_in_cents_before_mid_2023
docker compose exec trino trino --user tenant_a_analyst   # see the data as an analyst (works)
```

## Conventions

- Canonical names: `snake_case`, singular table names, `_dt` for dates, `_ts` for timestamps, `_id` for keys, `_amount` for money in currency units.
- Trino lowercases identifiers: MySQL camelCase tables and columns appear as `visit`, `isdeleted` (the catalog sets `case-insensitive-name-matching=true`).
- SQL is Trino dialect. Check that predicates push down to PostgreSQL/MySQL connectors (`EXPLAIN`) when writing staging filters.
- Ossie is pre-release (spec 0.2.0.dev0, Apache Incubator since July 2026). The converter is pinned to an apache/ossie commit in `pyproject.toml`; verify the spec at that commit before changing `semantic/clinic_analytics.yaml`, do not write the YAML from memory. Rules learned in the spike (ADR 0003): set `dimension: {is_time: true}` explicitly; name a dataset's key field after the entity (`encounter`, expression `encounter_hk`); declare `agg_time_dimension` per dataset in a `custom_extensions` DBT entry. `dbt parse` alone overwrites `target/semantic_manifest.json` without metrics, so run `poe semantic` before `mf`.
- `mf` and `ossie-dbt` print non-ASCII characters and crash on a Windows cp1251 console unless `PYTHONIOENCODING=utf-8` is set.
- Docs live in `docs/`: `PLAN.md`, `adr/`, metric catalog. `dbt docs` provides lineage.
