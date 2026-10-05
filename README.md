# Federated Clinic Data Harmonization PoC

A small-scale proof of concept of a federated data and semantic layer for a multi-tenant healthcare platform. Several synthetic "client clinics" live in different databases, each with its own schema conventions and five years of history with schema drift. Data is queried **in place** through Trino and mapped to one canonical model with dbt-trino. Business metrics are defined once in Apache Ossie (ex-Open Semantic Interchange) and served through dbt MetricFlow and Superset.

> Status: design settled, implementation in progress. Scope, decisions and the MVP definition of done are in [docs/PLAN.md](docs/PLAN.md). Sections below describe the target, not working code.

## What it demonstrates

- Federated querying across PostgreSQL, MySQL and Iceberg-on-S3 (RustFS, Apache Polaris REST catalog) with Trino.
- A canonical model (patient, encounter, diagnosis, claim) over tenants with different schemas, schema versions and history formats, with SCD2 history.
- One set of metric definitions in Ossie YAML, converted to MetricFlow and pushed to Superset, with tests that the values agree.
- Tenant isolation, PHI column masking and query audit with Trino access control: a tenant analyst's query physically reads only that tenant's source, and the audit log shows it.
- Planned for v2: a metadata-driven mapping registry that generates staging models for many tenants, schema drift detection, profiling and reconciliation.

## Dashboard

Superset at http://localhost:18088, dashboard "Clinic analytics". Its datasets and metrics are generated from the Ossie model (`uv run poe superset`), so it shows the same numbers as `mf query`. Log in as `tenant_a_analyst` and the same dashboard shows only clinic_a with PHI masked: Superset queries Trino as the logged-in user.

<!-- Screenshots: admin view and tenant_a_analyst view of the dashboard -->

## Stack

Trino · PostgreSQL · MySQL · Apache Iceberg · Apache Polaris · RustFS · dbt-trino · dbt MetricFlow · Apache Ossie · Superset · Python (uv) · Synthea · Docker Compose · GitHub Actions

## Production evolution

This PoC runs on open-source Trino on one machine. Below is how two components the PoC leaves out would fit if it moved toward production.

### Starburst

Starburst (Enterprise or Galaxy) is the commercial Trino distribution. The SQL, the dbt-trino project and the canonical views carry over unchanged. The gains are operational:

- **Access control.** Starburst built-in access control or the Apache Ranger integration replaces the PoC's file-based `rules.json`. Row filters on `tenant_id` and PHI column masks become managed policies with an admin UI, role inheritance and change history, instead of a file in Git.
- **Performance on federated sources.** Warp Speed (smart indexing and caching) and materialized views with refresh schedules cover the "federation first, materialize by exception" trade-off without hand-built Iceberg tables.
- **More connectors and better pushdown.** Enterprise connectors for SQL Server, Oracle and others widen the range of client databases that can be federated. Parallel reads from relational sources speed up large historical scans.
- **Catalog, lineage and audit.** Starburst catalog and query history give data discovery, column-level lineage and a central audit trail. The PoC builds these from dbt docs and a Trino event listener.
- **Data products.** Canonical and semantic datasets can be published as governed data products with owners and descriptions.

### AWS Lake Formation

Lake Formation fits the part of the platform that lives on S3. In the PoC that is the archive tenant `clinic_c`, and it would also cover any canonical tables materialized to Iceberg.

- **Catalog.** Replace the PoC's Polaris REST catalog with the AWS Glue Data Catalog, either through Glue's Iceberg REST endpoint (the same catalog protocol the PoC uses) or with `iceberg.catalog.type=glue`. Athena reads the same tables.
- **Fine-grained permissions.** Lake Formation grants at database, table, column and row level (data filters), with LF-Tags for tag-based access control. Example: tag PHI columns `phi=true` and tag tables `tenant=clinic_c`, then grant per analyst role by tag.
- **Enforcement across engines.** Athena, Redshift Spectrum and EMR enforce Lake Formation permissions natively. For Trino the options are Starburst's Lake Formation integration, or keeping Trino-side rules in sync with LF grants. The trade-off is one policy store for S3 data versus a second one for the relational sources Lake Formation does not cover. That is worth an ADR.
- **Audit.** Lake Formation data access events go to CloudTrail, which helps with PHI access audit requirements.
- **Tenant isolation at scale.** With 1,200+ tenants, LF-Tags scale better than per-table grants: one tag value per tenant and one grant per role pattern.

## How this project was built

Development used Claude Code under the rules of an AI Factory kit ([what an AI factory is](https://www.3alica.com/blog/what-is-an-ai-factory)). The kit is a method for running coding agents on evidence rather than on trust: an agent's work counts as done only when an independent check passes, and the amount of autonomy a loop gets depends on how good that check is.

In this project it shaped three things:

- **Design review before code.** The plan was stress-tested in rounds of questions with recommended answers before any code was written. The decisions it produced are recorded in [docs/PLAN.md](docs/PLAN.md).
- **Checks as the definition of done.** Every stage ends with a runnable check (`dbt build`, pytest for row and column security, seed-manifest counts, metric parity between MetricFlow and Superset), and CI runs them from a clean stack.
- **Small scoped changes with second opinions.** Changes stay within one stage, and design questions can be sent to models from other vendors for an independent read-only review.

The kit's files are not part of this repository.
