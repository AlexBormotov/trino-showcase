# Stage 1: sources and federation

Goal: three tenants with injected drift, all readable through Trino. Scope and decisions: `docs/PLAN.md`.

- [ ] 1. Docker resources: raise `.wslconfig` memory to 16GB, swap 4GB (needs `wsl --shutdown`, ask the user first).
  Check: `docker info --format '{{.MemTotal}}'` reports about 16 GB.
- [ ] 2. Python project: `pyproject.toml` (uv, Python 3.12, poethepoet tasks), pinned dbt-core 1.12.5, dbt-trino 1.10.6, dbt-metricflow[dbt-trino] 0.15.0.
  Check: `uv sync` and `uv run dbt --version` show the pinned versions.
- [ ] 3. `docker-compose.yml`: Trino 483 (host 18080), PostgreSQL (host 15432), MySQL, MinIO, Apache Polaris; healthchecks; memory limits.
  Check: `uv run poe up` and every service reports healthy.
- [ ] 4. Polaris bootstrap script: realm, principal, catalog backed by a MinIO bucket. Trino `iceberg` catalog over Polaris REST.
  Check: `CREATE SCHEMA iceberg.clinic_c` and a test table round-trip through Trino.
- [ ] 5. Synthea in an `eclipse-temurin:17` container: 2,000 patients, 5 years, seed 42, CSV export to `data/synthea/`.
  Check: CSVs present. Confirm the code system in `conditions.csv` is SNOMED CT; if not, revisit the diagnosis-code decision in `docs/PLAN.md`.
- [ ] 6. Seeder: split patients across tenants, reshape into each tenant's dialect, inject drift per `docs/PLAN.md`, write `data/manifest.json`.
  Check: unit tests on the reshaping functions.
- [ ] 7. Load tenants: PostgreSQL `clinic_a`, MySQL `clinic_b`, Iceberg `clinic_c` (written through Trino).
  Check: per-table row counts through Trino match `data/manifest.json`.
- [ ] 8. Federated smoke query: one `UNION ALL` of patient counts over the three catalogs; `EXPLAIN` shows the filters pushed down to PostgreSQL and MySQL.
  Check: a pytest runs the query and compares the counts with the manifest.
- [ ] 9. Update `CLAUDE.md` commands that now work; ADR 0001 on the catalog choice (Polaris REST vs JDBC vs Hive Metastore).

## Review

(filled in when the stage is done)
