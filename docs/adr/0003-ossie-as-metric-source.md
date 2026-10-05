# ADR 0003: Apache Ossie as the source of metric definitions

- Status: accepted
- Date: 2026-10-05

## Context

Metrics must be defined once and served the same way to MetricFlow and to BI (`docs/PLAN.md`). The candidate source format is Apache Ossie, in the Apache Incubator since July 2026, with spec `0.2.0.dev0` on `main`. Its dbt converter (`apache-ossie-dbt`) is not on PyPI and produces a MetricFlow `semantic_manifest.json`, not dbt YAML. The plan required a spike before committing: Ossie YAML → `ossie-to-msi` → `mf query` on Trino, for one metric.

## Spike result

It works, with four gaps to close. The converter and spec were pinned at apache/ossie `bc839fb2` (2026-10-05).

`mf query --metrics encounter_count --group-by encounter__tenant_id` on Trino returned 47,075 / 44,576 / 44,794. That equals the clean-source expectation in the seed manifest. `mf` reads the converted `target/semantic_manifest.json` as is; `dbt parse` does not overwrite it.

| Gap | Effect | Resolution |
|---|---|---|
| The converter emits no time spine; Ossie has no such concept | `mf` refuses every query: "At least one time spine must be configured" | `metricflow_time_spine` dbt model. `semantic/compile.py` copies the spine config from `dbt parse` output into the converted manifest |
| The converter never sets `defaults.agg_time_dimension` | "Invalid aggregation time dimension configuration" for every metric | Each Ossie dataset declares it in `custom_extensions` (`vendor_name: DBT`, `{"agg_time_dimension": ...}`), and `compile.py` applies it. The definition stays in the Ossie file |
| `datatype: DateTime` does not make a field a time dimension in the converter, although the spec says `is_time` defaults to true | `start_ts` became categorical | Set `dimension: {is_time: true}` explicitly |
| The MetricFlow entity is named after the primary-key field | Group-by names like `encounter_hk__tenant_id` | Name the key field after the entity (`encounter`, expression `encounter_hk`) |

Two smaller ones: the converter README shows `model_dump_json()`, but the manifest object is pydantic-v1 style (`.json()`). And the CLI crashes on a Windows cp1251 console printing "→" unless `PYTHONIOENCODING=utf-8` is set; the `poe semantic` task sets it.

## Decision

- `semantic/clinic_analytics.yaml` (Ossie) is the only place metrics are defined.
- `uv run poe semantic` (`dbt parse` + `semantic/compile.py`) builds the MetricFlow manifest from it. The glue is limited to the gaps above. Every other part of a metric comes from the converter unchanged.
- apache/ossie stays pinned to a commit in `pyproject.toml`, as PEP 508 direct git references in `dependencies`. With name-only requirements, any installer other than uv would look up `apache-ossie` and `apache-ossie-dbt` on PyPI, where those names are unclaimed. Moving the pin means re-running the semantic tests and re-checking each gap in the table.

## Consequences

- The model is portable: the same file can feed other Ossie converters (Cube, Snowflake, and others in the repo) and the Superset generator planned for the BI stage.
- Ossie expressions are aggregates over row-level fields. Row-level business logic that needs window functions, such as a 30-day readmission flag, has to live in a dbt model. The metric in Ossie then aggregates that field.
- The four gaps are upstream issues worth reporting. Each fix upstream removes one piece of glue.
- The rule "MetricFlow is generated, never hand-edited" depends on `target/semantic_manifest.json` being rebuilt by `poe semantic` after every `dbt parse`, because `dbt parse` alone writes a manifest with no metrics.
