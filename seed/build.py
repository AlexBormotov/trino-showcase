"""Reshape the Synthea export into three tenant dialects and inject drift.

Pure functions over pandas frames: no database access here. `build()` returns
the tenant tables plus a manifest of everything that was injected; tests use
the manifest as expected values.
"""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

WINDOW_START = pd.Timestamp("2021-10-01")
WINDOW_END = pd.Timestamp("2026-10-01")
CLINIC_A_V2_FROM = pd.Timestamp("2024-01-01")  # schema v1 before, v2 from this day
CLINIC_B_UNITS_FROM = pd.Timestamp("2023-07-01")  # money in cents before, currency units from
CLINIC_C_MISSING_MONTHS = ["2022-03", "2023-08", "2025-01"]
TENANTS = ("clinic_a", "clinic_b", "clinic_c")

DENIAL_RATE = 0.08
PENDING_DAYS = 14
ADDRESS_CHANGE_RATE = 0.15
SOFT_DELETED_DUPLICATE_RATE = 0.02
TEXT_ONLY_DIAGNOSIS_RATE = 0.05


@dataclass
class Tenant:
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    injected: dict[str, object] = field(default_factory=dict)


# ---------------------------------------------------------------- base frames


def read_synthea(csv_dir: Path) -> dict[str, pd.DataFrame]:
    """Synthea CSVs, cut to the 5-year window, with typed columns."""
    enc = pd.read_csv(csv_dir / "encounters.csv", dtype=str)
    enc["START"] = _utc_naive(enc["START"])
    enc["STOP"] = _utc_naive(enc["STOP"])
    enc = enc[(enc["START"] >= WINDOW_START) & (enc["START"] < WINDOW_END)]
    enc["TOTAL_CLAIM_COST"] = enc["TOTAL_CLAIM_COST"].astype(float).round(2)

    pat = pd.read_csv(csv_dir / "patients.csv", dtype=str)
    pat = pat[pat["Id"].isin(enc["PATIENT"])].copy()
    pat["BIRTHDATE"] = pd.to_datetime(pat["BIRTHDATE"])

    cond = pd.read_csv(csv_dir / "conditions.csv", dtype=str)
    cond = cond[cond["ENCOUNTER"].isin(enc["Id"])].copy()
    cond["START"] = pd.to_datetime(cond["START"])

    claims = pd.read_csv(csv_dir / "claims.csv", dtype=str, usecols=["Id", "PATIENTID", "APPOINTMENTID", "SERVICEDATE"])
    claims = claims[claims["APPOINTMENTID"].isin(enc["Id"])].copy()
    claims["SERVICEDATE"] = _utc_naive(claims["SERVICEDATE"])
    claims = claims.merge(enc[["Id", "TOTAL_CLAIM_COST"]].rename(columns={"Id": "APPOINTMENTID"}), on="APPOINTMENTID")
    return {"patients": pat, "encounters": enc, "conditions": cond, "claims": claims}


def tenant_of(patient_id: str) -> str:
    """Stable assignment of a patient to a tenant."""
    return TENANTS[int(hashlib.md5(patient_id.encode()).hexdigest(), 16) % len(TENANTS)]


def split(base: dict[str, pd.DataFrame]) -> dict[str, dict[str, pd.DataFrame]]:
    owner = {pid: tenant_of(pid) for pid in base["patients"]["Id"]}
    keys = {"patients": "Id", "encounters": "PATIENT", "conditions": "PATIENT", "claims": "PATIENTID"}
    return {
        t: {name: df[df[keys[name]].map(owner) == t].reset_index(drop=True) for name, df in base.items()}
        for t in TENANTS
    }


def claim_status(claims: pd.DataFrame, rng: np.random.Generator) -> pd.Series:
    """Synthea closes every claim; inject denials and recent pending claims."""
    status = np.where(rng.random(len(claims)) < DENIAL_RATE, "denied", "paid")
    pending = claims["SERVICEDATE"] >= WINDOW_END - pd.Timedelta(days=PENDING_DAYS)
    return pd.Series(np.where(pending, "pending", status), index=claims.index)


