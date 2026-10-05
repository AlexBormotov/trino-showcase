"""The Ossie model survives Ossie -> MetricFlow -> Ossie, except for the losses listed here."""

from pathlib import Path

import pytest
import yaml
from metricflow_semantics.model.dbt_manifest_parser import parse_manifest_from_dbt_generated_manifest
from ossie import OssieDocument
from ossie_dbt import MSIToOssieConverter, OssieToMSIConverter

OSSIE = Path(__file__).resolve().parents[2] / "semantic" / "clinic_analytics.yaml"


def expressions(doc: dict) -> dict[str, str]:
    return {m["name"]: m["expression"]["dialects"][0]["expression"] for m in doc["metrics"]}


@pytest.fixture(scope="module")
def round_trip():
    source = yaml.safe_load(OSSIE.read_text())
    to_msi = OssieToMSIConverter().convert(OssieDocument.model_validate(source))
    manifest = parse_manifest_from_dbt_generated_manifest(to_msi.output.json())
    back = MSIToOssieConverter().convert(manifest, ossie_model_name=source["name"])
    return source, to_msi, back, yaml.safe_load(back.output.to_ossie_yaml())


def test_forward_conversion_has_no_issues(round_trip):
    _, to_msi, _, _ = round_trip
    assert to_msi.issues == []


def test_metric_expressions_survive_except_row_counts(round_trip):
    source, _, _, back = round_trip
    original, returned = expressions(source), expressions(back)
    assert returned.pop("encounter_count") == "SUM(1)"  # COUNT(encounter.*) loses its dataset
    original.pop("encounter_count")
    assert {k: v for k, v in returned.items() if k in original} == original


def test_known_losses_are_reported(round_trip):
    _, _, back, returned = round_trip
    assert [(i.issue_type.value, i.element_name) for i in back.issues] == [
        ("CONSTANT_METRIC_SEMANTIC_MODEL_LOSS", "encounter_count"),
    ]
    # Ratio metrics come back with their generated parts as separate metrics.
    assert "claim_denial_rate__numerator" in expressions(returned)
    assert [d["name"] for d in returned["datasets"]] == ["encounter", "claim", "patient"]
