with unioned as (
    select * from {{ ref('stg_clinic_a__v1_dx') }}
    union all
    select * from {{ ref('stg_clinic_a__v2_diagnoses') }}
    union all
    select * from {{ ref('stg_clinic_b__visit_diagnosis') }}
    union all
    select * from {{ ref('stg_clinic_c__conditions') }}
)

select
    -- The description, not the code, identifies a diagnosis within an encounter: some archive rows have no code.
    {{ hash_key(['tenant_id', 'encounter_id', 'diagnosis_description']) }} as diagnosis_hk,
    {{ hash_key(['tenant_id', 'encounter_id']) }} as encounter_hk,
    {{ hash_key(['tenant_id', 'patient_id']) }} as patient_hk,
    tenant_id,
    encounter_id,
    patient_id,
    onset_dt,
    snomed_code,
    diagnosis_description,
    snomed_code is not null as is_coded,
    source_system,
    source_schema_version
from unioned