def address_changes(pat: pd.DataFrame, first_seen: pd.Series, rng: np.random.Generator) -> pd.DataFrame:
    """One address move for a share of patients, at a random time after first contact."""
    movers = pat[rng.random(len(pat)) < ADDRESS_CHANGE_RATE]
    seen = first_seen.loc[movers["Id"]].to_numpy()
    span = (WINDOW_END - pd.Series(seen)).dt.total_seconds().to_numpy()
    moved_at = pd.Series(seen) + pd.to_timedelta(rng.random(len(movers)) * span, unit="s")
    return pd.DataFrame({
        "patient_id": movers["Id"].to_numpy(),
        "changed_at": moved_at.dt.floor("s").to_numpy(),
        "address": [f"{rng.integers(1, 999)} Relocation Way" for _ in range(len(movers))],
        "city": movers["CITY"].to_numpy(),
        "zip": movers["ZIP"].to_numpy(),
    })


# ---------------------------------------------------------------- clinic_a


def clinic_a(src: dict[str, pd.DataFrame], rng: np.random.Generator) -> Tenant:
    """PostgreSQL. Schema app_v1 until 2023, app_v2 after; patients only in v2."""
    t = Tenant()
    enc, cond, claims = src["encounters"], src["conditions"], src["claims"]
    status = claim_status(claims, rng)
    first_seen = enc.groupby("PATIENT")["START"].min()

    pat = src["patients"]
    registered = first_seen.loc[pat["Id"]].to_numpy()
    legacy = registered < CLINIC_A_V2_FROM
    gender = np.where(legacy, pat["GENDER"].map({"M": "1", "F": "2"}), pat["GENDER"])
    moves = address_changes(pat, first_seen, rng)
    address = pat.set_index("Id")["ADDRESS"].copy()
    address.loc[moves["patient_id"]] = moves["address"].to_numpy()
    updated = pd.Series(registered, index=pat["Id"].to_numpy()).dt.floor("s")
    updated.loc[moves["patient_id"]] = moves["changed_at"].to_numpy()

    t.tables["app_v2.patients"] = pd.DataFrame({
        "patient_id": pat["Id"], "first_name": pat["FIRST"], "last_name": pat["LAST"],
        "birth_date": pat["BIRTHDATE"].dt.date, "gender": gender, "ssn": pat["SSN"],
        "address": address.loc[pat["Id"]].to_numpy(), "city": pat["CITY"], "zip": pat["ZIP"],
        "updated_at": updated.loc[pat["Id"]].to_numpy(),
    })
    inserts = pd.DataFrame({
        "op": "I", "changed_at": pd.Series(registered).dt.floor("s"), "patient_id": pat["Id"].to_numpy(),
        "address": pat["ADDRESS"].to_numpy(), "city": pat["CITY"].to_numpy(), "zip": pat["ZIP"].to_numpy(),
    })
    log = pd.concat([inserts, moves.assign(op="U")], ignore_index=True).sort_values(["changed_at", "patient_id"])
    log.insert(0, "lsn", np.arange(1, len(log) + 1))
    t.tables["app_v2.patient_cdc"] = log[["lsn", "op", "changed_at", "patient_id", "address", "city", "zip"]]

    v1 = enc["START"] < CLINIC_A_V2_FROM
    dmy = "%d.%m.%Y %H:%M:%S"
    t.tables["app_v1.visit"] = pd.DataFrame({
        "visit_id": enc.loc[v1, "Id"], "pat_id": enc.loc[v1, "PATIENT"],
        "visit_date": enc.loc[v1, "START"].dt.strftime(dmy), "end_date": enc.loc[v1, "STOP"].dt.strftime(dmy),
        "visit_type": enc.loc[v1, "ENCOUNTERCLASS"], "reason_code": enc.loc[v1, "CODE"],
        "reason_text": enc.loc[v1, "DESCRIPTION"], "cost": enc.loc[v1, "TOTAL_CLAIM_COST"],
    })
    t.tables["app_v2.encounters"] = pd.DataFrame({
        "encounter_id": enc.loc[~v1, "Id"], "patient_id": enc.loc[~v1, "PATIENT"],
        "started_at": enc.loc[~v1, "START"], "ended_at": enc.loc[~v1, "STOP"],
        "encounter_class": enc.loc[~v1, "ENCOUNTERCLASS"], "snomed_code": enc.loc[~v1, "CODE"],
        "description": enc.loc[~v1, "DESCRIPTION"], "total_cost": enc.loc[~v1, "TOTAL_CLAIM_COST"],
    })

    cv1 = cond["ENCOUNTER"].isin(enc.loc[v1, "Id"])
    t.tables["app_v1.dx"] = pd.DataFrame({
        "pat_id": cond.loc[cv1, "PATIENT"], "visit_id": cond.loc[cv1, "ENCOUNTER"],
        "dx_date": cond.loc[cv1, "START"].dt.strftime("%d.%m.%Y"), "snomed_code": cond.loc[cv1, "CODE"],
        "dx_text": cond.loc[cv1, "DESCRIPTION"],
    })
    t.tables["app_v2.diagnoses"] = pd.DataFrame({
        "encounter_id": cond.loc[~cv1, "ENCOUNTER"], "patient_id": cond.loc[~cv1, "PATIENT"],
        "diagnosed_on": cond.loc[~cv1, "START"].dt.date, "code": cond.loc[~cv1, "CODE"],
        "description": cond.loc[~cv1, "DESCRIPTION"],
    })

    lv1 = claims["APPOINTMENTID"].isin(enc.loc[v1, "Id"])
    t.tables["app_v1.bill"] = pd.DataFrame({
        "bill_id": claims.loc[lv1, "Id"], "visit_id": claims.loc[lv1, "APPOINTMENTID"], "pat_id": claims.loc[lv1, "PATIENTID"],
        "bill_date": claims.loc[lv1, "SERVICEDATE"].dt.strftime("%d.%m.%Y"), "amount": claims.loc[lv1, "TOTAL_CLAIM_COST"],
        "state": status[lv1].map({"paid": "P", "denied": "D", "pending": "O"}),
    })
    t.tables["app_v2.claims"] = pd.DataFrame({
        "claim_id": claims.loc[~lv1, "Id"], "encounter_id": claims.loc[~lv1, "APPOINTMENTID"],
        "patient_id": claims.loc[~lv1, "PATIENTID"], "service_date": claims.loc[~lv1, "SERVICEDATE"].dt.date,
        "amount": claims.loc[~lv1, "TOTAL_CLAIM_COST"], "status": status[~lv1].str.upper(),
    })

    t.injected = {
        "legacy_gender_codes": int(legacy.sum()),
        "address_changes": len(moves),
        "denied_claims": int((status == "denied").sum()),
        "pending_claims": int((status == "pending").sum()),
    }
    return t


