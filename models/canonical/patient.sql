-- SCD2 on address. clinic_a replays its change log into versions; clinic_b and clinic_c
-- keep only the current state, so each of their patients has one open version.

with clinic_a_versions as (
    select
        patient_id,
        address,
        city,
        zip,
        changed_ts as valid_from_ts,
        lead(changed_ts) over (partition by patient_id order by lsn) as valid_to_ts
    from {{ ref('stg_clinic_a__v2_patient_cdc') }}
),

clinic_a as (
    select
        p.tenant_id, p.source_system, p.source_schema_version,
        p.patient_id, p.first_name, p.last_name, p.birth_dt, p.gender, p.ssn,
        v.address, v.city, v.zip, v.valid_from_ts, v.valid_to_ts
    from {{ ref('stg_clinic_a__v2_patients') }} as p
    join clinic_a_versions as v on v.patient_id = p.patient_id
),

snapshot_tenants as (
    select *, cast(null as timestamp(6)) as valid_to_ts from {{ ref('stg_clinic_b__patient') }}
    union all
    select *, cast(null as timestamp(6)) as valid_to_ts from {{ ref('stg_clinic_c__patients') }}
),

unioned as (
    select * from clinic_a
    union all
    select
        tenant_id, source_system, source_schema_version,
        patient_id, first_name, last_name, birth_dt, gender, ssn,
        address, city, zip, valid_from_ts, valid_to_ts
    from snapshot_tenants
)

select
    {{ hash_key(['tenant_id', 'patient_id']) }} as patient_hk,
    {{ hash_key(['tenant_id', 'patient_id', 'valid_from_ts']) }} as patient_version_hk,
    tenant_id,
    patient_id,
    first_name,
    last_name,
    birth_dt,
    gender,
    ssn,
    address,
    city,
    zip,
    valid_from_ts,
    valid_to_ts,
    valid_to_ts is null as is_current,
    source_system,
    source_schema_version
from unioned
