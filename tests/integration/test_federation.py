"""Stage 1 checks against the running stack: data loaded as the manifest says, readable through Trino."""

import json
from pathlib import Path

import pytest
import trino

pytestmark = pytest.mark.integration

MANIFEST = json.loads((Path(__file__).resolve().parents[2] / "data" / "manifest.json").read_text())

# Manifest table name -> fully qualified Trino name.
TRINO_TABLES = {
    "clinic_a": lambda t: f"pg_clinic_a.{t}",
    "clinic_b": lambda t: f"mysql_clinic_b.clinic_b.{t.lower()}",
    "clinic_c": lambda t: f"iceberg.clinic_c.{t}",
}


@pytest.fixture(scope="module")
def query():
    conn = trino.dbapi.connect(host="localhost", port=18080, user="admin")

    def run(sql: str) -> list[tuple]:
        cur = conn.cursor()
        cur.execute(sql)
        return cur.fetchall()

    yield run
    conn.close()


@pytest.mark.parametrize(
    "tenant,table",
    [(tenant, table) for tenant, tables in MANIFEST["tables"].items() for table in tables],
)
def test_row_counts_match_manifest(query, tenant, table):
    [(count,)] = query(f"SELECT count(*) FROM {TRINO_TABLES[tenant](table)}")
    assert count == MANIFEST["tables"][tenant][table]


def test_federated_patient_count(query):
    [(total,)] = query("""
        SELECT sum(n) FROM (
            SELECT count(*) AS n FROM pg_clinic_a.app_v2.patients
            UNION ALL SELECT count(*) FROM mysql_clinic_b.clinic_b.patient
            UNION ALL SELECT count(*) FROM iceberg.clinic_c.patients
        ) AS t
    """)
    assert total == sum(src["patients"] for src in MANIFEST["source"].values())


@pytest.mark.parametrize("sql,remote", [
    ("SELECT count(*) FROM pg_clinic_a.app_v2.encounters WHERE started_at >= TIMESTAMP '2025-01-01'",
     'FROM "clinic_a"."app_v2"."encounters" WHERE "started_at" >= ?'),
    ("SELECT count(*) FROM mysql_clinic_b.clinic_b.visit WHERE isdeleted = 0",
     "FROM `clinic_b`.`Visit` WHERE `isDeleted` = ?"),
])
def test_filter_and_aggregate_push_down_to_relational_sources(query, sql, remote):
    plan = query(f"EXPLAIN {sql}")[0][0]
    assert "Query[SELECT count(*)" in plan and remote in plan


def test_archive_encounters_are_partitioned_by_month_with_gaps(query):
    months = {m for (m,) in query("""
        SELECT format_datetime(date_add('month', partition.start_ts_month, TIMESTAMP '1970-01-01'), 'yyyy-MM')
        FROM iceberg.clinic_c."encounters$partitions"
    """)}
    assert len(months) > 50
    assert not months & set(MANIFEST["injected"]["clinic_c"]["missing_months"])
