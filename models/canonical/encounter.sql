with unioned as (
    select * from {{ ref('stg_clinic_a__v1_visit') }}
    union all
    select * from {{ ref('stg_clinic_a__v2_encounters') }}
    union all
    select * from {{ ref('stg_clinic_b__visit') }}
    union all
    select * from {{ ref('stg_clinic_c__encounters') }}
)

select
    {{ hash_key(['tenant_id', 'encounter_id']) }} as encounter_hk,
    {{ hash_key(['tenant_id', 'patient_id']) }} as patient_hk,
    tenant_id,
    encounter_id,
    patient_id,
    start_ts,
    end_ts,
    encounter_class,
    encounter_code,
    encounter_description,
    total_cost_amount,
    source_system,
    source_schema_version
from unioned
