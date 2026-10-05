import numpy as np
import pandas as pd
import pytest

from seed import build as b


@pytest.fixture
def src() -> dict[str, pd.DataFrame]:
    """A small source in the shape read_synthea() returns."""
    patients = pd.DataFrame({
        "Id": ["p1", "p2", "p3"], "FIRST": ["A", "B", "C"], "LAST": ["X", "Y", "Z"],
        "BIRTHDATE": pd.to_datetime(["1980-01-01", "1990-06-15", "2000-12-31"]),
        "GENDER": ["M", "F", "M"], "SSN": ["999-00-0001", "999-00-0002", "999-00-0003"],
        "ADDRESS": ["1 Main", "2 Main", "3 Main"], "CITY": ["Boston"] * 3, "ZIP": ["02100"] * 3,
    })
    starts = pd.to_datetime([
        "2022-03-10 10:00", "2023-05-01 09:30", "2023-08-20 08:00",  # p1: before v2 / cents / missing months
        "2024-02-02 12:00", "2025-01-15 07:00",                      # p2: after v2 / units
        "2026-09-25 11:00",                                          # p3: recent, pending claim
    ])
    encounters = pd.DataFrame({
        "Id": [f"e{i}" for i in range(6)], "PATIENT": ["p1", "p1", "p1", "p2", "p2", "p3"],
        "START": starts, "STOP": starts + pd.Timedelta(hours=1),
        "ENCOUNTERCLASS": "ambulatory", "CODE": "185349003", "DESCRIPTION": "Encounter for check up",
        "TOTAL_CLAIM_COST": [100.25, 50.5, 10.0, 200.0, 75.75, 30.0],
    })
    conditions = pd.DataFrame({
        "START": starts.normalize(), "PATIENT": encounters["PATIENT"], "ENCOUNTER": encounters["Id"],
        "SYSTEM": "SNOMED-CT", "CODE": ["44054006", "38341003", "44054006", "38341003", "195662009", "44054006"],
        "DESCRIPTION": ["Diabetes", "Hypertension", "Diabetes", "Hypertension", "Pharyngitis", "Diabetes"],
    })
    claims = pd.DataFrame({
        "Id": [f"c{i}" for i in range(6)], "PATIENTID": encounters["PATIENT"], "APPOINTMENTID": encounters["Id"],
        "SERVICEDATE": starts, "TOTAL_CLAIM_COST": encounters["TOTAL_CLAIM_COST"],
    })
    return {"patients": patients, "encounters": encounters, "conditions": conditions, "claims": claims}


def rng() -> np.random.Generator:
    return np.random.default_rng(0)


def test_tenant_assignment_is_stable_and_uses_every_tenant():
    ids = [f"patient-{i}" for i in range(300)]
    assert [b.tenant_of(i) for i in ids] == [b.tenant_of(i) for i in ids]
    assert {b.tenant_of(i) for i in ids} == set(b.TENANTS)


def test_claim_status_marks_recent_claims_pending(src):
    status = b.claim_status(src["claims"], rng())
    assert status.iloc[-1] == "pending"
    assert set(status.iloc[:-1]) <= {"paid", "denied"}


def test_clinic_a_splits_by_schema_version(src):
    t = b.clinic_a(src, rng()).tables
    assert len(t["app_v1.visit"]) == 3 and len(t["app_v2.encounters"]) == 3
    assert t["app_v1.visit"]["visit_date"].iloc[0] == "10.03.2022 10:00:00"
    assert t["app_v1.dx"]["dx_date"].iloc[0] == "10.03.2022"
    assert set(t["app_v1.bill"]["state"]) <= {"P", "D", "O"}
    assert set(t["app_v2.claims"]["status"]) <= {"PAID", "DENIED", "PENDING"}


