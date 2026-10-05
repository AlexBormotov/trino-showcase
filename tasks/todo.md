# Stage 6: CI

Goal: every push proves, on a clean machine, that the whole stack comes up and every check passes. Scope: `docs/PLAN.md` (definition of done).

- [ ] 1. GitHub Actions workflow: uv sync, unit tests, compose up (incl. Superset), Synthea with a small fixed population (jar cached), seed, `dbt build`, `poe semantic`, `poe superset`, all tests; compose logs as an artifact on failure. Actions pinned by commit SHA.
  Check: the run on GitHub is green.
- [ ] 2. Status badge in README; CLAUDE.md; commit.
- [ ] 3. Make the repository public (decision Q20), after the user confirms.

## Review

(filled in when the stage is done)
