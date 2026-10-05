{# Reusable harmonization rules. Staging models call these instead of repeating SQL per tenant. #}

{% macro parse_dmy_ts(col) -%}
    date_parse({{ col }}, '%d.%m.%Y %H:%i:%s')
{%- endmacro %}

{% macro parse_dmy_date(col) -%}
    cast(date_parse({{ col }}, '%d.%m.%Y') as date)
{%- endmacro %}

{# M/F, 1/2 and male/female all map to M/F; anything else is U (unknown). #}
{% macro gender_code(col) -%}
    case
        when lower({{ col }}) in ('m', '1', 'male') then 'M'
        when lower({{ col }}) in ('f', '2', 'female') then 'F'
        else 'U'
    end
{%- endmacro %}

{# For sources that switched from cents to currency units on a known date. #}
{% macro cents_to_amount(amount, at, switched_on) -%}
    cast(case when {{ at }} < date '{{ switched_on }}' then {{ amount }} / 100 else {{ amount }} end as decimal(14, 2))
{%- endmacro %}

{# 'SNOMED:44054006' -> '44054006'; NULL stays NULL. #}
{% macro strip_code_prefix(col) -%}
    regexp_replace({{ col }}, '^[A-Za-z-]+:', '')
{%- endmacro %}

{# Hash key over a business key: md5 of the parts joined with '|', NULLs as ''. #}
{% macro hash_key(cols) -%}
    to_hex(md5(to_utf8(concat_ws('|'
        {%- for c in cols %}, coalesce(cast({{ c }} as varchar), ''){% endfor -%}
    ))))
{%- endmacro %}
