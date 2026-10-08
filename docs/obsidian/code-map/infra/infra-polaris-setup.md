---
title: infra/polaris/setup.sh
tags:
  - code-map
  - infra
---

# `infra/polaris/setup.sh`

Section: [[Infrastructure]]

## Purpose

Idempotent Polaris setup: gets a root token, creates catalog `lake` on s3://warehouse/lake (RustFS endpoints, drop-with-purge enabled), grants CATALOG_MANAGE_CONTENT to catalog_admin.
