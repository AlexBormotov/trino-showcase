# ADR 0004: Tenant isolation, PHI masking and audit in Trino

- Status: accepted
- Date: 2026-10-05

## Context

Analysts query a model that unions every client's data, and the data contains PHI. A tenant-scoped analyst must see only their tenant's rows. No analyst may see direct identifiers. Nobody may sidestep the rules by querying a source catalog. Every access attempt has to be traceable. v1 has no authentication (decision Q7 in the design review).

## Decision

**Enforcement point: Trino.** Every consumer (SQL clients, MetricFlow, BI) goes through it, and it is the only component that sees all tenants.

- **Roles** (`infra/trino/rules.json`, file-based access control, deny by default):

  | User | Catalogs | Rows | PHI |
  |---|---|---|---|
  | `admin` | all | all | raw |
  | `cross_tenant_analyst` | `iceberg` read-only: `canonical`, `marts`, `semantic` | all | masked |
  | `tenant_a_analyst` | same | `tenant_id = 'clinic_a'` | masked |
  | anyone else | none | none | none |

- **Masks**: first and last name and street address become `'***'`. SSN and the source patient id become SHA-256 hex. Birth date is truncated to January 1st. ZIP keeps three digits (`018**`). Hash keys (`patient_hk`) stay usable for joins.
- **No bypass through sources.** Analysts get no access to tenant catalogs (`pg_clinic_a`, `mysql_clinic_b`), to `iceberg.clinic_c` or to `iceberg.staging`. The model views are `SECURITY DEFINER`, created by `admin` through dbt, so they read sources with the owner's rights while the analyst's own grants stop at the canonical layer.
- **Least privilege towards sources.** Trino connects to PostgreSQL and MySQL as `trino_reader`, which has `SELECT` on the tenant schemas only. Even `admin` cannot write to a tenant database through Trino, and the MySQL catalog shows only `clinic_b`. The seeder keeps its own admin credentials.
- **Audit**: the MySQL event listener records every query, successful or failed. A record holds the user, the SQL, the state, the error code, and `inputs_json`, which lists the physical source tables actually read. The records go to `trino_audit` (a separate database and writer user). The `audit` catalog reads them with a select-only user, and only `admin` may use it.

## Consequences

- Row filtering plus union pruning (ADR 0002) isolate tenants physically, not only logically. A `tenant_a_analyst` query on `canonical.encounter` reads only PostgreSQL; the audit's `inputs_json` proves it and a test asserts it.
- **There is no authentication.** The user is whatever the client sends in `X-Trino-User`, so anyone who can reach port 18080 can claim `admin`. The rules are correct, but they rest on a spoofable identity. Before real data the next steps are password or certificate authentication over TLS, then OAuth2/SSO with group membership (`tenant:clinic_a`) mapped to roles.
- **Rules are per user and per table, and the first match wins.** Every new table needs its rule, in the right order. Rules for two analyst roles are already repetitive; for 1,200 tenants they would have to be generated, or replaced by attribute-based policies: Trino's OPA plugin (filter `tenant_id = current user's tenant attribute`) or Apache Ranger (central admin UI, policy audit). Both plugins ship in the Trino image. Starburst's built-in access control is the managed version of the same thing (README, "Production evolution").
- **Hashes are not anonymization.** Unsalted SHA-256 of a nine-digit SSN can be reversed by enumeration. Production needs a keyed HMAC with the key in a secret store, or tokenization. Birth year, 3-digit ZIP and city together are still quasi-identifiers. Masking here follows HIPAA Safe Harbor shapes; it is not a de-identification certificate.
- **The semantic layer runs as `admin`.** `mf query` uses the dbt profile, so MetricFlow results are not filtered per analyst. A BI tool must pass the end user's identity to Trino (Superset supports impersonation) so that the same rules apply. This is a requirement for the BI stage.
- **Storage is outside these rules.** Anyone with the RustFS keys can read `clinic_c` Parquet directly (ADR 0001). Polaris RBAC with credential vending, or Lake Formation on AWS, closes that gap.
- The rules file is read at startup; changing it needs a Trino restart (or `security.refresh-period`).
