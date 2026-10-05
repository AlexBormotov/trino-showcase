"""Publish the Ossie model to Superset: database, datasets, metrics, charts, dashboard.

Metric SQL is translated from `semantic/clinic_analytics.yaml`, never written here.
Charts and the dashboard layout are presentation only. Idempotent: objects are
matched by name and updated in place.
"""

import json
import os
import sys
from pathlib import Path

import requests
import sqlglot
import yaml
from sqlglot import exp

ROOT = Path(__file__).resolve().parent.parent
OSSIE = ROOT / "semantic" / "clinic_analytics.yaml"
SUPERSET = os.environ.get("SUPERSET_URL", "http://localhost:18088")
DATABASE_NAME = "Trino"
# Superset connects as the logged-in user (impersonate_user), so Trino's rules apply per viewer.
TRINO_URI = "trino://admin@trino:8080/iceberg"
DASHBOARD = "Clinic analytics"


# ---------------------------------------------------------------- Ossie -> Superset SQL


def translate_metric(expression: str) -> tuple[str, str]:
    """Ossie metric expression -> (dataset name, Trino SQL over that dataset's table).

    Superset metrics belong to one dataset, so qualifiers are dropped. Ratios are cast
    to double (Trino divides integers as integers) and guarded with NULLIF.
    """
    tree = sqlglot.parse_one(expression)
    datasets = {c.table for c in tree.find_all(exp.Column) if c.table}
    if len(datasets) != 1:
        raise ValueError(f"metric must reference exactly one dataset: {expression}")
    for column in tree.find_all(exp.Column):
        column.set("table", None)

    def ratio(node: exp.Expression) -> exp.Expression:
        if isinstance(node, exp.Div):
            return exp.Div(
                this=exp.cast(node.this, "DOUBLE"),
                expression=exp.func("NULLIF", node.expression, exp.Literal.number(0)),
            )
        return node

    return datasets.pop(), tree.transform(ratio).sql(dialect="trino")


def extension(obj: dict, vendor: str) -> dict:
    for ext in obj.get("custom_extensions", []):
        if ext["vendor_name"] == vendor:
            return json.loads(ext["data"])
    return {}


def datasets_from_ossie(model: dict) -> dict[str, dict]:
    """{dataset name: {schema, table, time_columns, main_dttm_col, metrics: [...]}}."""
    out = {}
    for ds in model["datasets"]:
        _, schema, table = ds["source"].split(".")
        time_cols = [
            f["expression"]["dialects"][0]["expression"]
            for f in ds.get("fields", [])
            if f.get("dimension", {}).get("is_time")
        ]
        out[ds["name"]] = {
            "schema": schema,
            "table": table,
            "time_columns": time_cols,
            "main_dttm_col": extension(ds, "DBT").get("agg_time_dimension") or (time_cols[0] if time_cols else None),
            "metrics": [],
        }
    for m in model.get("metrics", []):
        dataset, sql = translate_metric(m["expression"]["dialects"][0]["expression"])
        out[dataset]["metrics"].append({
            "metric_name": m["name"],
            "verbose_name": m["name"].replace("_", " ").capitalize(),
            "expression": sql,
            "description": m.get("description"),
            "d3format": extension(m, "SUPERSET").get("d3format"),
        })
    return out


# ---------------------------------------------------------------- presentation

CHARTS = [
    # (slice name, dataset, form data without datasource); width is in 12ths of the row.
    ("Encounters", "encounter", {"viz_type": "big_number_total", "metric": "encounter_count"}, 3),
    ("Active patients", "encounter", {"viz_type": "big_number_total", "metric": "active_patients"}, 3),
    ("Claim denial rate by tenant", "claim",
     {"viz_type": "echarts_timeseries_bar", "x_axis": "tenant_id", "metrics": ["claim_denial_rate"], "groupby": []}, 6),
    ("Clinical KPIs by tenant", "encounter",
     {"viz_type": "table", "query_mode": "aggregate", "groupby": ["tenant_id"],
      "metrics": ["encounter_count", "active_patients", "avg_length_of_stay_days", "readmission_rate_30d"]}, 12),
    ("Encounters per month by tenant", "encounter",
     {"viz_type": "echarts_timeseries_line", "x_axis": "start_ts", "time_grain_sqla": "P1M",
      "metrics": ["encounter_count"], "groupby": ["tenant_id"]}, 8),
    ("Encounters by class", "encounter",
     {"viz_type": "pie", "groupby": ["encounter_class"], "metric": "encounter_count"}, 4),
]


