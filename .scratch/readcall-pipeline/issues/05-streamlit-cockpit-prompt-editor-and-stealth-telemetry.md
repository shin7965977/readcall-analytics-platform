# 05: Bilingual Streamlit PLG Cockpit, Interactive System Prompt Editor & Stealth Recruiter Telemetry

**What to build:** Build the bilingual Streamlit Product Analytics & PLG Strategic Cockpit (`dashboard.py` & `dashboard_en.py`) featuring 4 SaaS analytical tabs, an interactive System Prompt Editor (`🛠️ 檢視 / 修改系統 Prompt`) in the AI Advisor drawer, and a 0px stealth recruiter telemetry module (`recruiter_telemetry.py`) that tracks `?utm_campaign=` / `?ref=` opens to `PORTFOLIO_TRACKER_GA_ID` without exposing any trace on the UI.

**Blocked by:** 04: FastMCP Gold Governance Server & PLG Growth Lead Diagnostic Engine

**Status:** closed

- [x] Tab 1 displays AARRR Growth Overview (DAU, Sessions, Engagement Rate, Aha! Activation Rate, DACH vs. Global breakdown, Channel Acquisition).
- [x] Tab 2 displays German Reader & Feature Stickiness (80/20 Pareto chart of the 32 events across 5 modules, mapped to `.tsx` components).
- [x] Tab 3 displays the 6-step BYOK API Key Conversion Funnel (highlighting `ByokModal.tsx` completion and `byok_verify_failed` friction) and the 5-step Viral Referral Loop (`TutorCustomPromptModal.tsx`).
- [x] Tab 4 provides the bilingual AI NL2Chart generator with one-click chart diagnostics.
- [x] The AI Advisor drawer includes the `🛠️ 檢視 / 修改系統 Prompt (Edit System Prompt)` toggle that reveals the default System Prompt, supports live manual edits (`💾 套用自訂 Prompt`), and includes a one-click reset (`🔄 還原預設值`).
- [x] Stealth Recruiter Telemetry silently fires `portfolio_opened`, `portfolio_tab_viewed`, and `portfolio_ai_tested` with `recruiter_ref` / `utm_campaign` to `PORTFOLIO_TRACKER_GA_ID` (with `?developer=true` opt-out) and leaves zero visual footprint on the dashboard.
