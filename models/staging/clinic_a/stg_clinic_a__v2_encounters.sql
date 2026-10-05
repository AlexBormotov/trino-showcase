select
    'clinic_a' as tenant_id, 'postgresql' as source_system, 'v2' as source_schema_version,
    encounter_id,
    patient_id,
    cast(started_at as timestamp(6)) as start_ts,
    cast(ended_at as timestamp(6)) as end_ts,
    encounter_class,
    snomed_code as encounter_code,
    description as encounter_description,
    cast(total_cost as decimal(14, 2)) as total_cost_amount
from {{ source('clinic_a_v2', 'encounters') }}
