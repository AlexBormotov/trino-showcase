-- Claim facts. Pending claims are not adjudicated yet and are excluded from denial rate denominators.
select
    claim_hk,
    encounter_hk,
    patient_hk,
    tenant_id,
    service_dt,
    claim_amount,
    claim_status,
    case when claim_status = 'denied' then 1 else 0 end as denied_claim,
    case when claim_status in ('paid', 'denied') then 1 else 0 end as adjudicated_claim
from {{ ref('claim') }}
