# ReadCall Product Analytics & PLG Data Platform (`CONTEXT.md`)

提供 **ReadCall（德語 AI 沉浸式閱讀與形態學拆解平台，`https://readcall.app`）** 的現代化雲端數據中台（ELT + dbt Semantic Layer + BI + PLG AI Advisor），兼具極低維運成本（~$0/月閒置成本）、嚴格資安去識別化（Zero-PII）與產品驅動成長（Product-Led Growth, PLG）漏斗分析能力。

---

## Domain Language & Ubiquitous Vocabulary

**Active User (`active_users` / DAU)**:
在特定時間窗內造訪 ReadCall 並觸發互動工作階段的不重複學習者（由 GA4 匿名彙總計算，不含任何個人識別資訊）。

**Aha! Moment (`aha_activation`)**:
新訪客在進入 ReadCall 後，首次實際體驗德語核心學習功能——包含在閱讀器中選取德文字句拆解（`reader_text_selected`）、點擊 AI 形態學與語法解釋（`reader_explain_clicked`）、或查詢德語雙語複合詞字典（`dictionary_searched`）。

**BYOK (Bring Your Own Key) Funnel**:
ReadCall 採用的「零訂閱費 + 用戶自備免費 Google AI Studio Gemini API Key」商業與留存架構：
- 免費試用額度體驗 ➔ 試用額度耗盡牆（`trial_exhausted_viewed`）或點擊頂部提示橫幅（`trial_banner_cta_clicked`）➔ 開啟金鑰設定視窗（`byok_modal_opened`）➔ 點擊前往領取金鑰（`byok_get_key_click`）或手動貼上（`byok_manual_paste_clicked`）➔ 驗證成功並儲存金鑰（`byok_key_saved`，解鎖每日 1,500 次免費額度）或驗證失敗（`byok_verify_failed`）。

**Viral Referral Loop (`referral_loop`)**:
ReadCall 的自然裂變增長迴圈：學習者為了解鎖「自訂 AI 家教提示詞（Custom AI Tutor Prompt）」，開啟推薦視窗（`referral_modal_opened`）➔ 複製個人推薦連結（`referral_link_copied`）➔ 好友透過推薦連結造訪（`referral_link_visited`）➔ 成功解鎖進階功能（`referral_unlock_success`）並儲存自訂提示詞（`custom_prompt_saved`）。

**Feature Module (`module_category`)**:
將 ReadCall 的 32+ 項 GA4 追蹤事件標準化映射為 5 大產品功能模組：
1. `Acquisition & Onboarding`（流量獲取與新手文件載入）
2. `Core Reader & Morphology`（德語閱讀器選字、AI 解釋、6 時態動詞變化表、AI Tutor 提問）
3. `Dictionary, Vocab & Recall`（雙語字典查詢、詞性色彩檢視、單字庫收藏、4 大 AI 測驗模式與閃卡）
4. `BYOK Monetization Funnel`（試用耗盡至綁定 Gemini API Key 轉換漏斗）
5. `Viral Referral & Feedback`（推薦分享解鎖與用戶回饋）

---

## Semantic Layer Core Metrics (`transform_dbt/models/semantic_models.yml`)

- **Aha! Activation Rate (`aha_activation_rate`)**:
  `Unique Users triggering (reader_text_selected OR dictionary_searched) / first_visit`
- **AI Morphological Depth Ratio (`ai_depth_ratio`)**:
  `(reader_explain_clicked + verb_conjugation_viewed + tutor_question_sent) / reader_text_selected`
- **BYOK Conversion Rate (`byok_conversion_rate`)**:
  `byok_key_saved / trial_exhausted_viewed`
- **BYOK Modal Completion Rate (`byok_modal_completion_rate`)**:
  `byok_key_saved / byok_modal_opened`
- **BYOK Verification Failure Rate (`byok_verify_failure_rate`)**:
  `byok_verify_failed / (byok_key_saved + byok_verify_failed)`
- **Viral K-Factor Proxy (`viral_k_factor`)**:
  `(referral_link_copied / referral_modal_opened) * (referral_unlock_success / referral_link_visited)`
- **AI Compute Offloaded (`offloaded_ai_compute_usd`)**:
  因用戶綁定 BYOK 自備金鑰，為平台轉移並省下的雲端 LLM 推論與代理伺服器成本。
- **Referral CAC Saved (`referral_cac_saved_usd`)**:
  透過推薦裂變帶來之新訪客，對標同業 EdTech 付費廣告獲客成本（CAC）所節省的行銷費用。

---

## Medallion Layers & Security Boundary

- **Bronze (`readcall_bronze`)**: 由 `dlt` (`ga4_adapter.py`) 寫入，僅包含通過嚴格事件白名單（Strict Event Allowlist）的去識別化聚合紀錄（`raw_ga4_daily_traffic`, `raw_ga4_events`）。任何求職追蹤事件（`portfolio_*`）或個資在擷取端即被 100% 過濾排除。
- **Silver (`readcall_silver`)**: 由 `dbt` 轉換為星型維度模型（`dim_channels`, `dim_devices_geo`, `dim_feature_catalog`, `fct_daily_traffic`, `fct_feature_events`）。
- **Gold (`readcall_gold`)**: 面向 Streamlit 戰略儀表板與 FastMCP 產品成長顧問的高效能聚合寬表（`gold_daily_growth_kpi`, `gold_feature_adoption`, `gold_byok_funnel`, `gold_referral_loop`）。
