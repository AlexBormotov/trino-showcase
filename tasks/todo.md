# Stage 3: semantic layer (Ossie -> MetricFlow)

Goal: the five planned metrics defined once in Ossie, queryable with `mf query` on Trino, with values proven by independent checks. Scope: `docs/PLAN.md`; decision: ADR 0003.

- [x] 1. Spike: one metric (encounter_count) from Ossie through `ossie-to-msi` to `mf query` on Trino.
  Check: result equals the manifest expectation per tenant. Outcome: works with glue for four converter gaps (ADR 0003).
- [ ] 2. Row-level facts the metrics need, in dbt (`models/marts/`): length of stay for inpatient encounters, 30-day readmission flag (an inpatient admission within 30 days of an inpatient discharge of the same patient and tenant).
  Check: dbt tests; the readmission flag is cross-checked by a test query written differently (self-join, not window function).
- [ ] 3. Ossie model: datasets `encounter`, `claim`, `patient` (current), relationships; metrics `encounter_count`, `active_patients`, `avg_length_of_stay_days`, `readmission_rate_30d`, `claim_denial_rate`.
  Check: `poe semantic` has no converter issues; `mf list metrics` lists all five.
- [ ] 4. pytest: each metric per tenant through MetricFlow (Python API or CLI) equals an independent expectation: manifest (`encounter_count`, denial rate) or a hand-written SQL over the canonical model (the rest), plus one query by `metric_time__month`.
  Check: tests pass, plus a negative control.
- [ ] 5. Round trip: `msi-to-ossie` on the compiled manifest gives back the same metric names; record what is lost.
  Check: a test.
- [ ] 6. `docs/metrics.md` metric catalog (definition, grain, caveats such as claims including medication claims), CLAUDE.md, commit.

## Review

(filled in when the stage is done)
