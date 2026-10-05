"""Metric values from MetricFlow (compiled from Ossie) vs independent expectations.

Expectations come from the seed manifest where it has the answer, otherwise from SQL
written directly over the canonical model, bypassing marts and MetricFlow.
Needs `dbt build` and `poe semantic` to have run.
"""

import csv
import json
import os
import subprocess
from pathlib import Path

import pytest
import trino

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((ROOT / "data" / "manifest.json").read_text())
EXPECTED = MANIFEST["expected"]
TENANTS = sorted(EXPECTED)


def mf(tmp_path: Path, metrics: list[str], group_by: str) -> dict[str, dict[str, float]]:
    """Run `mf query` and return {group value: {metric: value}}."""
    out = tmp_path / f"{'_'.join(metrics)}__{group_by}.csv"
    subprocess.run(
        ["mf", "query", "--metrics", ",".join(metrics), "--group-by", group_by, "--csv", str(out)],
        cwd=ROOT, check=True, capture_output=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    with out.open() as f:
        return {row[group_by]: {m: float(row[m]) for m in metrics} for row in csv.DictReader(f)}


@pytest.fixture(scope="module")
def sql():
    conn = trino.dbapi.connect(host="localhost", port=18080, user="admin", catalog="iceberg", schema="canonical")

    def run(query: str) -> dict:
        cur = conn.cursor()
        cur.execute(query)
        return {row[0]: float(row[1]) for row in cur.fetchall()}

    yield run
    conn.close()


@pytest.fixture(scope="module")
def by_tenant(tmp_path_factory):
    metrics = ["encounter_count", "active_patients", "avg_length_of_stay_days", "readmission_rate_30d"]
    return mf(tmp_path_factory.mktemp("mf"), metrics, "encounter__tenant_id")


def test_encounter_count_matches_manifest(by_tenant):
    assert {t: by_tenant[t]["encounter_count"] for t in TENANTS} == {t: EXPECTED[t]["encounters"] for t in TENANTS}


def test_claim_denial_rate_matches_manifest(tmp_path):
    got = mf(tmp_path, ["claim_denial_rate"], "claim__tenant_id")
    for t in TENANTS:
        status = EXPECTED[t]["claims_by_status"]
        assert got[t]["claim_denial_rate"] == pytest.approx(status["denied"] / (status["denied"] + status["paid"]))


def test_active_patients(by_tenant, sql):
    expected = sql("select tenant_id, count(distinct patient_id) from encounter group by 1")
    assert {t: by_tenant[t]["active_patients"] for t in TENANTS} == expected


def test_avg_length_of_stay(by_tenant, sql):
    expected = sql("""
        select tenant_id, avg(date_diff('second', start_ts, end_ts) / 86400.0)
        from encounter where encounter_class = 'inpatient' group by 1
    """)
    for t in TENANTS:
        assert by_tenant[t]["avg_length_of_stay_days"] == pytest.approx(expected[t], abs=1e-4)


def test_readmission_rate(by_tenant, sql):
    expected = sql("""
        with stays as (
            select tenant_id, patient_id, encounter_id, end_ts from encounter where encounter_class = 'inpatient'
        )
        select s.tenant_id, avg(case when exists (
            select 1 from encounter n
            where n.tenant_id = s.tenant_id and n.patient_id = s.patient_id
              and n.encounter_class = 'inpatient'
              and n.start_ts > s.end_ts and n.start_ts <= s.end_ts + interval '30' day
        ) then 1e0 else 0e0 end)  -- double: decimal literals would round avg() to one digit
        from stays s group by 1
    """)
    for t in TENANTS:
        assert by_tenant[t]["readmission_rate_30d"] == pytest.approx(expected[t])


def test_join_to_patient_dimension(tmp_path, sql):
    got = mf(tmp_path, ["encounter_count"], "patient__gender")
    expected = sql("""
        select p.gender, count(*) from encounter e
        join patient p on p.patient_hk = e.patient_hk and p.is_current group by 1
    """)
    assert {g: v["encounter_count"] for g, v in got.items()} == expected


def test_time_grain_adds_up(tmp_path):
    got = mf(tmp_path, ["encounter_count"], "metric_time__year")
    assert sum(v["encounter_count"] for v in got.values()) == sum(EXPECTED[t]["encounters"] for t in TENANTS)
