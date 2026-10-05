-- Soft-deleted rows are duplicates kept by the application, not encounters.
select
    'clinic_b' as tenant_id, 'mysql' as source_system, 'v1' as source_schema_version,
    visitid as encounter_id,
    patientid as patient_id,
    cast(visitstart as timestamp(6)) as start_ts,
    cast(visitend as timestamp(6)) as end_ts,
    visitkind as encounter_class,
    proccode as encounter_code,
    procname as encounter_description,
    {{ cents_to_amount('totalcost', 'visitstart', '2023-07-01') }} as total_cost_amount
from {{ source('clinic_b', 'visit') }}
where isdeleted = 0
