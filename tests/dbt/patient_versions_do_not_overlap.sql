-- Each version must end exactly where the next one starts, and never before it starts.
select *
from (
    select
        patient_hk,
        valid_from_ts,
        valid_to_ts,
        lead(valid_from_ts) over (partition by patient_hk order by valid_from_ts) as next_from_ts
    from {{ ref('patient') }}
) as v
where valid_to_ts <= valid_from_ts
   or valid_to_ts is distinct from next_from_ts
