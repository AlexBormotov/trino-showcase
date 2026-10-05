# ADR 0002: Canonical model as federated views

- Status: accepted
- Date: 2026-10-05

## Context

Three tenants keep the same business entities in different engines, schemas, schema versions and history formats (ADR 0001, `docs/PLAN.md`). The canonical model has to present one `patient`, `encounter`, `diagnosis` and `claim` without copying source data into a central store.

## Decision

- **Every model is a Trino view, stored as an Iceberg view in the Polaris catalog** (`iceberg.staging`, `iceberg.canonical`). Nothing is created inside tenant databases, and queries always read current source data.
- **Two layers.** Staging has one view per source table and schema version. It renames columns to canonical names, fixes types and applies transform macros (`macros/transforms.sql`). Canonical is a `UNION ALL` over staging plus keys. Tenant-specific logic lives only in staging.
- **Keys are hashes of business keys**: `<entity>_hk = md5(tenant_id | natural id)`, as in Data Vault hubs. They are stable across rebuilds and unique across tenants, with no sequence to coordinate. `diagnosis_hk` hashes the description, not the code, because some archive rows have no code.
- **SCD2 on patient address.** `clinic_a` versions are replayed from its change log with `lead()` over the log sequence number. `clinic_b` and `clinic_c` keep only current state, so each patient has one open version: from `createdAt` for `clinic_b`, and from `1900-01-01` ("since unknown") for `clinic_c`. Singular tests check that versions do not overlap and that each patient has exactly one current version.
- **Known gaps are warnings, not errors.** Diagnoses and claims of encounters lost from the `clinic_c` archive fail the relationship tests with `severity: warn`. The reconciliation tests then require the orphan counts to equal what the seeder injected, so an unexpected orphan still fails the build.
- **The oracle is the clean source.** The seeder records per-tenant truth computed from Synthea before any drift (`expected` in `data/manifest.json`). pytest compares the canonical model with it: counts, cost and amount sums, status counts, gender split and coded share.

## Consequences

- Filters on `tenant_id` prune the union to one branch, so a single-tenant query touches one source system. Filters on source columns are pushed into PostgreSQL and MySQL, and a plain `count(*)` is pushed down whole.
- Transforms that rewrite values block aggregate pushdown. For `clinic_b` the cents-to-units `CASE` means `sum(total_cost_amount)` is computed in Trino over rows streamed from MySQL. Each query pays that cost again. It is the first candidate for materialization if it shows up in a measured workload (federation first, materialize by exception).
- Views over remote sources depend on those sources being up, and every query re-reads them. Materialization, a separate decision per model, trades that for staleness.
- `char(n)` columns cannot appear in Iceberg views, so staging casts them to `varchar`.
- Staging SQL is hand-written per tenant for now. The v2 mapping registry will generate it, and the canonical contract and tests stay as they are.
