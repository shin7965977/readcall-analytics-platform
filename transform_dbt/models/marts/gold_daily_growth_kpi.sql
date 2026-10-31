with daily_traffic as (
    select
        event_date,
        sum(active_users) as dau,
        sum(new_users) as new_users,
        sum(returning_users) as returning_users,
        sum(sessions) as total_sessions,
        sum(engaged_sessions) as engaged_sessions,
        round(avg(avg_session_duration_sec), 2) as avg_session_duration_sec
    from {{ ref('fct_daily_traffic') }}
    group by event_date
),

daily_events as (
    select
        e.event_date,
        sum(case when c.is_aha_moment then e.total_users else 0 end) as raw_aha_users,
        sum(case when c.module_category = '2_Core_Reader_Morphology' then e.event_count else 0 end) as core_reader_events,
        sum(case when c.module_category = '3_Dictionary_Vocab_Quiz' then e.event_count else 0 end) as dictionary_events,
        sum(case when c.is_ai_inference_event then e.event_count else 0 end) as ai_inference_events,
        sum(case when e.event_name = 'byok_key_saved' then e.event_count else 0 end) as byok_keys_saved,
        sum(case when e.event_name = 'referral_unlock_success' then e.event_count else 0 end) as referral_unlocks
    from {{ ref('fct_feature_events') }} e
    left join {{ ref('dim_feature_catalog') }} c on e.event_name = c.event_name
    group by e.event_date
)

select
    t.event_date,
    t.dau,
    t.new_users,
    t.returning_users,
    t.total_sessions,
    t.engaged_sessions,
    round(cast(t.engaged_sessions as {{ dbt.type_float() }}) / nullif(t.total_sessions, 0), 4) as engagement_rate,
    t.avg_session_duration_sec,
    case
        when coalesce(e.raw_aha_users, 0) > t.dau then cast(round(t.dau * 0.78) as {{ dbt.type_int() }})
        else coalesce(e.raw_aha_users, 0)
    end as aha_users,
    round(
        cast(
            case
                when coalesce(e.raw_aha_users, 0) > t.dau then round(t.dau * 0.78)
                else coalesce(e.raw_aha_users, 0)
            end as {{ dbt.type_float() }}
        ) / nullif(t.dau, 0),
        4
    ) as aha_activation_rate,
    coalesce(e.core_reader_events, 0) as core_reader_events,
    coalesce(e.dictionary_events, 0) as dictionary_events,
    coalesce(e.ai_inference_events, 0) as ai_inference_events,
    coalesce(e.byok_keys_saved, 0) as byok_keys_saved,
    coalesce(e.referral_unlocks, 0) as referral_unlocks,
    round(coalesce(e.ai_inference_events, 0) * 0.0025 + coalesce(e.byok_keys_saved, 0) * 0.45, 2) as offloaded_ai_compute_usd
from daily_traffic t
left join daily_events e
    on t.event_date = e.event_date
order by t.event_date desc
