"""Access model enforced by Trino (infra/trino/rules.json) and the audit trail.

Roles: admin (everything), cross_tenant_analyst (all tenants, PHI masked),
tenant_a_analyst (clinic_a rows only, PHI masked); any other user is denied.
"""

import json
import re
import time
import uuid
from pathlib import Path

import pytest
import trino
from trino.exceptions import TrinoUserError

pytestmark = pytest.mark.integration

EXPECTED = json.loads((Path(__file__).resolve().parents[2] / "data" / "manifest.json").read_text())["expected"]


def query(user: str, sql: str) -> list[tuple]:
    conn = trino.dbapi.connect(host="localhost", port=18080, user=user)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        return cur.fetchall()
    finally:
        conn.close()


def denied(user: str, sql: str) -> bool:
    with pytest.raises(TrinoUserError) as err:
        query(user, sql)
    return err.value.error_name == "PERMISSION_DENIED"


# ---------------------------------------------------------------- row-level security


@pytest.mark.parametrize("table", ["canonical.encounter", "canonical.claim", "canonical.patient", "marts.fct_encounter"])
def test_tenant_analyst_sees_only_own_tenant(table):
    rows = query("tenant_a_analyst", f"SELECT DISTINCT tenant_id FROM iceberg.{table}")
    assert rows == [["clinic_a"]]


def test_tenant_analyst_counts_match_own_tenant():
    [[count]] = query("tenant_a_analyst", "SELECT count(*) FROM iceberg.canonical.encounter")
    assert count == EXPECTED["clinic_a"]["encounters"]


def test_cross_tenant_analyst_sees_all_tenants():
    rows = query("cross_tenant_analyst", "SELECT tenant_id, count(*) FROM iceberg.canonical.encounter GROUP BY 1")
    assert dict(rows) == {t: EXPECTED[t]["encounters"] for t in EXPECTED}


# ---------------------------------------------------------------- column masking


@pytest.mark.parametrize("user", ["tenant_a_analyst", "cross_tenant_analyst"])
def test_phi_is_masked_for_analysts(user):
    rows = query(user, """
        SELECT patient_id, first_name, last_name, ssn, address, birth_dt, zip
        FROM iceberg.canonical.patient LIMIT 200
    """)
    for patient_id, first, last, ssn, address, birth_dt, zip_code in rows:
        assert re.fullmatch(r"[0-9A-F]{64}", patient_id)
        assert first == last == address == "***"
        assert re.fullmatch(r"[0-9A-F]{64}", ssn)
        assert (birth_dt.month, birth_dt.day) == (1, 1)
        assert zip_code is None or re.fullmatch(r"\d{3}\*\*", zip_code)


def test_admin_sees_raw_values():
    [[first, ssn]] = query("admin", "SELECT first_name, ssn FROM iceberg.canonical.patient LIMIT 1")
    assert first != "***" and re.fullmatch(r"\d{3}-\d{2}-\d{4}", ssn)


# ---------------------------------------------------------------- no way around it


@pytest.mark.parametrize("sql", [
    "SELECT count(*) FROM pg_clinic_a.app_v2.patients",
    "SELECT count(*) FROM mysql_clinic_b.clinic_b.patient",
    "SELECT count(*) FROM iceberg.clinic_c.patients",
    "SELECT count(*) FROM iceberg.staging.stg_clinic_b__patient",
    "SELECT count(*) FROM audit.trino_audit.trino_queries",
])
@pytest.mark.parametrize("user", ["tenant_a_analyst", "cross_tenant_analyst"])
def test_analysts_cannot_bypass_through_sources_staging_or_audit(user, sql):
    assert denied(user, sql)


def test_unknown_user_is_denied():
    assert denied("someone_else", "SELECT count(*) FROM iceberg.canonical.encounter")


def test_tenant_filter_means_other_tenants_sources_are_never_read():
    tag = uuid.uuid4().hex
    query("tenant_a_analyst", f"SELECT count(*) FROM iceberg.canonical.encounter -- {tag}")
    inputs = json.loads(audit_row(tag)[1])
    assert {i["catalogName"] for i in inputs} == {"pg_clinic_a"}


def test_trino_cannot_write_to_sources():
    """Even admin cannot write through Trino: it connects to sources as a read-only user."""
    with pytest.raises(trino.exceptions.TrinoQueryError) as err:
        query("admin", "INSERT INTO pg_clinic_a.app_v2.claims VALUES ('x','x','x',DATE '2025-01-01',1,'PAID')")
    assert "permission denied" in str(err.value)


# ---------------------------------------------------------------- audit


def audit_row(tag: str, timeout_s: float = 15.0) -> tuple:
    """The audit record of the query whose text contains `tag` (the listener writes asynchronously)."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        rows = query("admin", f"""
            SELECT "user", inputs_json, query_state, error_code FROM audit.trino_audit.trino_queries
            WHERE query LIKE '%{tag}%' AND query NOT LIKE '%trino_queries%'
        """)
        if rows:
            return tuple(rows[0])
        time.sleep(0.5)
    raise AssertionError(f"no audit record for {tag}")


def test_completed_queries_are_audited_with_user():
    tag = uuid.uuid4().hex
    query("tenant_a_analyst", f"SELECT 1 AS probe FROM iceberg.canonical.encounter LIMIT 1 -- {tag}")
    user, _, state, _ = audit_row(tag)
    assert (user, state) == ("tenant_a_analyst", "FINISHED")


def test_denied_attempts_are_audited():
    tag = uuid.uuid4().hex
    denied("tenant_a_analyst", f"SELECT count(*) FROM pg_clinic_a.app_v2.patients -- {tag}")
    user, _, state, error = audit_row(tag)
    assert (user, state, error) == ("tenant_a_analyst", "FAILED", "PERMISSION_DENIED")


def test_new_tables_are_invisible_to_analysts_until_ruled():
    query("admin", "CREATE OR REPLACE VIEW iceberg.semantic.unruled_probe AS SELECT 'clinic_b' AS tenant_id")
    try:
        for user in ("tenant_a_analyst", "cross_tenant_analyst"):
            assert denied(user, "SELECT * FROM iceberg.semantic.unruled_probe")
    finally:
        query("admin", "DROP VIEW iceberg.semantic.unruled_probe")