# ---------------------------------------------------------------- clinic_b


def clinic_b(src: dict[str, pd.DataFrame], rng: np.random.Generator) -> Tenant:
    """MySQL. camelCase, soft-deleted duplicates, cents before mid-2023, local codes."""
    t = Tenant()
    enc, cond, claims, pat = src["encounters"], src["conditions"], src["claims"], src["patients"]
    status = claim_status(claims, rng)
    first_seen = enc.groupby("PATIENT")["START"].min()

    t.tables["Patient"] = pd.DataFrame({
        "patientId": pat["Id"], "firstName": pat["FIRST"], "lastName": pat["LAST"],
        "dob": pat["BIRTHDATE"].dt.date, "sex": pat["GENDER"].map({"M": "male", "F": "female"}),
        "ssn": pat["SSN"], "street": pat["ADDRESS"], "city": pat["CITY"], "postalCode": pat["ZIP"],
        "createdAt": first_seen.loc[pat["Id"]].dt.floor("s").to_numpy(),
        "updatedAt": first_seen.loc[pat["Id"]].dt.floor("s").to_numpy(),
    })

    def money(amount: pd.Series, when: pd.Series) -> pd.Series:
        return np.where(when < CLINIC_B_UNITS_FROM, (amount * 100).round(), amount)

    visits = pd.DataFrame({
        "visitId": enc["Id"], "patientId": enc["PATIENT"], "visitStart": enc["START"], "visitEnd": enc["STOP"],
        "visitKind": enc["ENCOUNTERCLASS"], "procCode": enc["CODE"], "procName": enc["DESCRIPTION"],
        "totalCost": money(enc["TOTAL_CLAIM_COST"], enc["START"]), "isDeleted": 0,
    })
    dupes = visits[rng.random(len(visits)) < SOFT_DELETED_DUPLICATE_RATE].copy()
    dupes["visitId"] = [f"dup-{i:06d}" for i in range(len(dupes))]
    dupes["isDeleted"] = 1
    t.tables["Visit"] = pd.concat([visits, dupes], ignore_index=True)

    codes = cond[["CODE", "DESCRIPTION"]].drop_duplicates("CODE").sort_values("CODE").reset_index(drop=True)
    codes["localCode"] = [f"B{i:05d}" for i in range(1, len(codes) + 1)]
    t.tables["DxCode"] = pd.DataFrame({"localCode": codes["localCode"], "snomedCode": codes["CODE"], "label": codes["DESCRIPTION"]})
    t.tables["VisitDiagnosis"] = pd.DataFrame({
        "visitId": cond["ENCOUNTER"], "patientId": cond["PATIENT"], "diagDate": cond["START"].dt.date,
        "localCode": cond["CODE"].map(dict(zip(codes["CODE"], codes["localCode"]))),
    })

    t.tables["Claim"] = pd.DataFrame({
        "claimId": claims["Id"], "visitId": claims["APPOINTMENTID"], "patientId": claims["PATIENTID"],
        "serviceDate": claims["SERVICEDATE"].dt.date,
        "amount": money(claims["TOTAL_CLAIM_COST"], claims["SERVICEDATE"]),
        "claimStatus": status.map({"paid": "approved", "denied": "rejected", "pending": "pending"}),
    })

    t.injected = {
        "soft_deleted_duplicates": len(dupes),
        "cents_rows_visit": int((enc["START"] < CLINIC_B_UNITS_FROM).sum()),
        "local_codes": len(codes),
        "denied_claims": int((status == "denied").sum()),
        "pending_claims": int((status == "pending").sum()),
    }
    return t