def layout(charts: list[tuple[int, str, int]]) -> dict:
    """Dashboard v2 layout: charts fill rows of width 12 in the given order."""
    pos = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
        "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": DASHBOARD}},
    }
    row, used = None, 12
    for chart_id, name, width in charts:
        if used + width > 12:
            row = f"ROW-{len(pos['GRID_ID']['children']) + 1}"
            pos["GRID_ID"]["children"].append(row)
            pos[row] = {"type": "ROW", "id": row, "children": [], "parents": ["ROOT_ID", "GRID_ID"],
                        "meta": {"background": "BACKGROUND_TRANSPARENT"}}
            used = 0
        key = f"CHART-{chart_id}"
        pos[row]["children"].append(key)
        pos[key] = {"type": "CHART", "id": key, "children": [], "parents": ["ROOT_ID", "GRID_ID", row],
                    "meta": {"chartId": chart_id, "width": width, "height": 50, "sliceName": name}}
        used += width
    return pos


# ---------------------------------------------------------------- REST client


class Superset:
    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.s = requests.Session()
        token = self.s.post(f"{url}/api/v1/security/login",
                            json={"username": username, "password": password, "provider": "db"}).json()["access_token"]
        self.s.headers["Authorization"] = f"Bearer {token}"
        self.s.headers["Referer"] = url
        self.s.headers["X-CSRFToken"] = self.get("/api/v1/security/csrf_token/")["result"]

    def call(self, method: str, path: str, **kw) -> dict:
        r = self.s.request(method, f"{self.url}{path}", **kw)
        if not r.ok:
            raise RuntimeError(f"{method} {path}: {r.status_code} {r.text[:500]}")
        return r.json() if r.content else {}

    def get(self, path: str) -> dict:
        return self.call("GET", path)

    def find(self, resource: str, field: str, value: str) -> dict | None:
        rows = self.get(f"/api/v1/{resource}/?q=(page_size:100)")["result"]
        return next((r for r in rows if r.get(field) == value), None)


def sync(client: Superset) -> dict:
    model = yaml.safe_load(OSSIE.read_text())

    db = client.find("database", "database_name", DATABASE_NAME)
    db_body = {"database_name": DATABASE_NAME, "sqlalchemy_uri": TRINO_URI,
               "impersonate_user": True, "expose_in_sqllab": True}
    db_id = client.call("PUT", f"/api/v1/database/{db['id']}", json=db_body)["id"] if db else \
        client.call("POST", "/api/v1/database/", json=db_body)["id"]

    dataset_ids = {}
    for name, spec in datasets_from_ossie(model).items():
        existing = next((d for d in client.get("/api/v1/dataset/?q=(page_size:100)")["result"]
                         if d["table_name"] == spec["table"] and d["schema"] == spec["schema"]), None)
        ds_id = existing["id"] if existing else client.call(
            "POST", "/api/v1/dataset/", json={"database": db_id, "schema": spec["schema"], "table_name": spec["table"]})["id"]
        current = client.get(f"/api/v1/dataset/{ds_id}")["result"]
        metric_ids = {m["metric_name"]: m["id"] for m in current["metrics"]}
        client.call("PUT", f"/api/v1/dataset/{ds_id}", json={
            "main_dttm_col": spec["main_dttm_col"],
            "columns": [{"id": c["id"], "column_name": c["column_name"], "type": c["type"],
                         "is_dttm": c["column_name"] in spec["time_columns"]} for c in current["columns"]],
            # Exactly the Ossie metrics: anything else on the dataset is dropped.
            "metrics": [{**m, **({"id": metric_ids[m["metric_name"]]} if m["metric_name"] in metric_ids else {})}
                        for m in spec["metrics"]],
        })
        dataset_ids[name] = ds_id

    dash = client.find("dashboard", "dashboard_title", DASHBOARD)
    dash_id = dash["id"] if dash else client.call(
        "POST", "/api/v1/dashboard/", json={"dashboard_title": DASHBOARD, "slug": "clinic-analytics", "published": True})["id"]

    placed = []
    for slice_name, dataset, form, width in CHARTS:
        params = {**form, "datasource": f"{dataset_ids[dataset]}__table", "adhoc_filters": [], "row_limit": 10000}
        body = {"slice_name": slice_name, "viz_type": form["viz_type"], "datasource_id": dataset_ids[dataset],
                "datasource_type": "table", "params": json.dumps(params), "dashboards": [dash_id]}
        chart = client.find("chart", "slice_name", slice_name)
        chart_id = chart["id"] if chart else client.call("POST", "/api/v1/chart/", json=body)["id"]
        if chart:
            client.call("PUT", f"/api/v1/chart/{chart_id}", json=body)
        placed.append((chart_id, slice_name, width))

    client.call("PUT", f"/api/v1/dashboard/{dash_id}", json={
        "dashboard_title": DASHBOARD, "slug": "clinic-analytics", "published": True,
        "position_json": json.dumps(layout(placed))})
    return {"database": db_id, "datasets": dataset_ids, "dashboard": dash_id, "charts": [c[0] for c in placed]}


def main() -> int:
    result = sync(Superset(SUPERSET, "admin", os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin")))
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
