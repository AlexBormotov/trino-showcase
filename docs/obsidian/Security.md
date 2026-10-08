---
title: Security
tags:
  - security
---

# Security

Hub: [[INDEX]]

## Architecture

- Trino file-based access control, deny by default, first matching rule wins. Roles: `admin`; `cross_tenant_analyst` (canonical, marts, time spine; PHI masked); `tenant_a_analyst` (same + `tenant_id = 'clinic_a'`); anyone else denied.
- Masks: names and address `***`, SSN and source patient id SHA-256, birth date to year, ZIP to 3 digits.
- No bypass: analysts cannot read source catalogs, `iceberg.clinic_c` or staging; models are SECURITY DEFINER views created by admin.
- Sources read as read-only `trino_reader`.
- Audit: MySQL event listener → `trino_audit.trino_queries` (user, SQL, state, error, `inputs_json`); catalog `audit` for admin only. Audit shows a tenant_a query on the union reads only PostgreSQL.
- **A new canonical or marts model is invisible to analysts until it gets a rule per analyst role** (+ masks for PHI, filter if it has tenant_id). Restart Trino after editing rules.
- Known gaps: no authentication (spoofable user header), unsalted SHA-256, mf runs as admin, RustFS keys bypass Trino. See [[Decisions]] (ADR 0004).

## Code map

- [[infra-mysql-init]] — `infra/mysql/init.sql`
- [[infra-trino-access-control]] — `infra/trino/access-control.properties`
- [[infra-trino-catalog-audit]] — `infra/trino/catalog/audit.properties`
- [[infra-trino-event-listener]] — `infra/trino/event-listener.properties`
- [[infra-trino-rules]] — `infra/trino/rules.json`
