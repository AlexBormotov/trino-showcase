---
title: Infrastructure
tags:
  - infrastructure
---

# Infrastructure

Hub: [[INDEX]]

**Stack:** Docker Compose; PostgreSQL 18.6, MySQL 8.4, RustFS 1.0.1 (S3), Apache Polaris 1.8.0 (Iceberg REST catalog), Trino 483, Superset 6.1.0. Python 3.12 with uv; tasks through poethepoet.

## Architecture

- Trino catalogs: `pg_clinic_a` (JDBC), `mysql_clinic_b` (JDBC, case-insensitive names), `iceberg` (Polaris REST + RustFS S3), `audit` (see [[Security]]).
- Bootstrap order by health checks: `polaris-bootstrap` (realm + root in PostgreSQL) and `create-bucket` → Polaris → `polaris-setup` (catalog `lake`) → Trino → Superset. All steps idempotent; catalog property changes need a fresh volume (`poe reset`).
- Host ports bound to 127.0.0.1: Trino 18080, Superset 18088, PostgreSQL 15432, MySQL 13306, Polaris 18181/18182, RustFS 19000/19001. Credentials are throwaway local values.
- MinIO was replaced by RustFS (MinIO archived upstream); Polaris needs `polaris.config.drop-with-purge.enabled` for Trino's DROP TABLE. See [[Decisions]] (ADR 0001).
- CI runs the whole sequence on every push: see [[Testing]].

## Code map

- [[docker-compose]] — `docker-compose.yml`
- [[infra-polaris-setup]] — `infra/polaris/setup.sh`
- [[infra-postgres-init]] — `infra/postgres/init.sql`
- [[infra-trino-catalog-iceberg]] — `infra/trino/catalog/iceberg.properties`
- [[infra-trino-catalog-mysql_clinic_b]] — `infra/trino/catalog/mysql_clinic_b.properties`
- [[infra-trino-catalog-pg_clinic_a]] — `infra/trino/catalog/pg_clinic_a.properties`
- [[pyproject]] — `pyproject.toml`
