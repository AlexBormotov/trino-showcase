select
    'clinic_c' as tenant_id, 'iceberg' as source_system, 'v1' as source_schema_version,
    id as encounter_id,
    patient_id,
    cast(start_ts as timestamp(6)) as start_ts,
    cast(end_ts as timestamp(6)) as end_ts,
    class as encounter_class,
    {{ strip_code_prefix('code') }} as encounter_code,
    description as encounter_description,
    cast(cost as decimal(14, 2)) as total_cost_amount
from {{ source('clinic_c', 'encounters') }}
