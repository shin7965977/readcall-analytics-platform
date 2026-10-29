with pivoted as (
    select
        event_date,
        sum(case when event_name = 'referral_modal_opened' then event_count else 0 end) as step_1_referral_modal_opened,
        sum(case when event_name = 'referral_link_copied' then event_count else 0 end) as step_2_referral_link_copied,
        sum(case when event_name = 'referral_link_visited' then event_count else 0 end) as step_3_referral_link_visited,
        sum(case when event_name = 'referral_unlock_success' then event_count else 0 end) as step_4_referral_unlock_success,
        sum(case when event_name = 'custom_prompt_saved' then event_count else 0 end) as step_5_custom_prompt_saved
    from {{ ref('fct_feature_events') }}
    group by event_date
)

select
    event_date,
    step_1_referral_modal_opened,
    step_2_referral_link_copied,
    step_3_referral_link_visited,
    step_4_referral_unlock_success,
    step_5_custom_prompt_saved,
    round(
        cast(step_2_referral_link_copied as {{ dbt.type_float() }})
        / nullif(step_1_referral_modal_opened, 0),
        4
    ) as copy_intent_rate,
    round(
        cast(step_4_referral_unlock_success as {{ dbt.type_float() }})
        / nullif(step_2_referral_link_copied, 0),
        4
    ) as share_to_unlock_rate,
    round(
        (cast(step_2_referral_link_copied as {{ dbt.type_float() }}) / nullif(step_1_referral_modal_opened, 0))
        * (cast(step_4_referral_unlock_success as {{ dbt.type_float() }}) / nullif(step_2_referral_link_copied, 0)),
        4
    ) as viral_k_factor,
    round(step_4_referral_unlock_success * 8.50, 2) as referral_cac_saved_usd
from pivoted
order by event_date desc
