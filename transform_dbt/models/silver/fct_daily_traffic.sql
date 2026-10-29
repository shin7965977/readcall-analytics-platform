with stg as (
    select * from {{ ref('stg_ga4_daily_traffic') }}
)

select
    traffic_record_id,
    event_date,
    concat(lower(replace(channel_group, ' ', '_')), '__', lower(replace(replace(source_medium, ' ', ''), '/', '_'))) as channel_key,
    concat(lower(device_category), '__', lower(replace(country, ' ', '_'))) as device_geo_key,
    channel_group,
    source_medium,
    device_category,
    country,
    sessions,
    engaged_sessions,
    active_users,
    new_users,
    case when active_users > new_users then active_users - new_users else 0 end as returning_users,
    avg_session_duration_sec,
    round(cast(engaged_sessions as {{ dbt.type_float() }}) / nullif(sessions, 0), 4) as engagement_rate,
    event_count,
    updated_at
from stg
