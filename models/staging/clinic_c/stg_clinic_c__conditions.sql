select
    'clinic_c' as tenant_id, 'iceberg' as source_system, 'v1' as source_schema_version,
    encounter_id,
    patient_id,
    recorded_date as onset_dt,
    {{ strip_code_prefix('code') }} as snomed_code,
    description as diagnosis_description
from {{ source('clinic_c', 'conditions') }}
