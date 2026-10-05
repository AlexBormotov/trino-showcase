"""Compile the Ossie model into the manifest MetricFlow reads.

Ossie (`semantic/clinic_analytics.yaml`) is the only place metrics are defined.
Two gaps of the converter (apache/ossie at the pinned commit) are filled here:
- no time spine: it comes from `dbt parse` (model `metricflow_time_spine`);
- no default aggregation time dimension: each Ossie dataset declares it in a
  `custom_extensions` entry with vendor DBT, e.g. {"agg_time_dimension": "start_ts"}.

Run `dbt parse` first; it writes target/semantic_manifest.json, which this
script reads for the spine and then overwrites.
"""

import json
import sys
from pathlib import Path

import yaml
from ossie import OssieDocument
from ossie_dbt import OssieToMSIConverter

ROOT = Path(__file__).resolve().parent.parent
OSSIE = ROOT / "semantic" / "clinic_analytics.yaml"
MANIFEST = ROOT / "target" / "semantic_manifest.json"
SPINE_KEYS = ("time_spines", "time_spine_table_configurations")


def main() -> int:
    dbt_config = json.loads(MANIFEST.read_text())["project_configuration"]
    if not dbt_config["time_spines"]:
        print("no time spine in target/semantic_manifest.json; run `dbt parse` first", file=sys.stderr)
        return 1

    document = OssieDocument.model_validate(yaml.safe_load(OSSIE.read_text()))
    result = OssieToMSIConverter().convert(document)
    for issue in result.issues:
        print(f"[converter] {issue.issue_type.value}: {issue.element_name}", file=sys.stderr)

    # metricflow-semantic-interfaces models are pydantic v1 style: .json(), not .model_dump_json()
    manifest = json.loads(result.output.json(by_alias=True, exclude_none=True))
    for key in SPINE_KEYS:
        manifest["project_configuration"][key] = dbt_config[key]
    models = {m["name"]: m for m in manifest["semantic_models"]}
    for dataset in document.datasets:
        for ext in dataset.custom_extensions or []:
            if ext.vendor_name == "DBT" and "agg_time_dimension" in (data := json.loads(ext.data)):
                models[dataset.name]["defaults"] = {"agg_time_dimension": data["agg_time_dimension"]}
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    print(f"{len(manifest['semantic_models'])} semantic models, {len(manifest['metrics'])} metrics -> {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
