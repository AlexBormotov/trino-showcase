# Stage 3: semantic layer (Ossie -> MetricFlow) (done)

Goal: the five planned metrics defined once in Ossie, queryable with `mf query` on Trino, with values proven by independent checks. Scope: `docs/PLAN.md`; decision: ADR 0003.

- [x] 1. Spike: one metric (encounter_count) from Ossie through `ossie-to-msi` to `mf query` on Trino.
  Check: result equals the manifest expectation per tenant. Outcome: works with glue for four converter gaps (ADR 0003).
- [x] 2. Row-level facts the metrics need, in dbt (`models/marts/`): length of stay for inpatient encounters, 30-day readmission flag (an inpatient admission within 30 days of an inpatient discharge of the same patient and tenant).
  Check: dbt tests; the readmission flag is cross-checked by a test query written differently (self-join, not window function).
- [x] 3. Ossie model: datasets `encounter`, `claim`, `patient` (current), relationships; metrics `encounter_count`, `active_patients`, `avg_length_of_stay_days`, `readmission_rate_30d`, `claim_denial_rate`.
  Check: `poe semantic` has no converter issues; `mf list metrics` lists all five.
- [x] 4. pytest: each metric per tenant through MetricFlow (Python API or CLI) equals an independent expectation: manifest (`encounter_count`, denial rate) or a hand-written SQL over the canonical model (the rest), plus one query by `metric_time__month`.
  Check: tests pass, plus a negative control.
- [x] 5. Round trip: `msi-to-ossie` on the compiled manifest gives back the same metric names; record what is lost.
  Check: a test.
- [x] 6. `docs/metrics.md` metric catalog (definition, grain, caveats such as claims including medication claims), CLAUDE.md, commit.

## Review

- Five metrics in Ossie, 11 in MetricFlow (ratios generate `__numerator`/`__denominator`). Queries by tenant, by `patient__gender` through relationships, and by `metric_time__year` work on Trino.
- Tests: 13 unit (incl. round trip), 7 metric integration tests. Negative control: counting pending claims in the denial denominator fails exactly `test_claim_denial_rate_matches_manifest`.
- Bugs caught by the cross-checks: `lead()` readmission missed 61 readmissions because 151 inpatient stays overlap (fixed: first admission after discharge); a test's decimal literals made Trino round `avg()` to 0.2 (fixed in the test).
- Round trip loses only the dataset of `COUNT(encounter.*)` (comes back as `SUM(1)`), reported by the converter.
