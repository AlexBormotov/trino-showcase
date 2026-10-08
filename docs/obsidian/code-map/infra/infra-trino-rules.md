---
title: infra/trino/rules.json
tags:
  - code-map
  - infra
---

# `infra/trino/rules.json`

Section: [[Security]]

## Purpose

Access rules: admin all; tenant_a_analyst and cross_tenant_analyst read-only on iceberg canonical/marts and the time spine; row filter tenant_id = 'clinic_a' for tenant_a; PHI masks; deny by default; first matching rule wins.
