with distinct_geo as (
    select distinct
        device_category,
        country
    from {{ ref('stg_ga4_daily_traffic') }}
)

select
    concat(lower(device_category), '__', lower(replace(country, ' ', '_'))) as device_geo_key,
    device_category,
    country,
    case
        when country in ('Germany', 'Austria', 'Switzerland') then true
        else false
    end as is_dach_region
from distinct_geo
