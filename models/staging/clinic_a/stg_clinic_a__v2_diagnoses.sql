select
    'clinic_a' as tenant_id, 'postgresql' as source_system, 'v2' as source_schema_version,
    encounter_id,
    patient_id,
    diagnosed_on as onset_dt,
    code as snomed_code,
    description as diagnosis_description
from {{ source('clinic_a_v2', 'diagnoses') }}
