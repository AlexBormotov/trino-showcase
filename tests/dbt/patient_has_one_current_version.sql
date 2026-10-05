select patient_hk, count_if(is_current) as current_versions
from {{ ref('patient') }}
group by patient_hk
having count_if(is_current) <> 1
