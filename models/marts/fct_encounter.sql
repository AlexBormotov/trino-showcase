-- Encounter facts with the row-level flags metrics aggregate.
-- Readmission: an inpatient stay is readmitted when the same patient (same tenant) is
-- admitted as an inpatient again within 30 days after its discharge.

with inpatient as (
    select encounter_hk, patient_hk, end_ts
    from {{ ref('encounter') }}
    where encounter_class = 'inpatient'
),

-- First inpatient admission after discharge. Not lead(): inpatient stays of one patient
-- can overlap, and the next stay by start time may begin before this one ends.
next_admission as (
    select a.encounter_hk, a.end_ts, min(b.start_ts) as next_admission_ts
    from inpatient as a
    left join {{ ref('encounter') }} as b
        on b.patient_hk = a.patient_hk
       and b.encounter_class = 'inpatient'
       and b.start_ts > a.end_ts
    group by a.encounter_hk, a.end_ts
)

select
    e.encounter_hk,
    e.patient_hk,
    e.tenant_id,
    e.start_ts,
    e.end_ts,
    e.encounter_class,
    e.total_cost_amount,
    case when e.encounter_class = 'inpatient' then 1 else 0 end as inpatient_stay,
    case when e.encounter_class = 'inpatient'
        then cast(date_diff('second', e.start_ts, e.end_ts) / 86400.0 as decimal(12, 4))
    end as length_of_stay_days,
    case
        when i.encounter_hk is null then null
        when i.next_admission_ts > i.end_ts and i.next_admission_ts <= i.end_ts + interval '30' day then 1
        else 0
    end as readmitted_30d
from {{ ref('encounter') }} as e
left join next_admission as i on i.encounter_hk = e.encounter_hk
