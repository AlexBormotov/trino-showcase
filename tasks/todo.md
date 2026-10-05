# Stage 6: CI

Goal: every push proves, on a clean machine, that the whole stack comes up and every check passes. Scope: `docs/PLAN.md` (definition of done).

- [x] 1. GitHub Actions workflow: uv sync, unit tests, compose up (incl. Superset), Synthea with a small fixed population (jar cached), seed, `dbt build`, `poe semantic`, `poe superset`, all tests; compose logs as an artifact on failure. Actions pinned by commit SHA.
  Check: the run on GitHub is green.
- [x] 2. Status badge in README; CLAUDE.md; commit.
- [ ] 3. Make the repository public (decision Q20), after the user confirms.

## Review

- Green on GitHub in 7m17s: 19 unit, dbt 63 PASS / 2 WARN by design, 66 integration tests on a 300-patient population.
- First run failed at collection: integration modules read `data/manifest.json` at import; unit tests now run by path.
