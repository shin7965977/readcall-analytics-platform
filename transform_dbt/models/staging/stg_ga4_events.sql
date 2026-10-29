with source as (
    select * from {{ source('readcall_bronze', 'raw_ga4_events') }}
),

deduped as (
    select
        cast(event_record_id as {{ dbt.type_string() }}) as event_record_id,
        cast(event_date as date) as event_date,
        cast(event_name as {{ dbt.type_string() }}) as event_name,
        lower(cast(device_category as {{ dbt.type_string() }})) as device_category,
        cast(channel_group as {{ dbt.type_string() }}) as channel_group,
        cast(event_count as {{ dbt.type_int() }}) as event_count,
        cast(total_users as {{ dbt.type_int() }}) as total_users,
        cast(updated_at as {{ dbt.type_timestamp() }}) as updated_at,
        row_number() over (
            partition by event_record_id
            order by updated_at desc
        ) as rn
    from source
)

select
    event_record_id,
    event_date,
    event_name,
    device_category,
    channel_group,
    event_count,
    case when total_users > event_count then event_count else total_users end as total_users,
    updated_at
from deduped
where rn = 1
  and event_count > 0
  and event_name not like 'portfolio_%'
