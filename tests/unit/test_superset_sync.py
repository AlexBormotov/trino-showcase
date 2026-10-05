from pathlib import Path

import pytest
import yaml

from semantic.superset_sync import datasets_from_ossie, layout, translate_metric

OSSIE = Path(__file__).resolve().parents[2] / "semantic" / "clinic_analytics.yaml"


@pytest.mark.parametrize("ossie,dataset,sql", [
    ("COUNT(encounter.*)", "encounter", "COUNT(*)"),
    ("COUNT(DISTINCT encounter.patient_hk)", "encounter", "COUNT(DISTINCT patient_hk)"),
    ("(SUM(claim.denied_claim)) / (SUM(claim.adjudicated_claim))", "claim",
     "CAST((SUM(denied_claim)) AS DOUBLE) / NULLIF((SUM(adjudicated_claim)), 0)"),
])
def test_translate_metric(ossie, dataset, sql):
    assert translate_metric(ossie) == (dataset, sql)


def test_cross_dataset_metric_is_rejected():
    with pytest.raises(ValueError):
        translate_metric("SUM(claim.amount) / COUNT(encounter.*)")


def test_every_ossie_metric_lands_on_its_dataset():
    model = yaml.safe_load(OSSIE.read_text())
    spec = datasets_from_ossie(model)
    names = {m["metric_name"] for d in spec.values() for m in d["metrics"]}
    assert names == {m["name"] for m in model["metrics"]}
    assert spec["encounter"]["main_dttm_col"] == "start_ts"
    assert spec["claim"]["time_columns"] == ["service_dt"]


def test_layout_wraps_rows_at_twelve():
    pos = layout([(1, "a", 6), (2, "b", 6), (3, "c", 8), (4, "d", 4), (5, "e", 3)])
    assert pos["GRID_ID"]["children"] == ["ROW-1", "ROW-2", "ROW-3"]
    assert pos["ROW-2"]["children"] == ["CHART-3", "CHART-4"]
