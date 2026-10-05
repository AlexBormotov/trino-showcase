with unioned as (
    select * from {{ ref('stg_clinic_a__v1_bill') }}
    union all
    select * from {{ ref('stg_clinic_a__v2_claims') }}
    union all
    select * from {{ ref('stg_clinic_b__claim') }}
    union all
    select * from {{ ref('stg_clinic_c__claims') }}
)

select
    {{ hash_key(['tenant_id', 'claim_id']) }} as claim_hk,
    {{ hash_key(['tenant_id', 'encounter_id']) }} as encounter_hk,
    {{ hash_key(['tenant_id', 'patient_id']) }} as patient_hk,
    tenant_id,
    claim_id,
    encounter_id,
    patient_id,
    service_dt,
    claim_amount,
    claim_status,
    source_system,
    source_schema_version
from unioned
