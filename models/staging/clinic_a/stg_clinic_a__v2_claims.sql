select
    'clinic_a' as tenant_id, 'postgresql' as source_system, 'v2' as source_schema_version,
    claim_id,
    encounter_id,
    patient_id,
    service_date as service_dt,
    cast(amount as decimal(14, 2)) as claim_amount,
    lower(status) as claim_status
from {{ source('clinic_a_v2', 'claims') }}
