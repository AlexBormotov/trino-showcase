select
    lsn,
    cast(op as varchar) as op,  -- char(1) is not a valid Iceberg view column type
    patient_id,
    cast(changed_at as timestamp(6)) as changed_ts,
    address,
    city,
    zip
from {{ source('clinic_a_v2', 'patient_cdc') }}
