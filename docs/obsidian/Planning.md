---
title: Planning
tags:
  - planning
---

# Planning

Hub: [[INDEX]]

## Current stage

MVP complete (stages 1–6: sources, canonical model, semantic layer, security, Superset, CI). Repository public at https://github.com/AlexBormotov/trino-showcase. Stage task lists: `tasks/todo.md`, finished stages in `tasks/done/`.

## Next (v2)

- Metadata-driven mapping registry (`mappings/<tenant>.yml`) generating staging models; N tenant schemas from one template.
- Schema drift detection and profiling over `information_schema` of every catalog.
- `provider` as a canonical entity.
- Hardening: Trino authentication (TLS → password → OAuth2/SSO), OPA or Ranger instead of rules.json, keyed HMAC for PHI hashes, Polaris RBAC with credential vending.

Completed facts go to [[Timeline]].
