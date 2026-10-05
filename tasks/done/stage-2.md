# Stage 2: canonical model in dbt-trino (done)

Goal: `patient` (SCD2), `encounter`, `diagnosis`, `claim` as views over all three tenants, proven equal to the clean source. Scope and decisions: `docs/PLAN.md`. Finished stages: `tasks/done/`.

Oracle: the seeder records the clean Synthea truth per tenant (before drift) in the manifest. The canonical model must reproduce it, and must flag exactly the anomalies that were injected.

- [x] 1. dbt skeleton: `dbt_project.yml`, `profiles.yml` (Trino, catalog `iceberg`), `generate_schema_name` without prefixing, `sources.yml` for the four source schemas.
  Check: `dbt debug` passes; a trivial view lands in `iceberg.staging` and is queryable (Trino views stored in Polaris).
- [x] 2. Manifest `expected` block computed from the clean source: per tenant patients, encounters (minus clinic_c missing months), diagnoses, coded diagnoses, claims by status, encounter cost sum, gender counts.
  Check: unit test that drift does not leak into `expected`.
- [x] 3. Transform macros (`parse_dmy_ts`, `parse_dmy_date`, `gender_code`, `cents_to_amount`, `strip_code_prefix`, `surrogate_key`) and staging views: `clinic_a` v1 and v2, `clinic_b`, `clinic_c`, all in canonical column names and types.
  Check: `dbt build --select staging` green.
- [x] 4. Canonical `encounter`, `diagnosis`, `claim`: union over tenants, `tenant_id`, `source_system`, `source_schema_version`, surrogate keys; generic tests (unique, not_null, accepted_values, relationships with orphans as warn).
  Check: `dbt build --select canonical` green.
- [x] 5. Canonical `patient` with SCD2: history from the `clinic_a` change log, single open version for snapshot tenants; singular tests for no overlaps and exactly one current row.
  Check: tests green; a mover in `clinic_a` has two versions.
- [x] 6. pytest reconciliation: canonical vs manifest `expected` per tenant (counts, cost sum, status counts, gender, coded share); orphan claims and text-only diagnoses equal the injected counts.
  Check: tests pass, plus a negative control.
- [x] 7. Query plan check: a filter on `tenant_id` over the canonical union prunes the other tenants' branches.
  Check: EXPLAIN shows a single remote source.
- [x] 8. ADR 0002 (canonical views in the lake catalog, SCD2 approach), CLAUDE.md commands, commit.

## Review

- dbt: 20 views (16 staging, 4 canonical), 50 data tests: 48 pass, 2 warn by design (archive orphans, 4,123 claims and 1,260 diagnoses, exactly as injected).
- pytest: 39 pass (10 unit, 29 integration). Negative control: removing the `clinic_b` soft-delete filter fails exactly `test_encounters_and_cost`.
- Plan: a `tenant_id` filter prunes the union to one source; `count(*)` with filters runs whole inside MySQL; the cents `CASE` blocks aggregate pushdown (first materialization candidate, ADR 0002).
- Deviations: Iceberg views reject `char(n)`, staging casts to varchar; keys named `_hk` (hash of business key) instead of "surrogate key".
