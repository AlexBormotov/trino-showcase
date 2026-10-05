-- Current version of each patient: the patient dimension for metrics.
select
    patient_hk,
    tenant_id,
    gender,
    birth_dt,
    city,
    zip,
    valid_from_ts
from {{ ref('patient') }}
where is_current