# ---------------------------------------------------------------- clinic_c


def clinic_c(src: dict[str, pd.DataFrame], rng: np.random.Generator) -> Tenant:
    """Iceberg archive. Missing months of encounters; prefixed or missing codes."""
    t = Tenant()
    enc, cond, claims, pat = src["encounters"], src["conditions"], src["claims"], src["patients"]
    status = claim_status(claims, rng)

    t.tables["patients"] = pd.DataFrame({
        "id": pat["Id"], "given_name": pat["FIRST"], "family_name": pat["LAST"],
        "birth_date": pat["BIRTHDATE"].dt.date, "gender": pat["GENDER"], "ssn": pat["SSN"],
        "address": pat["ADDRESS"], "city": pat["CITY"], "zip": pat["ZIP"],
    })

    missing = enc["START"].dt.strftime("%Y-%m").isin(CLINIC_C_MISSING_MONTHS)
    kept = enc[~missing]
    t.tables["encounters"] = pd.DataFrame({
        "id": kept["Id"], "patient_id": kept["PATIENT"], "start_ts": kept["START"], "end_ts": kept["STOP"],
        "class": kept["ENCOUNTERCLASS"], "code": "SNOMED:" + kept["CODE"], "description": kept["DESCRIPTION"],
        "cost": kept["TOTAL_CLAIM_COST"],
    })

    text_only = rng.random(len(cond)) < TEXT_ONLY_DIAGNOSIS_RATE
    t.tables["conditions"] = pd.DataFrame({
        "patient_id": cond["PATIENT"], "encounter_id": cond["ENCOUNTER"], "recorded_date": cond["START"].dt.date,
        "code": np.where(text_only, None, "SNOMED:" + cond["CODE"]), "description": cond["DESCRIPTION"],
    })

    t.tables["claims"] = pd.DataFrame({
        "id": claims["Id"], "encounter_id": claims["APPOINTMENTID"], "patient_id": claims["PATIENTID"],
        "service_date": claims["SERVICEDATE"].dt.date, "amount": claims["TOTAL_CLAIM_COST"], "outcome": status,
    })

    orphans = ~claims["APPOINTMENTID"].isin(kept["Id"])
    t.injected = {
        "missing_months": CLINIC_C_MISSING_MONTHS,
        "missing_encounters": int(missing.sum()),
        "orphan_claims": int(orphans.sum()),
        "orphan_conditions": int((~cond["ENCOUNTER"].isin(kept["Id"])).sum()),
        "text_only_diagnoses": int(text_only.sum()),
        "denied_claims": int((status == "denied").sum()),
        "pending_claims": int((status == "pending").sum()),
    }
    return t


# ---------------------------------------------------------------- entry point


def build(csv_dir: Path, seed: int = 42) -> tuple[dict[str, Tenant], dict]:
    parts = split(read_synthea(csv_dir))
    builders = {"clinic_a": clinic_a, "clinic_b": clinic_b, "clinic_c": clinic_c}
    tenants = {name: fn(parts[name], np.random.default_rng([seed, i])) for i, (name, fn) in enumerate(builders.items())}
    manifest = {
        "window": [str(WINDOW_START.date()), str(WINDOW_END.date())],
        "source": {name: {k: len(v) for k, v in parts[name].items()} for name in TENANTS},
        "tables": {name: {k: len(v) for k, v in t.tables.items()} for name, t in tenants.items()},
        "injected": {name: t.injected for name, t in tenants.items()},
    }
    return tenants, manifest


def _utc_naive(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, utc=True).dt.tz_localize(None)
