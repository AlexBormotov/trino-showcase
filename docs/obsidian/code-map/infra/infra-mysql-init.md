---
title: infra/mysql/init.sql
tags:
  - code-map
  - infra
---

# `infra/mysql/init.sql`

Section: [[Security]]

## Purpose

First-start init of MySQL: read-only user trino_reader on clinic_b; database trino_audit with writer trino_audit and reader audit_reader.
