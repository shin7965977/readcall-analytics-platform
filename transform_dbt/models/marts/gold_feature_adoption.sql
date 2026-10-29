with agg as (
    select
        c.event_name,
        c.module_category,
        c.aarrr_stage,
        c.source_component,
        c.is_aha_moment,
        c.is_ai_inference_event,
        coalesce(sum(f.event_count), 0) as total_event_count,
        coalesce(sum(f.total_users), 0) as total_active_user_days
    from {{ ref('dim_feature_catalog') }} c
    left join {{ ref('fct_feature_events') }} f
        on c.event_name = f.event_name
    group by
        c.event_name,
        c.module_category,
        c.aarrr_stage,
        c.source_component,
        c.is_aha_moment,
        c.is_ai_inference_event
),

grand_total as (
    select sum(total_event_count) as all_events from agg
)

select
    a.event_name,
    a.module_category,
    a.aarrr_stage,
    a.source_component,
    a.is_aha_moment,
    a.is_ai_inference_event,
    a.total_event_count,
    a.total_active_user_days,
    round(cast(a.total_event_count as {{ dbt.type_float() }}) / nullif(a.total_active_user_days, 0), 2) as avg_frequency_per_user,
    round(cast(a.total_event_count as {{ dbt.type_float() }}) * 100.0 / nullif(g.all_events, 0), 2) as interaction_share_pct,
    case
        when a.total_event_count >= 1500 then 'Core Pillar'
        when a.total_event_count >= 250 then 'Power Feature'
        when a.total_event_count >= 40 then 'Growth Lever'
        else 'Emerging Feature'
    end as adoption_tier
from agg a
cross join grand_total g
order by a.total_event_count desc
