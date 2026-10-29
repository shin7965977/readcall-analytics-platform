with stg as (
    select * from {{ ref('stg_ga4_events') }}
),

catalog as (
    select * from {{ ref('dim_feature_catalog') }}
)

select
    s.event_record_id,
    s.event_date,
    s.event_name,
    c.module_category,
    c.aarrr_stage,
    c.source_component,
    c.is_aha_moment,
    c.is_ai_inference_event,
    s.device_category,
    s.channel_group,
    s.event_count,
    s.total_users,
    round(cast(s.event_count as {{ dbt.type_float() }}) / nullif(s.total_users, 0), 2) as events_per_user,
    s.updated_at
from stg s
inner join catalog c
    on s.event_name = c.event_name
