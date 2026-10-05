select
    'clinic_a' as tenant_id, 'postgresql' as source_system, 'v1' as source_schema_version,
    bill_id as claim_id,
    visit_id as encounter_id,
    pat_id as patient_id,
    {{ parse_dmy_date('bill_date') }} as service_dt,
    cast(amount as decimal(14, 2)) as claim_amount,
    case state when 'P' then 'paid' when 'D' then 'denied' when 'O' then 'pending' end as claim_status
from {{ source('clinic_a_v1', 'bill') }}
