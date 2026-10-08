---
title: tests/integration/test_security.py
tags:
  - code-map
  - tests
---

# `tests/integration/test_security.py`

Section: [[Testing]]

## Purpose

Per role: row filters, PHI masks, denied bypass via sources/staging/audit, unknown user, read-only sources, audit of finished and denied queries, new tables invisible until ruled.

## Contents

- `query(user: str, sql: str)` -> `list[tuple]` — test helper
- `denied(user: str, sql: str)` -> `bool` — test helper
- `test_tenant_analyst_sees_only_own_tenant(table)` — checks that tenant analyst sees only own tenant
- `test_tenant_analyst_counts_match_own_tenant()` — checks that tenant analyst counts match own tenant
- `test_cross_tenant_analyst_sees_all_tenants()` — checks that cross tenant analyst sees all tenants
- `test_phi_is_masked_for_analysts(user)` — checks that phi is masked for analysts
- `test_admin_sees_raw_values()` — checks that admin sees raw values
- `test_analysts_cannot_bypass_through_sources_staging_or_audit(user, sql)` — checks that analysts cannot bypass through sources staging or audit
- `test_unknown_user_is_denied()` — checks that unknown user is denied
- `test_tenant_filter_means_other_tenants_sources_are_never_read()` — checks that tenant filter means other tenants sources are never read
- `test_trino_cannot_write_to_sources()` — Even admin cannot write through Trino: it connects to sources as a read-only user.
- `audit_row(tag: str, timeout_s: float=15.0)` -> `tuple` — The audit record of the query whose text contains `tag` (the listener writes asynchronously).
- `test_completed_queries_are_audited_with_user()` — checks that completed queries are audited with user
- `test_denied_attempts_are_audited()` — checks that denied attempts are audited
- `test_new_tables_are_invisible_to_analysts_until_ruled()` — checks that new tables are invisible to analysts until ruled
