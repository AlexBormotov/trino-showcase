-- Daily calendar MetricFlow needs for time-based queries.
select cast(d as date) as date_day
from unnest(sequence(date '2015-01-01', date '2030-12-31', interval '1' day)) as t(d)
