with pivoted as (
    select
        event_date,
        sum(case when event_name = 'first_visit' then event_count else 0 end) as step_1_first_visit,
        sum(case when event_name in ('reader_text_selected', 'dictionary_searched') then total_users else 0 end) as step_2_aha_interaction,
        sum(case when event_name in ('trial_exhausted_viewed', 'trial_banner_cta_clicked') then event_count else 0 end) as step_3_trial_limit_hit,
        sum(case when event_name = 'byok_modal_opened' then event_count else 0 end) as step_4_byok_modal_opened,
        sum(case when event_name in ('byok_get_key_click', 'byok_manual_paste_clicked') then event_count else 0 end) as step_5_key_acquisition_attempt,
        sum(case when event_name = 'byok_key_saved' then event_count else 0 end) as step_6_byok_key_saved,
        sum(case when event_name = 'byok_verify_failed' then event_count else 0 end) as byok_verify_failed,
        sum(case when event_name = 'reader_explain_clicked' then event_count else 0 end) as reader_explain_clicked,
        sum(case when event_name = 'verb_conjugation_viewed' then event_count else 0 end) as verb_conjugation_viewed,
        sum(case when event_name = 'tutor_question_sent' then event_count else 0 end) as tutor_question_sent,
        sum(case when event_name = 'reader_text_selected' then event_count else 0 end) as reader_text_selected
    from {{ ref('fct_feature_events') }}
    group by event_date
)

select
    event_date,
    step_1_first_visit,
    step_2_aha_interaction,
    step_3_trial_limit_hit,
    step_4_byok_modal_opened,
    step_5_key_acquisition_attempt,
    step_6_byok_key_saved,
    byok_verify_failed,
    round(
        cast(reader_explain_clicked + verb_conjugation_viewed + tutor_question_sent as {{ dbt.type_float() }})
        / nullif(reader_text_selected, 0),
        4
    ) as ai_morphological_depth,
    round(
        cast(step_4_byok_modal_opened as {{ dbt.type_float() }})
        / nullif(step_3_trial_limit_hit, 0),
        4
    ) as trial_to_modal_rate,
    round(
        cast(step_6_byok_key_saved as {{ dbt.type_float() }})
        / nullif(step_4_byok_modal_opened, 0),
        4
    ) as byok_modal_completion_rate,
    round(
        cast(step_6_byok_key_saved as {{ dbt.type_float() }})
        / nullif(step_3_trial_limit_hit, 0),
        4
    ) as byok_conversion_rate,
    round(
        cast(byok_verify_failed as {{ dbt.type_float() }})
        / nullif(step_6_byok_key_saved + byok_verify_failed, 0),
        4
    ) as byok_verify_failure_rate
from pivoted
order by event_date desc
