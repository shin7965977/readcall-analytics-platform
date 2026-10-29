with catalog as (
    select 'page_view' as event_name, '1_Acquisition_Onboarding' as module_category, 'Acquisition' as aarrr_stage, 'src/app/layout.tsx' as source_component, false as is_aha_moment, false as is_ai_inference_event, 0 as funnel_step_order union all
    select 'session_start', '1_Acquisition_Onboarding', 'Acquisition', 'src/app/layout.tsx', false, false, 0 union all
    select 'first_visit', '1_Acquisition_Onboarding', 'Acquisition', 'src/app/page.tsx', false, false, 1 union all
    select 'user_engagement', '1_Acquisition_Onboarding', 'Acquisition', 'src/app/page.tsx', false, false, 0 union all
    select 'scroll', '1_Acquisition_Onboarding', 'Acquisition', 'src/app/page.tsx', false, false, 0 union all
    select 'click', '1_Acquisition_Onboarding', 'Acquisition', 'src/app/page.tsx', false, false, 0 union all
    select 'form_start', '1_Acquisition_Onboarding', 'Activation', 'src/app/dictionary/page.tsx', false, false, 0 union all
    select 'starter_doc_loaded', '1_Acquisition_Onboarding', 'Activation', 'src/app/library/page.tsx', false, false, 0 union all
    select 'sample_story_loaded', '1_Acquisition_Onboarding', 'Activation', 'src/app/library/page.tsx', false, false, 0 union all
    select 'document_uploaded', '1_Acquisition_Onboarding', 'Activation', 'src/app/library/page.tsx', false, false, 0 union all
    select 'reader_text_selected', '2_Core_Reader_Morphology', 'Activation', 'src/app/reader/[id]/page.tsx', true, false, 2 union all
    select 'reader_explain_clicked', '2_Core_Reader_Morphology', 'Activation', 'src/app/reader/[id]/page.tsx', true, true, 0 union all
    select 'verb_conjugation_viewed', '2_Core_Reader_Morphology', 'Retention', 'src/components/reader/LinguisticInspectorContent.tsx', false, false, 0 union all
    select 'tutor_question_sent', '2_Core_Reader_Morphology', 'Retention', 'src/components/reader/LinguisticInspectorContent.tsx', false, true, 0 union all
    select 'dictionary_searched', '3_Dictionary_Vocab_Quiz', 'Activation', 'src/app/dictionary/page.tsx', true, false, 2 union all
    select 'view_search_results', '3_Dictionary_Vocab_Quiz', 'Activation', 'src/app/dictionary/page.tsx', false, false, 0 union all
    select 'dictionary_word_selected', '3_Dictionary_Vocab_Quiz', 'Retention', 'src/app/dictionary/page.tsx', false, false, 0 union all
    select 'vocab_saved', '3_Dictionary_Vocab_Quiz', 'Retention', 'src/components/reader/LinguisticInspectorContent.tsx', false, false, 0 union all
    select 'favorite_button_clicked', '3_Dictionary_Vocab_Quiz', 'Retention', 'src/components/FavoriteButton.tsx', false, false, 0 union all
    select 'trial_banner_cta_clicked', '4_BYOK_Monetization', 'Revenue_BYOK', 'src/components/reader/LinguisticInspectorContent.tsx', false, false, 3 union all
    select 'trial_exhausted_viewed', '4_BYOK_Monetization', 'Revenue_BYOK', 'src/components/reader/LinguisticInspectorContent.tsx', false, false, 3 union all
    select 'byok_modal_opened', '4_BYOK_Monetization', 'Revenue_BYOK', 'src/components/ByokModal.tsx', false, false, 4 union all
    select 'byok_get_key_click', '4_BYOK_Monetization', 'Revenue_BYOK', 'src/components/ByokModal.tsx', false, false, 5 union all
    select 'byok_manual_paste_clicked', '4_BYOK_Monetization', 'Revenue_BYOK', 'src/components/ByokModal.tsx', false, false, 5 union all
    select 'byok_key_saved', '4_BYOK_Monetization', 'Revenue_BYOK', 'src/components/ByokModal.tsx', false, false, 6 union all
    select 'byok_verify_failed', '4_BYOK_Monetization', 'Revenue_BYOK', 'src/components/ByokModal.tsx', false, false, 0 union all
    select 'referral_modal_opened', '5_Referral_Viral_Loop', 'Referral', 'src/components/reader/TutorCustomPromptModal.tsx', false, false, 1 union all
    select 'referral_link_copied', '5_Referral_Viral_Loop', 'Referral', 'src/components/reader/TutorCustomPromptModal.tsx', false, false, 2 union all
    select 'referral_link_visited', '5_Referral_Viral_Loop', 'Referral', 'src/components/ReferralWelcomeBanner.tsx', false, false, 3 union all
    select 'referral_unlock_success', '5_Referral_Viral_Loop', 'Referral', 'src/components/reader/TutorCustomPromptModal.tsx', false, false, 4 union all
    select 'custom_prompt_saved', '5_Referral_Viral_Loop', 'Retention', 'src/components/reader/TutorCustomPromptModal.tsx', false, false, 5 union all
    select 'feedback_submitted', '5_Referral_Viral_Loop', 'Retention', 'src/components/FeedbackModal.tsx', false, false, 0
)

select
    cast(event_name as {{ dbt.type_string() }}) as event_name,
    cast(module_category as {{ dbt.type_string() }}) as module_category,
    cast(aarrr_stage as {{ dbt.type_string() }}) as aarrr_stage,
    cast(source_component as {{ dbt.type_string() }}) as source_component,
    cast(is_aha_moment as boolean) as is_aha_moment,
    cast(is_ai_inference_event as boolean) as is_ai_inference_event,
    cast(funnel_step_order as {{ dbt.type_int() }}) as funnel_step_order
from catalog
