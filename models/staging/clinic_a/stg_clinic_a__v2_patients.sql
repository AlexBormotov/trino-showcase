-- Current state; address history comes from stg_clinic_a__v2_patient_cdc.
select
    'clinic_a' as tenant_id, 'postgresql' as source_system, 'v2' as source_schema_version,
    patient_id,
    first_name,
    last_name,
    birth_date as birth_dt,
    {{ gender_code('gender') }} as gender,
    ssn
from {{ source('clinic_a_v2', 'patients') }}
