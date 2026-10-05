# Stage 1: sources and federation

Goal: three tenants with injected drift, all readable through Trino. Scope and decisions: `docs/PLAN.md`.

- [x] 1. Docker resources: raise `.wslconfig` memory to 16GB, swap 4GB (needs `wsl --shutdown`, ask the user first).
  Check: `docker info --format '{{.MemTotal}}'` reports about 16 GB.
- [x] 2. Python project: `pyproject.toml` (uv, Python 3.12, poethepoet tasks), pinned dbt-core 1.12.5, dbt-trino 1.10.6, dbt-metricflow[dbt-trino] 0.15.0.
  Check: `uv sync` and `uv run dbt --version` show the pinned versions.
- [x] 3. `docker-compose.yml`: Trino 483 (host 18080), PostgreSQL (host 15432), MySQL, RustFS (MinIO is archived), Apache Polaris; healthchecks; memory limits.
  Check: `uv run poe up` and every service reports healthy.
- [x] 4. Polaris bootstrap script: realm, principal, catalog backed by a RustFS bucket. Trino `iceberg` catalog over Polaris REST.
  Check: `CREATE SCHEMA iceberg.clinic_c` and a test table round-trip through Trino.
- [x] 5. Synthea in an `eclipse-temurin:17` container: 2,000 patients, 5 years, seed 42, CSV export to `data/synthea/`.
  Check: CSVs present. Confirm the code system in `conditions.csv` is SNOMED CT; if not, revisit the diagnosis-code decision in `docs/PLAN.md`.
- [x] 6. Seeder: split patients across tenants, reshape into each tenant's dialect, inject drift per `docs/PLAN.md`, write `data/manifest.json`.
  Check: unit tests on the reshaping functions.
- [x] 7. Load tenants: PostgreSQL `clinic_a`, MySQL `clinic_b`, Iceberg `clinic_c` (written through Trino).
  Check: per-table row counts through Trino match `data/manifest.json`.
- [x] 8. Federated smoke query: one `UNION ALL` of patient counts over the three catalogs; `EXPLAIN` shows the filters pushed down to PostgreSQL and MySQL.
  Check: a pytest runs the query and compares the counts with the manifest.
- [x] 9. Update `CLAUDE.md` commands that now work; ADR 0001 on the catalog choice (Polaris REST vs JDBC vs Hive Metastore).

## Review

- 30 tests pass (9 unit, 21 integration). Negative control: deleting one PostgreSQL row fails exactly the two dependent tests.
- Data: ~6,150 patients in the window, about 2,000 per tenant; claims outnumber encounters about 1.8 to 1 because Synthea bills medications separately on the same encounter.
- Synthea codes conditions in SNOMED-CT, so the plan's diagnosis-code decision stands.
- Deviations: MinIO -> RustFS (archived upstream); Polaris needed `drop-with-purge.enabled`; PyIceberg needs the `pyiceberg-core` extra for month partitioning; Trino's MySQL catalog needs `case-insensitive-name-matching`.
- Pushdown confirmed: filter + count(*) are sent whole to PostgreSQL and MySQL.
