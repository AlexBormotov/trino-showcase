# Stage 4: security (tenant isolation, PHI masking, audit)

Goal: analysts see only their tenant's rows and never raw PHI, cannot bypass that through source catalogs, and every query is audited. Scope: `docs/PLAN.md`.

- [x] 1. Least-privilege source credentials: Trino reads PostgreSQL and MySQL as read-only users limited to the tenant schemas; the seeder keeps admin credentials.
  Check: reads work; `INSERT` through `pg_clinic_a` and `mysql_clinic_b` fails; the MySQL catalog shows only `clinic_b`.
- [x] 2. Trino file-based access control: `admin` (all), `cross_tenant_analyst` (canonical, marts, semantic; PHI masked), `tenant_a_analyst` (same plus row filter `tenant_id = 'clinic_a'`); everyone else denied. Masks: names and address hidden, SSN and source patient id hashed, birth date to year, ZIP to 3 digits.
  Check: pytest per role (rows, masks, denied source/staging access, unknown user denied).
- [x] 3. Audit: MySQL event listener writes every completed query (user, SQL, tables, state) to `trino_audit`; an `audit` catalog exposes it to `admin` only.
  Check: a tagged query by `tenant_a_analyst` appears in the audit table; analysts cannot read it.
- [x] 4. ADR 0004 (access model, what file-based rules cannot do, path to OPA/Ranger/Starburst and Polaris RBAC), CLAUDE.md, README, commit.

## Review

- 24 security tests (rows, masks, bypass attempts, unknown user, read-only sources, audit of finished and denied queries); full suite 73 passed. Negative control: dropping the clinic_a filter on encounter/diagnosis/claim fails exactly the 4 isolation tests.
- Audit `inputs_json` shows physical isolation: a tenant_a query on the canonical union reads only PostgreSQL.
- The MySQL listener's table has no timestamp columns at Trino 483 (order by `query_id`, which is time-prefixed).
- Open, recorded in ADR 0004: no authentication; unsalted SSN hash; mf runs as admin (BI stage must impersonate users); storage keys bypass Trino.
