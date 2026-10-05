"""Load built tenant tables into their stores. Every load drops and recreates."""

from pathlib import Path

import pandas as pd
import psycopg
import pyarrow as pa
import pymysql
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NoSuchTableError
from pyiceberg.transforms import MonthTransform

INFRA = Path(__file__).resolve().parent.parent / "infra" / "tenants"

PG = dict(host="localhost", port=15432, user="postgres", password="postgres", dbname="clinic_a")
MYSQL = dict(host="localhost", port=13306, user="root", password="mysql", database="clinic_b")
ICEBERG = {
    "type": "rest",
    "uri": "http://localhost:18181/api/catalog",
    "warehouse": "lake",
    "credential": "root:s3cr3t",
    "scope": "PRINCIPAL_ROLE:ALL",
    "s3.endpoint": "http://localhost:19000",
    "s3.access-key-id": "rustfsadmin",
    "s3.secret-access-key": "rustfsadmin",
    "s3.path-style-access": "true",
    "s3.region": "us-west-2",
}
ICEBERG_PARTITIONS = {"encounters": "start_ts"}  # table -> timestamp column partitioned by month


def records(df: pd.DataFrame) -> list[tuple]:
    """Rows as tuples of plain Python values, with NaN/NaT as None."""
    cols = []
    for name in df.columns:
        s = df[name]
        if pd.api.types.is_datetime64_any_dtype(s):
            cols.append([None if pd.isna(v) else v.to_pydatetime() for v in s])
        else:
            cols.append([None if (v is None or (isinstance(v, float) and v != v)) else v for v in s.tolist()])
    return list(zip(*cols))


def load_clinic_a(tables: dict[str, pd.DataFrame]) -> None:
    with psycopg.connect(**PG) as conn:
        conn.execute((INFRA / "clinic_a.sql").read_text())
        for name, df in tables.items():
            with conn.cursor().copy(f"COPY {name} ({', '.join(df.columns)}) FROM STDIN") as copy:
                for row in records(df):
                    copy.write_row(row)


def load_clinic_b(tables: dict[str, pd.DataFrame]) -> None:
    conn = pymysql.connect(**MYSQL, autocommit=True)
    try:
        with conn.cursor() as cur:
            for stmt in (INFRA / "clinic_b.sql").read_text().split(";"):
                body = "\n".join(l for l in stmt.splitlines() if not l.strip().startswith("--")).strip()
                if body:
                    cur.execute(body)
            for name, df in tables.items():
                sql = f"INSERT INTO {name} ({', '.join(df.columns)}) VALUES ({', '.join(['%s'] * len(df.columns))})"
                rows = records(df)
                for i in range(0, len(rows), 5000):
                    cur.executemany(sql, rows[i : i + 5000])
    finally:
        conn.close()


def load_clinic_c(tables: dict[str, pd.DataFrame]) -> None:
    catalog = load_catalog("lake", **ICEBERG)
    catalog.create_namespace_if_not_exists("clinic_c")
    for name, df in tables.items():
        ident = f"clinic_c.{name}"
        try:
            catalog.purge_table(ident)
        except NoSuchTableError:
            pass
        data = pa.Table.from_pandas(df, preserve_index=False)
        data = data.cast(pa.schema([
            pa.field(f.name, pa.timestamp("us")) if pa.types.is_timestamp(f.type) else f for f in data.schema
        ]))
        table = catalog.create_table(ident, schema=data.schema)
        if name in ICEBERG_PARTITIONS:
            col = ICEBERG_PARTITIONS[name]
            with table.update_spec() as spec:
                spec.add_field(col, MonthTransform(), f"{col}_month")
        table.append(data)
