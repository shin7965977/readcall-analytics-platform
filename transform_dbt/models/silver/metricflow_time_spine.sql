with days as (
    select distinct event_date as date_day
    from {{ ref('stg_ga4_daily_traffic') }}
)

select
    cast(date_day as date) as date_day
from days