def test_clinic_a_legacy_gender_codes_only_for_patients_registered_before_v2(src):
    patients = b.clinic_a(src, rng()).tables["app_v2.patients"].set_index("patient_id")
    assert patients.loc["p1", "gender"] == "1"   # first seen 2022
    assert patients.loc["p2", "gender"] == "F"   # first seen 2024
    assert patients.loc["p3", "gender"] == "M"


def test_clinic_a_change_log_replays_to_current_address(src, monkeypatch):
    monkeypatch.setattr(b, "ADDRESS_CHANGE_RATE", 1.0)
    t = b.clinic_a(src, rng())
    log, current = t.tables["app_v2.patient_cdc"], t.tables["app_v2.patients"].set_index("patient_id")
    assert (log["op"] == "I").sum() == 3
    assert (log["op"] == "U").sum() == t.injected["address_changes"] == 3
    assert log["lsn"].is_monotonic_increasing
    last = log.sort_values("lsn").groupby("patient_id").last()
    assert (last["address"] == current.loc[last.index, "address"]).all()
    assert (last["changed_at"] == current.loc[last.index, "updated_at"]).all()


def test_clinic_b_money_is_in_cents_before_mid_2023(src):
    visits = b.clinic_b(src, rng()).tables["Visit"].set_index("visitId")
    assert visits.loc["e0", "totalCost"] == 10025   # 2022-03, cents
    assert visits.loc["e1", "totalCost"] == 5050    # 2023-05, cents
    assert visits.loc["e2", "totalCost"] == 10.0    # 2023-08, units


def test_clinic_b_soft_deleted_duplicates_and_code_dictionary(src, monkeypatch):
    monkeypatch.setattr(b, "SOFT_DELETED_DUPLICATE_RATE", 1.0)
    t = b.clinic_b(src, rng())
    visits = t.tables["Visit"]
    assert (visits["isDeleted"] == 1).sum() == t.injected["soft_deleted_duplicates"] == 6
    dictionary = t.tables["DxCode"].set_index("localCode")["snomedCode"]
    translated = t.tables["VisitDiagnosis"]["localCode"].map(dictionary)
    assert translated.tolist() == src["conditions"]["CODE"].tolist()


def test_clinic_c_drops_missing_months_but_keeps_their_claims(src):
    t = b.clinic_c(src, rng())
    months = t.tables["encounters"]["start_ts"].dt.strftime("%Y-%m")
    assert not months.isin(b.CLINIC_C_MISSING_MONTHS).any()
    assert t.injected["missing_encounters"] == 3      # 2022-03, 2023-08, 2025-01
    assert t.injected["orphan_claims"] == 3
    assert len(t.tables["claims"]) == 6


def test_clinic_c_codes_are_prefixed_or_missing(src, monkeypatch):
    monkeypatch.setattr(b, "TEXT_ONLY_DIAGNOSIS_RATE", 0.5)
    t = b.clinic_c(src, rng())
    codes = t.tables["conditions"]["code"]
    assert codes.isna().sum() == t.injected["text_only_diagnoses"]
    assert codes.dropna().str.startswith("SNOMED:").all()
    assert t.tables["conditions"]["description"].notna().all()


def test_expected_comes_from_the_clean_source(src):
    a, b_, c = b.clinic_a(src, rng()), b.clinic_b(src, rng()), b.clinic_c(src, rng())
    for tenant in (a, b_, c):
        exp = b.expected(src, tenant)
        assert exp["patients"] == 3 and exp["patients_by_gender"] == {"F": 1, "M": 2}
        assert exp["diagnoses"] == 6 and exp["claims"] == 6
        assert sum(exp["claims_by_status"].values()) == 6
        assert exp["claim_amount_sum"] == 466.5
    # cents in clinic_b and lost months in clinic_c must not leak into the expectation
    assert b.expected(src, b_)["encounter_cost_sum"] == 466.5
    assert b.expected(src, c)["encounters"] == 3
    assert b.expected(src, c)["encounter_cost_sum"] == 466.5 - 100.25 - 10.0 - 75.75
