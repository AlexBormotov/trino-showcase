"""Canonical model vs the clean source recorded in the manifest (`expected`), per tenant.

Needs `dbt build` to have run against the current seed.
"""

import json
from decimal import Decimal
from pathlib import Path

import pytest
import trino

pytestmark = pytest.mark.integration

MANIFEST = json.loads((Path(__file__).resolve().parents[2] / "data" / "manifest.json").read_text())
EXPECTED = MANIFEST["expected"]
INJECTED = MANIFEST["injected"]
TENANTS = sorted(EXPECTED)


@pytest.fixture(scope="module")
def by_tenant():
    conn = trino.dbapi.connect(host="localhost", port=18080, user="admin", catalog="iceberg", schema="canonical")

    def run(sql: str) -> dict:
        """Run a query whose first column is tenant_id; return {tenant: rest of the row}."""
        cur = conn.cursor()
        cur.execute(sql)
        return {row[0]: row[1] if len(row) == 2 else tuple(row[1:]) for row in cur.fetchall()}

    yield run
    conn.close()


def close(a, b) -> bool:
    return abs(Decimal(str(a)) - Decimal(str(b))) <= Decimal("0.01")


def test_patients(by_tenant):
    got = by_tenant("select tenant_id, count(distinct patient_hk) from patient group by 1")
    assert got == {t: EXPECTED[t]["patients"] for t in TENANTS}


def test_gender_is_harmonized(by_tenant):
    got = by_tenant("select tenant_id || '/' || gender, count(*) from patient where is_current group by 1")
    assert got == {f"{t}/{g}": n for t in TENANTS for g, n in EXPECTED[t]["patients_by_gender"].items()}


def test_scd2_versions_come_from_the_change_log_only(by_tenant):
    got = by_tenant("select tenant_id, count(*) from patient group by 1")
    assert got["clinic_a"] == EXPECTED["clinic_a"]["patients"] + INJECTED["clinic_a"]["address_changes"]
    assert got["clinic_b"] == EXPECTED["clinic_b"]["patients"]
    assert got["clinic_c"] == EXPECTED["clinic_c"]["patients"]


def test_encounters_and_cost(by_tenant):
    got = by_tenant("select tenant_id, count(*), sum(total_cost_amount) from encounter group by 1")
    for t in TENANTS:
        count, cost = got[t]
        assert count == EXPECTED[t]["encounters"], t
        assert close(cost, EXPECTED[t]["encounter_cost_sum"]), (t, cost)


def test_diagnoses_and_coding(by_tenant):
    got = by_tenant("select tenant_id, count(*), count_if(is_coded) from diagnosis group by 1")
    for t in TENANTS:
        assert got[t] == (EXPECTED[t]["diagnoses"], EXPECTED[t]["coded_diagnoses"]), t


def test_claims_amount_and_status(by_tenant):
    got = by_tenant("select tenant_id, count(*), sum(claim_amount) from claim group by 1")
    status = by_tenant("select tenant_id || '/' || claim_status, count(*) from claim group by 1")
    for t in TENANTS:
        count, amount = got[t]
        assert count == EXPECTED[t]["claims"], t
        assert close(amount, EXPECTED[t]["claim_amount_sum"]), (t, amount)
        for s, n in EXPECTED[t]["claims_by_status"].items():
            assert status.get(f"{t}/{s}", 0) == n, (t, s)


def test_archive_gap_is_visible_as_orphans(by_tenant):
    claims = by_tenant("""
        select c.tenant_id, count(*) from claim c
        left join encounter e on e.encounter_hk = c.encounter_hk
        where e.encounter_hk is null group by 1
    """)
    diagnoses = by_tenant("""
        select d.tenant_id, count(*) from diagnosis d
        left join encounter e on e.encounter_hk = d.encounter_hk
        where e.encounter_hk is null group by 1
    """)
    assert claims == {"clinic_c": INJECTED["clinic_c"]["orphan_claims"]}
    assert diagnoses == {"clinic_c": INJECTED["clinic_c"]["orphan_conditions"]}


def test_tenant_filter_prunes_the_union_to_one_source():
    conn = trino.dbapi.connect(host="localhost", port=18080, user="admin")
    cur = conn.cursor()
    cur.execute("""EXPLAIN SELECT count(*) FROM iceberg.canonical.encounter
                   WHERE tenant_id = 'clinic_b' AND start_ts >= TIMESTAMP '2025-01-01'""")
    plan = cur.fetchall()[0][0]
    conn.close()
    assert "mysql_clinic_b:" in plan
    assert "pg_clinic_a" not in plan and "iceberg:clinic_c" not in plan
    # filter, soft-delete rule and count(*) all run inside MySQL
    assert "FROM `clinic_b`.`Visit` WHERE `isDeleted` = ? AND `visitStart` >= ?" in plan
