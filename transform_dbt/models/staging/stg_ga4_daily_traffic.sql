with source as (
    select * from {{ source('readcall_bronze', 'raw_ga4_daily_traffic') }}
),

deduped as (
    select
        cast(traffic_record_id as {{ dbt.type_string() }}) as traffic_record_id,
        cast(event_date as date) as event_date,
        cast(channel_group as {{ dbt.type_string() }}) as channel_group,
        cast(source_medium as {{ dbt.type_string() }}) as source_medium,
        lower(cast(device_category as {{ dbt.type_string() }})) as device_category,
        cast(country as {{ dbt.type_string() }}) as country,
        cast(sessions as {{ dbt.type_int() }}) as sessions,
        cast(engaged_sessions as {{ dbt.type_int() }}) as engaged_sessions,
        cast(active_users as {{ dbt.type_int() }}) as active_users,
        cast(new_users as {{ dbt.type_int() }}) as new_users,
        cast(avg_session_duration_sec as {{ dbt.type_float() }}) as avg_session_duration_sec,
        cast(event_count as {{ dbt.type_int() }}) as event_count,
        cast(updated_at as {{ dbt.type_timestamp() }}) as updated_at,
        row_number() over (
            partition by traffic_record_id
            order by updated_at desc
        ) as rn
    from source
)

select
    traffic_record_id,
    event_date,
    channel_group,
    source_medium,
    device_category,
    country,
    sessions,
    case when engaged_sessions > sessions then sessions else engaged_sessions end as engaged_sessions,
    active_users,
    case when new_users > active_users then active_users else new_users end as new_users,
    avg_session_duration_sec,
    event_count,
    updated_at
from deduped
where rn = 1
  and sessions > 0
