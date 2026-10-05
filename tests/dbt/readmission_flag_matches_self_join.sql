-- Same definition written with EXISTS instead of a grouped join: the flags must agree.
with inpatient as (
    select encounter_hk, patient_hk, start_ts, end_ts
    from {{ ref('encounter') }}
    where encounter_class = 'inpatient'
),

expected as (
    select
        a.encounter_hk,
        case when exists (
            select 1 from inpatient as b
            where b.patient_hk = a.patient_hk
              and b.encounter_hk <> a.encounter_hk
              and b.start_ts > a.end_ts
              and b.start_ts <= a.end_ts + interval '30' day
        ) then 1 else 0 end as readmitted_30d
    from inpatient as a
)

select e.encounter_hk, e.readmitted_30d as expected, f.readmitted_30d as actual
from expected as e
join {{ ref('fct_encounter') }} as f on f.encounter_hk = e.encounter_hk
where e.readmitted_30d <> f.readmitted_30d
