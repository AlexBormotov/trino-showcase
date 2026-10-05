# ADR 0001: Iceberg catalog and object storage

- Status: accepted
- Date: 2026-10-05

## Context

The archive tenant `clinic_c` lives in Apache Iceberg tables on S3-compatible storage. Trino needs an Iceberg catalog to find them. The production target in the job context is AWS (S3, Glue, Lake Formation), so the local choice should follow the same catalog model and keep the migration path short.

Options considered for the catalog:

| Option | For | Against |
|---|---|---|
| JDBC catalog in the existing PostgreSQL | No extra service | No access control model; nothing like it exists in AWS |
| Hive Metastore | Close to the classic Glue/Hive model | Extra JVM service plus its own database; the Hive model is being replaced by REST catalogs |
| Iceberg REST: Lakekeeper | Small Rust binary, ~50 MB RAM | Less widely known |
| **Iceberg REST: Apache Polaris** | Apache project; RBAC (principal roles, catalog roles, privileges); same REST protocol as AWS Glue's Iceberg endpoint | JVM (~0.5 GB), needs a bootstrap step |

Object storage was planned as MinIO. On 2026-10-05 the MinIO repository was archived and its images were no longer published, so it was replaced.

## Decision

- Catalog: Apache Polaris 1.8.0 with relational-JDBC persistence in the stack's PostgreSQL (database `polaris`). Catalog `lake`, location `s3://warehouse/lake`.
- Storage: RustFS 1.0.1, the S3-compatible store used by the Polaris guides.
- Bootstrap is two idempotent compose jobs: `polaris-admin-tool bootstrap` (realm and root credentials) and `infra/polaris/setup.sh` (catalog and grants). Trino starts only after both succeed.
- The catalog sets `polaris.config.drop-with-purge.enabled=true`. Trino's `DROP TABLE` asks the catalog to purge data, and Polaris rejects that by default.
- Trino and the Python loader both authenticate as Polaris `root` and read S3 with static keys. No credential vending.

## Consequences

- Moving to AWS is a configuration change: point Trino at Glue's Iceberg REST endpoint (or `iceberg.catalog.type=glue`) and S3. Table layout and SQL do not change.
- Polaris RBAC is available for tenant isolation at the storage layer, but v1 does not use it: everything runs as `root`. A per-engine principal (Trino with read-only privileges on `clinic_c`) is a follow-up for the security stage.
- Static S3 keys on the Trino side mean Trino can read any path in the bucket regardless of Polaris grants. Credential vending (Polaris issuing scoped credentials per table) would close that gap. That is the Polaris counterpart of Lake Formation's credential vending, and the next step if storage-level isolation becomes a requirement.
- Two more services than the JDBC option, about 0.5 GB more memory.
