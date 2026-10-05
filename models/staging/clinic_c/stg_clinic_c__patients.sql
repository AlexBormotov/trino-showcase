-- The archive has no registration timestamp: the version is open since an unknown date.
select
    'clinic_c' as tenant_id, 'iceberg' as source_system, 'v1' as source_schema_version,
    id as patient_id,
    given_name as first_name,
    family_name as last_name,
    birth_date as birth_dt,
    {{ gender_code('gender') }} as gender,
    ssn,
    address,
    city,
    zip,
    timestamp '1900-01-01 00:00:00.000000' as valid_from_ts
from {{ source('clinic_c', 'patients') }}
