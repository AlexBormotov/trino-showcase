---
title: .github/workflows/ci.yml
tags:
  - code-map
  - infra
---

# `.github/workflows/ci.yml`

Section: [[Testing]]

## Purpose

GitHub Actions: uv sync, unit tests, compose up, Synthea with 300 patients (jar cached), seed, dbt build, poe semantic, poe superset, integration tests; compose logs as artifact on failure; actions pinned by SHA.
