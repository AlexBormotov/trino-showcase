select
    'clinic_b' as tenant_id, 'mysql' as source_system, 'v1' as source_schema_version,
    claimid as claim_id,
    visitid as encounter_id,
    patientid as patient_id,
    servicedate as service_dt,
    {{ cents_to_amount('amount', 'servicedate', '2023-07-01') }} as claim_amount,
    case claimstatus when 'approved' then 'paid' when 'rejected' then 'denied' else claimstatus end as claim_status
from {{ source('clinic_b', 'claim') }}
