select
    'clinic_a' as tenant_id, 'postgresql' as source_system, 'v1' as source_schema_version,
    visit_id as encounter_id,
    pat_id as patient_id,
    {{ parse_dmy_date('dx_date') }} as onset_dt,
    snomed_code,
    dx_text as diagnosis_description
from {{ source('clinic_a_v1', 'dx') }}
