select
    'clinic_c' as tenant_id, 'iceberg' as source_system, 'v1' as source_schema_version,
    id as claim_id,
    encounter_id,
    patient_id,
    service_date as service_dt,
    cast(amount as decimal(14, 2)) as claim_amount,
    outcome as claim_status
from {{ source('clinic_c', 'claims') }}
