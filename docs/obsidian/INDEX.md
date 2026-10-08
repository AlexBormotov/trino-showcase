---
title: Project Documentation Hub
tags:
  - index
---

# trino-showcase — documentation hub

Federated clinic data PoC: Trino reads three drifted tenant stores in place, dbt maps them to a canonical model as views, metrics are defined once in Apache Ossie and served through MetricFlow and Superset, and Trino enforces tenant isolation, PHI masking and audit. Open Graph View in Obsidian to see the whole structure. Vault layout and update hooks come from [obsidian-hooks](https://github.com/AlexBormotov/obsidian-hooks) (Apache-2.0).

## Sections

- [[Infrastructure]] — compose stack, Trino catalogs, Polaris, bootstrap, ports
- [[Data-Generation]] — Synthea, tenant drift, seed manifest
- [[dbt-Models]] — staging, canonical, marts, macros
- [[Semantic-Layer]] — Ossie model, MetricFlow compilation, metric facts
- [[Security]] — access rules, masks, read-only sources, audit
- [[BI]] — Superset generated from Ossie
- [[Testing]] — oracles, negative controls, CI
- [[Decisions]] — ADR summaries
- [[Planning]] — current stage and v2
- [[Timeline]] — log: what was done and when

## Code map

Every source file is described by its own note under `code-map/<area>/`, named after its repository path with `/` → `-` and no extension:

- `code-map/infra/` — compose, pyproject, dbt project and profile, CI, `infra/**` (except tenant DDL)
- `code-map/seed/` — `seed/*.py`, `infra/tenants/*.sql`
- `code-map/dbt/` — `models/**`, `macros/**`
- `code-map/semantic/` — `semantic/*`
- `code-map/tests/` — `tests/**`

Example: `models/canonical/patient.sql` → `code-map/dbt/models-canonical-patient.md`.

A file note contains: the file's purpose, its classes and their methods, functions or macros (signature + one-line description), the models it reads, and links to related notes via `[[wikilinks]]`.

> [!important] Before writing new code
> Check the code map: a similar function, macro or model may already exist. Adapt existing code instead of creating a duplicate.

## Conventions

- Note filenames in ASCII (latin letters, dashes, underscores); content in English, matching the repository
- Every section note links back to [[INDEX]]; code map notes link to their section
- New files, classes, functions and models are documented in the code map in the same session they are created
- Claude may create new sections when a topic doesn't fit existing ones — add the note and link it from [[INDEX]]
- [[Timeline]] gets a new entry after every working session (newest on top)
- Repository-level rules (CLAUDE.md, ADRs, docs/PLAN.md) stay the source of truth; this vault describes and links, it does not override them
