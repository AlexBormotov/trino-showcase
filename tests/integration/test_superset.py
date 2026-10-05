"""Superset serves the same metric values as MetricFlow, and Trino's rules apply per viewer.

Needs the superset service up and `python -m semantic.superset_sync` to have run.
"""

import json
import time
import uuid

import pytest
import trino

from semantic.superset_sync import SUPERSET, Superset
from tests.integration.test_metrics import mf

pytestmark = pytest.mark.integration

ENCOUNTER_METRICS = ["encounter_count", "active_patients", "avg_length_of_stay_days", "readmission_rate_30d"]


def login(user: str) -> Superset:
    return Superset(SUPERSET, user, user)


def dataset_id(client: Superset, table: str) -> int:
    return next(d["id"] for d in client.get("/api/v1/dataset/?q=(page_size:100)")["result"] if d["table_name"] == table)


def chart_data(client: Superset, table: str, metrics: list[str], columns: list[str], comment: str = "") -> list[dict]:
    body = {
        "datasource": {"id": dataset_id(client, table), "type": "table"},
        "force": True,
        "queries": [{"metrics": metrics, "columns": columns, "row_limit": 10000,
                     "extras": {"where": f"1 = 1 /* {comment} */" if comment else ""}}],
        "result_format": "json",
        "result_type": "full",
    }
    return client.call("POST", "/api/v1/chart/data", json=body)["result"][0]["data"]


@pytest.fixture(scope="module")
def admin():
    return login("admin")


def test_encounter_metrics_match_metricflow(admin, tmp_path):
    superset = {r["tenant_id"]: r for r in chart_data(admin, "fct_encounter", ENCOUNTER_METRICS, ["tenant_id"])}
    metricflow = mf(tmp_path, ENCOUNTER_METRICS, "encounter__tenant_id")
    assert superset.keys() == metricflow.keys()
    for tenant, values in metricflow.items():
        for metric, value in values.items():
            assert superset[tenant][metric] == pytest.approx(value, rel=1e-6), (tenant, metric)


def test_denial_rate_matches_metricflow(admin, tmp_path):
    superset = {r["tenant_id"]: r["claim_denial_rate"] for r in chart_data(admin, "fct_claim", ["claim_denial_rate"], ["tenant_id"])}
    metricflow = mf(tmp_path, ["claim_denial_rate"], "claim__tenant_id")
    assert superset == pytest.approx({t: v["claim_denial_rate"] for t, v in metricflow.items()}, rel=1e-6)


def test_every_dashboard_chart_returns_data(admin):
    charts = admin.get("/api/v1/chart/?q=(page_size:100)")["result"]
    assert len(charts) == 6
    for chart in charts:
        form = json.loads(admin.get(f"/api/v1/chart/{chart['id']}")["result"]["params"])
        metrics = form.get("metrics") or [form["metric"]]
        columns = [c for c in form.get("groupby", []) + [form.get("x_axis")] if c and c != "start_ts"]
        table = admin.get(f"/api/v1/dataset/{form['datasource'].split('__')[0]}")["result"]["table_name"]
        assert chart_data(admin, table, metrics, columns), chart["slice_name"]


def test_tenant_analyst_sees_only_own_tenant_in_superset(admin):
    own = chart_data(login("tenant_a_analyst"), "fct_encounter", ENCOUNTER_METRICS, ["tenant_id"])
    everyone = {r["tenant_id"]: r for r in chart_data(admin, "fct_encounter", ENCOUNTER_METRICS, ["tenant_id"])}
    assert [r["tenant_id"] for r in own] == ["clinic_a"]
    assert own[0] == everyone["clinic_a"]


def test_superset_queries_run_as_the_viewer():
    tag = uuid.uuid4().hex
    chart_data(login("tenant_a_analyst"), "fct_claim", ["claim_denial_rate"], [], comment=tag)
    conn = trino.dbapi.connect(host="localhost", port=18080, user="admin")
    cur = conn.cursor()
    for _ in range(30):
        cur.execute(f"SELECT DISTINCT \"user\" FROM audit.trino_audit.trino_queries "
                    f"WHERE query LIKE '%{tag}%' AND query NOT LIKE '%trino_queries%'")
        users = cur.fetchall()
        if users:
            break
        time.sleep(0.5)
    conn.close()
    assert users == [["tenant_a_analyst"]]
