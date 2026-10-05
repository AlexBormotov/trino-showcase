# Plan

Decisions were settled in a design review on 2026-10-05. Stages are built in order; each one ends with a runnable check.

## Scope

**MVP (v1)**

1. Sources and federation: Docker stack, synthetic data, three tenants queried through Trino.
2. Canonical model in dbt-trino: `patient`, `encounter`, `diagnosis`, `claim`, with SCD2 on `patient`.
3. Semantic layer: Ossie YAML as the source of metric definitions, converted to MetricFlow.
4. Security: per-tenant row filters, PHI column masks, query audit.
5. BI: Superset dashboards whose metrics are generated from Ossie.
6. CI: GitHub Actions brings the stack up from scratch and runs every check.

**v2**

- Metadata-driven mapping registry that generates staging models.
- Scale demo: N tenant schemas in PostgreSQL generated from one mapping template.
- Schema profiling and drift detection over Trino `information_schema`.
- Source-vs-canonical reconciliation models.
- `provider` as a canonical entity.

## Data

- Synthea 4.0, run in a throwaway `eclipse-temurin:17` container, seed `-s 42`.
- 2,000 patients per tenant, 5 years of history (2021–2026).
- A Python seeder reshapes the Synthea CSVs into each tenant's dialect and injects drift. It writes a manifest of every injected anomaly; tests read the manifest as the expected values.

| Tenant | Store | Injected drift |
|---|---|---|
| `clinic_a` | PostgreSQL | Schema v1 until 2023-12-31, v2 from 2024-01-01: renamed columns, `DD.MM.YYYY` dates as `varchar` in v1, gender `M/F/1/2`. Patient history as a change-log table. |
| `clinic_b` | MySQL | camelCase names, soft deletes. Money in cents until 2023-06-30, then in currency units. Local diagnosis codes with a lookup table to SNOMED CT. Patient history as a current snapshot with `updated_at`. |
| `clinic_c` | Iceberg on MinIO | Archive tenant, Parquet partitioned by month. 2–3 months missing. Codes stored with a system prefix (`SNOMED:44054006`), some rows with description text only. |

Canonical diagnosis code system: SNOMED CT, which is what Synthea emits (verify on Synthea 4.0 output before writing the seeder). ICD crosswalks are out of scope because the official SNOMED-to-ICD-10 map is licensed through UMLS.

## Stack

| Component | Choice | Why |
|---|---|---|
| Query engine | Trino 483 | The target architecture. |
| Iceberg catalog | Apache Polaris (Iceberg REST) | Same catalog model as AWS Glue's Iceberg REST endpoint; its RBAC maps to Lake Formation grants. |
| Object storage | MinIO | S3 API locally. |
| Transformations | dbt-core 1.12.5, dbt-trino 1.10.6 | |
| Metrics | dbt-metricflow[dbt-trino] 0.15.0, apache-ossie-dbt from a pinned apache/ossie commit | The converter is not on PyPI. |
| BI | Superset | Trino support; screenshots go into the README. |
| Python | uv, Python 3.12 | dbt does not support 3.14 yet. |
| Task runner | poethepoet (`uv run poe <task>`) | Needs nothing beyond uv; works on Windows, macOS and Linux. |

Host ports avoid 5432 and 8080, which are taken on the dev machine: Trino on 18080, PostgreSQL on 15432.

## Semantic layer

- Ossie YAML is the source. `ossie-to-msi` produces `semantic_manifest.json`, and `mf query` reads it.
- First step is a spike on one metric (encounter count). If `mf` does not accept the converted manifest, dbt `semantic_models` YAML becomes the source and Ossie is exported with `msi-to-ossie`. Record the outcome in an ADR either way.
- Metrics: active patients, encounter count, average length of stay, 30-day readmission rate, claim denial rate. Ratios are written as `(a)/(b)` so the converter emits RATIO metrics.
- A generator pushes the same Ossie metrics to Superset through its REST API. No metric SQL is hand-written in Superset.

## Security

- No authentication in v1. The user name comes from `--user` / `X-Trino-User`. An ADR describes the path to password auth over TLS and then OAuth2/SSO.
- File-based access control: row filter on `tenant_id` per role, masks on PHI (name, DOB to year, SSN/MRN hashed), event listener for audit.
- Roles: `tenant_a_analyst`, `cross_tenant_analyst`, `admin`.

## Definition of done (MVP)

- `dbt build` passes (models and tests).
- pytest against the running stack:
  - RLS: `tenant_a_analyst` sees only `clinic_a`.
  - CLS: PHI columns are masked for non-admin roles.
  - Row counts in the canonical model match the seed manifest.
  - Each metric value in Superset/Trino matches `mf query`.
- GitHub Actions runs all of the above on every push, with a small fixed seed instead of a full Synthea run. Status badge in the README.

## Repository

- `trino-showcase` on GitHub: the name says it is a reference project for the tool stack; the README title names the domain. Private until the MVP is done, then public. MIT licence, English throughout.
- Not committed: `data/`, `.claude/`, `ai-factory-kit/`, `CLAUDE.local.md`, and the personal notes `docs/QUERY.md` and `docs/GRILLME.md`.
