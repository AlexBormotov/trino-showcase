select
    'clinic_b' as tenant_id, 'mysql' as source_system, 'v1' as source_schema_version,
    d.visitid as encounter_id,
    d.patientid as patient_id,
    d.diagdate as onset_dt,
    c.snomedcode as snomed_code,
    c.label as diagnosis_description
from {{ source('clinic_b', 'visitdiagnosis') }} as d
left join {{ source('clinic_b', 'dxcode') }} as c on c.localcode = d.localcode
