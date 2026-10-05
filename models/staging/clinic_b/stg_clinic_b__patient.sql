-- Current state only: the source keeps no history.
select
    'clinic_b' as tenant_id, 'mysql' as source_system, 'v1' as source_schema_version,
    patientid as patient_id,
    firstname as first_name,
    lastname as last_name,
    dob as birth_dt,
    {{ gender_code('sex') }} as gender,
    ssn,
    street as address,
    city,
    postalcode as zip,
    cast(createdat as timestamp(6)) as valid_from_ts
from {{ source('clinic_b', 'patient') }}
