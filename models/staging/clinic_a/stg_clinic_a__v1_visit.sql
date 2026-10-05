select
    'clinic_a' as tenant_id, 'postgresql' as source_system, 'v1' as source_schema_version,
    visit_id as encounter_id,
    pat_id as patient_id,
    cast({{ parse_dmy_ts('visit_date') }} as timestamp(6)) as start_ts,
    cast({{ parse_dmy_ts('end_date') }} as timestamp(6)) as end_ts,
    visit_type as encounter_class,
    reason_code as encounter_code,
    reason_text as encounter_description,
    cast(cost as decimal(14, 2)) as total_cost_amount
from {{ source('clinic_a_v1', 'visit') }}
