# Stage 5: BI (Superset) on the Ossie metrics

Goal: a Superset dashboard whose metrics are generated from the Ossie model, showing the same numbers as MetricFlow, and respecting Trino's per-user rules. Scope: `docs/PLAN.md` (Q8, Q14); requirement from ADR 0004: BI must pass the end user's identity to Trino.

- [x] 1. Superset 6.1.0 image with the Trino driver; compose service (SQLite metadata, localhost port 18088); bootstrap creates admin and the two analyst users.
  Check: `/health` OK, login works.
- [x] 2. `semantic/superset_sync.py`: Trino database with user impersonation; one dataset per Ossie dataset; metrics translated from Ossie with sqlglot (qualifiers dropped, ratios as double with NULLIF); time columns marked. Idempotent.
  Check: unit tests on the expression translation; a second run changes nothing.
- [x] 3. Charts and a dashboard created by the same script.
  Check: dashboard opens, every chart returns data through the chart data API.
- [x] 4. pytest parity: each metric per tenant from the Superset chart data API equals `mf query`; logged in as `tenant_a_analyst`, Superset returns only clinic_a.
  Check: tests pass, plus a negative control.
- [x] 5. ADR 0005, README (how to open the dashboard, screenshots placeholders for the user), CLAUDE.md, commit.

## Review

- Superset 6.1.0 with the Trino driver; sync script publishes 3 datasets, 5 metrics (translated by sqlglot), 6 charts and the dashboard; a second run changes nothing.
- Tests: 6 unit (translation, layout), 5 integration: values equal `mf query` per tenant, every chart's query returns data, tenant_a sees only clinic_a, and the audit log shows Superset queries arriving as the viewer. Negative control: syncing a changed readmission denominator to Superset only fails the parity test.
- Not verified: chart rendering in a browser (Chrome automation did not log in and froze on screenshots). The user checks visually while taking README screenshots.
