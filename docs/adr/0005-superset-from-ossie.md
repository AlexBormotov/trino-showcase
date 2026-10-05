# ADR 0005: Superset as the BI layer, generated from Ossie

- Status: accepted
- Date: 2026-10-05

## Context

The BI layer must show the five metrics with the same values as MetricFlow, without anyone writing metric SQL by hand in BI (design review Q14). ADR 0004 adds a second requirement: BI must query Trino as the end user, so the row filters and PHI masks apply to whoever is looking at the dashboard.

## Decision

- **Superset 6.1.0** in compose, image extended with the Trino SQLAlchemy driver (`infra/superset/Dockerfile`). Metadata lives in SQLite on a volume. `infra/superset/bootstrap.sh` creates `admin`, `tenant_a_analyst` and `cross_tenant_analyst`.
- **`semantic/superset_sync.py` publishes the Ossie model through the Superset REST API**, matching objects by name so it can be rerun safely:
  - one Trino database connection with `impersonate_user`;
  - one dataset per Ossie dataset, with time columns and the default time column taken from Ossie;
  - each Ossie metric translated with sqlglot into a dataset metric. Qualifiers are dropped, because a Superset metric belongs to one dataset. Ratios become `CAST(num AS DOUBLE) / NULLIF(den, 0)`, because Trino divides integers as integers. A metric that spans two datasets is rejected. Number formats come from a `SUPERSET` custom extension on the Ossie metric;
  - six charts and the "Clinic analytics" dashboard. These are presentation only: they reference metrics by name and contain no metric SQL.
- **Authorization stays in Trino.** Superset gives analysts the broad `Alpha` role. What they actually see is decided by Trino, because every query runs as the logged-in user.

## Consequences

- One definition, three consumers: Ossie feeds MetricFlow (ADR 0003) and Superset. `tests/integration/test_superset.py` compares every metric per tenant between Superset's chart data API and `mf query`. If the Superset metrics are synced from a changed Ossie file while MetricFlow is not recompiled, the test fails (negative control).
- A test asserts impersonation from the audit log: a chart data request by `tenant_a_analyst` reaches Trino as `tenant_a_analyst`, and returns only `clinic_a` rows.
- Superset sees each dataset as one table, so the Ossie relationships (encounter → patient) do not appear in BI. A metric grouped by patient gender needs a virtual dataset or a wider mart. MetricFlow handles the joins itself.
- The translation covers the expression shapes this model uses: aggregates, `COUNT(DISTINCT ...)`, `COUNT(dataset.*)` and ratios. A new shape needs a unit test in `tests/unit/test_superset_sync.py`.
- Chart rendering in the browser is not covered by tests. The data endpoints are.
- Without authentication in Trino (ADR 0004), impersonation only means something because Superset itself authenticates its users. Anyone who can reach Trino directly can still claim any user name.
