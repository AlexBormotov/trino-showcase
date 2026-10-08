---
title: docker-compose.yml
tags:
  - code-map
  - infra
---

# `docker-compose.yml`

Section: [[Infrastructure]]

## Purpose

The local stack: PostgreSQL, MySQL, RustFS, Polaris (+ bootstrap and setup jobs), Trino, Superset. Health checks order the bootstrap; host ports shifted to 1xxxx and bound to 127.0.0.1; memory limits about 7.5 GB in total.
