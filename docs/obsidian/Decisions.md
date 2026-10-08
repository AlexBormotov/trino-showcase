---
title: Decisions
tags:
  - adr
  - decisions
---

# Decisions

Hub: [[INDEX]]

Architecture decision records live in the repository at `docs/adr/` (outside this vault).

- ADR 0001 — Iceberg catalog and object storage: Polaris REST over JDBC/Hive; RustFS instead of archived MinIO. → [[Infrastructure]]
- ADR 0002 — Canonical model as federated views: two layers, hash keys, SCD2 replay, orphans as warn, pushdown trade-offs. → [[dbt-Models]]
- ADR 0003 — Ossie as the metric source: spike result and converter gaps. → [[Semantic-Layer]]
- ADR 0004 — Tenant isolation, PHI masking and audit; known gaps and path to OPA/Ranger/Starburst. → [[Security]]
- ADR 0005 — Superset generated from Ossie, impersonation. → [[BI]]

Scope and the design review outcome: `docs/PLAN.md`. Production evolution (Starburst, AWS Lake Formation): `README.md`.
