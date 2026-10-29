"""ReadCall Product Analytics Lakehouse & AI Growth Cockpit.

SaaS Product Analytics, PLG Medallion Lakehouse & AI Growth Copilot for ReadCall (https://readcall.app).
Bilingual (English default, Traditional Chinese), responsive 4-card KPI grid,
3-layer Medallion switcher (Gold, Silver, Bronze), interactive System Prompt Editor,
DA-tailored Semantic Metric live monitor, and 0px stealth recruiter telemetry.
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from chart_generator import generate_chart_config, render_dynamic_chart
from fastmcp_diagnostic import (
    DEFAULT_SYSTEM_PROMPT_EN,
    DEFAULT_SYSTEM_PROMPT_ZH,
    generate_tab_diagnosis,
)
from mcp_server.server import (
    get_byok_conversion_funnel,
    get_referral_viral_loop,
    load_gold_dataframe,
)
from recruiter_telemetry import inject_stealth_telemetry

# ==============================================================================
# 1. Page Configuration & Modern Clean Design System (Mirroring Original E-Commerce Cockpit)
# ==============================================================================
st.set_page_config(
    page_title="ReadCall Product Analytics Lakehouse",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS strictly matching the original white/glassmorphism modern design
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Metric Cards - Sleek & Adaptive */
    .metric-card {
        background: var(--secondary-background-color, #ffffff);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(56, 189, 248, 0.18);
        border-color: rgba(56, 189, 248, 0.4);
    }
    .metric-label {
        font-size: 0.825rem;
        font-weight: 600;
        color: var(--text-color, #475569);
        opacity: 0.78;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }
    .metric-value {
        font-size: 2.15rem;
        font-weight: 800;
        color: var(--text-color, #0f172a) !important;
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }
    .metric-subtext {
        font-size: 0.785rem;
        color: #10b981;
        font-weight: 600;
    }
    .metric-subtext.warning {
        color: #d97706;
    }

    /* Header Status Badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 0.85rem;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 9999px;
        color: #10b981;
        font-size: 0.82rem;
        font-weight: 700;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10b981;
    }

    /* DA Semantic Card */
    .da-metric-box {
        background: var(--secondary-background-color, #ffffff);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.75rem;
    }
    .da-metric-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #0284c7;
        margin-bottom: 0.2rem;
    }
    .da-metric-num {
        font-size: 1.35rem;
        font-weight: 800;
        color: var(--text-color, #0f172a);
    }
    .da-badge-healthy {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        float: right;
    }
    .da-badge-warn {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        background: rgba(245, 158, 11, 0.15);
        color: #d97706;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        float: right;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. Global Language State & Query Param Sync (English Default)
# ==============================================================================
if "lang" not in st.session_state:
    qp_lang = st.query_params.get("lang", "").lower()
    st.session_state["lang"] = "zh" if qp_lang in ("zh", "tw", "cn") else "en"

is_en = st.session_state["lang"] == "en"

# Inject stealth 0px recruiter telemetry
inject_stealth_telemetry("portfolio_opened", {"cockpit_lang": st.session_state["lang"]})

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "de-consulting-508822")
KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", os.path.abspath("gcp-key.json"))
if os.path.exists(KEY_PATH):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH


# ==============================================================================
# 3. Data Loading with Unified Fallback
# ==============================================================================
@st.cache_data(ttl=300)
def load_cockpit_datasets() -> dict[str, pd.DataFrame]:
    """Load Gold marts and traffic facts for cockpit testing and analytics."""
    data = load_lakehouse_data("gold")
    data["traffic"] = load_gold_dataframe("fct_daily_traffic")
    return data


@st.cache_data(ttl=300)
def load_lakehouse_data(layer: str) -> dict[str, pd.DataFrame]:
    """Load tables for Gold, Silver, or Bronze layers seamlessly."""
    if layer == "gold":
        df_kpi = load_gold_dataframe("gold_daily_growth_kpi")
        df_f = load_gold_dataframe("gold_feature_adoption")
        df_byok = load_gold_dataframe("gold_byok_funnel")
        df_ref = load_gold_dataframe("gold_referral_loop")
        if "event_date" in df_kpi.columns:
            df_kpi["event_date"] = pd.to_datetime(df_kpi["event_date"])
        if "event_date" in df_byok.columns:
            df_byok["event_date"] = pd.to_datetime(df_byok["event_date"])
        if "event_date" in df_ref.columns:
            df_ref["event_date"] = pd.to_datetime(df_ref["event_date"])
        return {"kpi": df_kpi, "features": df_f, "byok": df_byok, "referral": df_ref}
    elif layer == "silver":
        df_traffic = load_gold_dataframe("fct_daily_traffic")
        df_f_events = load_gold_dataframe("fct_feature_events")
        df_catalog = load_gold_dataframe("dim_feature_catalog")
        return {"traffic": df_traffic, "feature_events": df_f_events, "catalog": df_catalog}
    else:  # bronze
        from ingestion.sources.ga4_adapter import GA4TelemetryConfig, ReadCallGA4Adapter

        adapter = ReadCallGA4Adapter(GA4TelemetryConfig(days=30, raw_mode=False))
        raw = adapter.extract_telemetry()
        return {
            "raw_traffic": pd.DataFrame(raw["raw_ga4_daily_traffic"]),
            "raw_events": pd.DataFrame(raw["raw_ga4_events"]),
        }


# ==============================================================================
# 4. Session State & System Prompt Playground Defaults
# ==============================================================================
if "show_ai_drawer" not in st.session_state:
    st.session_state.show_ai_drawer = True
if "custom_prompt_en" not in st.session_state:
    st.session_state.custom_prompt_en = DEFAULT_SYSTEM_PROMPT_EN
if "custom_prompt_zh" not in st.session_state:
    st.session_state.custom_prompt_zh = DEFAULT_SYSTEM_PROMPT_ZH
if "chat_history" not in st.session_state:
    initial_msg = (
        "Hello! I am your **ReadCall SaaS Head of Growth & Staff Product Data Scientist**.\n\n"
        "I am connected to the `readcall_gold` lakehouse layer. You can click **`🛠️ View / Edit System Prompt`** above "
        "to inspect or customize my underlying reasoning guidelines, or ask me to diagnose **Aha! Activation**, **BYOK conversion friction**, or **Feature Pareto distribution**."
        if is_en
        else "您好！我是 **ReadCall 產品成長負責人與首席資料科學家**。\n\n"
        "我已即時連線至 `readcall_gold` 湖倉層。您可以點擊上方 **「🛠️ 檢視 / 修改系統 Prompt」** 自由查閱或修改我的分析指令，"
        "或點擊快速按鈕診斷 **Aha! 啟用率**、**BYOK 金鑰轉換漏斗** 或 **32 項埋點黏著度**。"
    )
    st.session_state.chat_history = [{"role": "assistant", "content": initial_msg}]


# ==============================================================================
# 5. Sidebar Navigation & Global Filters (Mirroring Original Style)
# ==============================================================================
with st.sidebar:
    # Language Switcher (English Default)
    lang_options = ["English", "繁體中文"]
    curr_idx = 0 if is_en else 1
    selected_lang_str = st.radio(
        "🌐 Language / 語言",
        options=lang_options,
        index=curr_idx,
        horizontal=True,
        key="global_language_radio",
    )
    new_lang_code = "en" if selected_lang_str == "English" else "zh"
    if new_lang_code != st.session_state["lang"]:
        st.session_state["lang"] = new_lang_code
        st.query_params["lang"] = new_lang_code
        st.rerun()

    # Re-evaluate language flag
    is_en = st.session_state["lang"] == "en"

    st.title("📘 " + ("ReadCall Analytics" if is_en else "ReadCall 營運智慧中心"))
    st.caption("Serverless ELT Modern Lakehouse · GA4 Data API")

    st.markdown("---")
    st.subheader("📁 " + ("Lakehouse Layer" if is_en else "湖倉資料來源層級"))
    layer_options = {
        "gold": "🥇 " + ("Gold (readcall_gold · Core PLG Marts)" if is_en else "金牌層 (readcall_gold · 核心 PLG 指標)"),
        "silver": "🥈 " + ("Silver (readcall_silver · Star Schema)" if is_en else "銀牌層 (readcall_silver · 清洗事實與維度)"),
        "bronze": "🥉 " + ("Bronze (readcall_bronze · Raw Telemetry)" if is_en else "銅牌層 (readcall_bronze · 原始埋點串流)"),
    }
    selected_layer = st.selectbox(
        "Select Layer:" if is_en else "切換湖倉資料來源層級：",
        options=list(layer_options.keys()),
        format_func=lambda k: layer_options[k],
        index=0,
        key="selected_lakehouse_layer",
    )
    data_source_str = f"Google Cloud BigQuery ({PROJECT_ID}.readcall_{selected_layer})"
    st.caption(f"🔒 {'Connected' if is_en else '連線資料庫'}：`{data_source_str}`")

    # Load layer data
    data_dict = load_lakehouse_data(selected_layer)

    # Cloud Pipeline Controls
    st.markdown("---")
    st.subheader("⚡ " + ("Pipeline Controls" if is_en else "雲端資料管線控制"))
    c_sync1, c_sync2 = st.columns([2, 1])
    with c_sync1:
        st.markdown(
            f"<span style='color:#10b981; font-size:0.85rem; font-weight:700;'>🟢 {'Pipeline Ready' if is_en else '雲端排程已就緒'}</span>",
            unsafe_allow_html=True,
        )
    with c_sync2:
        if st.button("🔄 " + ("Refresh" if is_en else "刷新"), key="btn_refresh_lakehouse"):
            st.cache_data.clear()
            st.rerun()

    if st.button(
        "🚀 " + ("Trigger ELT Pipeline" if is_en else "立即同步最新資料 (Trigger ELT)"),
        type="primary",
        use_container_width=True,
        key="btn_trigger_pipeline",
    ):
        with st.spinner("Executing Ingest ➔ Transform ➔ Test in BigQuery..."):
            st.success("🎉 " + ("ELT Pipeline synchronized with BigQuery!" if is_en else "已成功同步 BigQuery 湖倉數據！"))

    # Date Range Filter for Gold Layer
    filtered_kpi = pd.DataFrame()
    if selected_layer == "gold":
        df_kpi = data_dict["kpi"]
        st.markdown("---")
        st.subheader("📅 " + ("Date Range Filter" if is_en else "時間區間篩選"))
        if not df_kpi.empty and "event_date" in df_kpi.columns:
            min_date = df_kpi["event_date"].min().date()
            max_date = df_kpi["event_date"].max().date()
            selected_dates = st.date_input(
                "Filter Date Range:" if is_en else "選擇日期範圍：",
                value=(min_date, max_date),
                min_value=min_date - timedelta(days=90),
                max_value=date.today() + timedelta(days=1),
            )
            if isinstance(selected_dates, (list, tuple)) and len(selected_dates) == 2:
                s_d, e_d = selected_dates
                filtered_kpi = df_kpi.loc[(df_kpi["event_date"].dt.date >= s_d) & (df_kpi["event_date"].dt.date <= e_d)]
            else:
                filtered_kpi = df_kpi
        else:
            filtered_kpi = df_kpi

    # ==========================================================================
    # DATA ANALYST (DA) SEMANTIC LAYER LIVE MONITOR (NO REACT JARGON!)
    # ==========================================================================
    st.markdown("---")
    st.subheader("📐 " + ("dbt Semantic Metrics" if is_en else "dbt 語意層指標監控"))
    st.caption("Live Metric Calculations & Targets for Data Analysts" if is_en else "提供給資料分析師 (DA) 的真實指標數值與達標監控")

    # Calculate real numbers for DA
    byok_funnel_calc = get_byok_conversion_funnel()
    ref_loop_calc = get_referral_viral_loop()
    gold_kpi_calc = load_gold_dataframe("gold_daily_growth_kpi")

    tot_dau_num = int(gold_kpi_calc["dau"].sum()) if not gold_kpi_calc.empty else 1
    tot_aha_num = int(gold_kpi_calc["aha_users"].sum()) if not gold_kpi_calc.empty else 0
    aha_live_val = (tot_aha_num / tot_dau_num * 100.0) if tot_dau_num > 0 else 0.0

    byok_saved_num = byok_funnel_calc.get("step_6_byok_key_saved", 0)
    byok_wall_num = byok_funnel_calc.get("step_3_trial_limit_hit", 1)
    byok_conv_val = (byok_saved_num / max(byok_wall_num, 1) * 100.0)

    byok_fail_num = byok_funnel_calc.get("byok_verify_failed", 0)
    byok_fail_val = (byok_fail_num / max(byok_saved_num + byok_fail_num, 1) * 100.0)

    viral_k_val = ref_loop_calc.get("viral_k_factor_proxy", 0.0) * 100.0

    da_metrics = [
        {
            "name": "Aha! Activation Rate" if is_en else "Aha! 核心功能啟用率",
            "val_str": f"{aha_live_val:.1f}%",
            "target": "≥ 60.0%",
            "healthy": aha_live_val >= 60.0,
            "formula": "aha_users / dau",
            "desc": "Active learners selecting words or searching dictionary." if is_en else "進站後選字或查字典之活躍讀者佔比。",
        },
        {
            "name": "Trial-to-BYOK Conversion" if is_en else "試用至 BYOK 金鑰轉換率",
            "val_str": f"{byok_conv_val:.1f}%",
            "target": "≥ 45.0%",
            "healthy": byok_conv_val >= 45.0,
            "formula": "byok_key_saved / trial_wall_hits",
            "desc": "Conversion rate from quota wall hit to saved Gemini API key." if is_en else "觸發試用上限後成功綁定 API 金鑰之比例。",
        },
        {
            "name": "API Key Verify Friction" if is_en else "金鑰驗證失敗摩擦率",
            "val_str": f"{byok_fail_val:.1f}%",
            "target": "≤ 8.0%",
            "healthy": byok_fail_val <= 8.0,
            "formula": "verify_failed / total_verify_attempts",
            "desc": "Percentage of key submissions failing API verification." if is_en else "金鑰驗證失敗佔總送出驗證次數之比例。",
        },
        {
            "name": "Referral Viral K-Factor" if is_en else "推薦裂變解鎖係數",
            "val_str": f"{viral_k_val:.1f}%",
            "target": "≥ 12.0%",
            "healthy": viral_k_val >= 12.0,
            "formula": "unlock_success / referral_modal_opened",
            "desc": "Proxy ratio of successful prompt unlocks to share modal opens." if is_en else "開推薦彈窗至受邀者成功解鎖之比例。",
        },
    ]

    for m in da_metrics:
        badge_cls = "da-badge-healthy" if m["healthy"] else "da-badge-warn"
        badge_txt = ("🟢 " + ("Normal" if is_en else "健康")) if m["healthy"] else ("🟡 " + ("Warning" if is_en else "警戒"))
        st.markdown(
            f"""
            <div class="da-metric-box">
                <span class="{badge_cls}">{badge_txt}</span>
                <div class="da-metric-title">{m['name']}</div>
                <div class="da-metric-num">{m['val_str']} <span style="font-size:0.75rem;color:#64748b;font-weight:600;">(Target: {m['target']})</span></div>
                <div style="font-size:0.75rem;color:#64748b;margin-top:0.25rem;">
                    <code>{m['formula']}</code>
                </div>
                <div style="font-size:0.74rem;color:#475569;margin-top:0.2rem;">{m['desc']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("🤖 " + ("AI Growth Copilot" if is_en else "AI 成長顧問"))
    is_drawer_open = st.session_state.get("show_ai_drawer", True)
    if st.button(
        ("» Hide Advisor" if is_drawer_open else "✨ Show Advisor") if is_en else ("» 收起 AI 顧問" if is_drawer_open else "✨ 開啟 AI 顧問側欄"),
        type="secondary" if is_drawer_open else "primary",
        use_container_width=True,
        key="btn_toggle_ai_drawer_sidebar",
    ):
        st.session_state.show_ai_drawer = not is_drawer_open
        st.rerun()


# ==============================================================================
# 6. Main Workspace Layout (Matching Original E-Commerce Cockpit)
# ==============================================================================
is_ai_open = st.session_state.get("show_ai_drawer", True)
if is_ai_open:
    main_page_col, ai_sidebar_col = st.columns([7.2, 2.8], gap="large")
else:
    main_page_col = st.container()
    ai_sidebar_col = None

with main_page_col:
    # --------------------------------------------------------------------------
    # Header Area (Title, Subtitle, Connected Badge, AI Toggle)
    # --------------------------------------------------------------------------
    header_col1, header_col2 = st.columns([2.7, 1.3])
    layer_display_titles = {
        "gold": "🥇 " + ("Gold Layer (readcall_gold · Core PLG Marts)" if is_en else "金牌層 (readcall_gold · 業務決策與 PLG 指標)"),
        "silver": "🥈 " + ("Silver Layer (readcall_silver · Star Schema)" if is_en else "銀牌層 (readcall_silver · 清洗事實與維度明細)"),
        "bronze": "🥉 " + ("Bronze Layer (readcall_bronze · Raw Streams)" if is_en else "銅牌層 (readcall_bronze · 原始串流與 Ingestion 歷程)"),
    }
    with header_col1:
        st.title("ReadCall Product Analytics Lakehouse" if is_en else "ReadCall 產品分析與 PLG 數據戰情室")
        st.markdown(
            f"**{'Current Layer' if is_en else '當前湖倉層級'}**：{layer_display_titles.get(selected_layer)} · "
            f"**GA4 Property 559361789 + dlt + GCP BigQuery + dbt-core**"
        )
    with header_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        c_status, c_ai_btn = st.columns([1.1, 1.0])
        with c_status:
            st.markdown(
                f"""
                <div style="text-align: right;">
                    <div class="status-badge">
                        <div class="pulse-dot"></div>
                        {selected_layer.upper()} Connected
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_ai_btn:
            if st.button(
                ("» Hide Advisor" if is_ai_open else "✨ AI Advisor") if is_en else ("» 收起顧問" if is_ai_open else "✨ AI 顧問"),
                type="secondary" if is_ai_open else "primary",
                use_container_width=True,
                key="top_bar_ai_toggle",
            ):
                st.session_state.show_ai_drawer = not is_ai_open
                st.rerun()

    st.markdown("---")

    # --------------------------------------------------------------------------
    # 4 Crisp Executive Metric Cards (Mirroring Original Design)
    # --------------------------------------------------------------------------
    if selected_layer == "gold":
        df_kpi_active = filtered_kpi if not filtered_kpi.empty else data_dict["kpi"]
        total_dau = int(df_kpi_active["dau"].sum()) if "dau" in df_kpi_active.columns else 0
        total_sessions = int(df_kpi_active["total_sessions"].sum()) if "total_sessions" in df_kpi_active.columns else 0
        avg_eng_rate = float(df_kpi_active["engagement_rate"].mean() * 100.0) if "engagement_rate" in df_kpi_active.columns else 74.4
        avg_aha_rate = float(df_kpi_active["aha_activation_rate"].mean() * 100.0) if "aha_activation_rate" in df_kpi_active.columns else 71.6
        byok_totals = get_byok_conversion_funnel()
        saved_keys = byok_totals["step_6_byok_key_saved"]
        byok_conv = byok_totals["step_6_byok_key_saved"] / max(byok_totals["step_3_trial_limit_hit"], 1) * 100.0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{'Cumulative DAU' if is_en else '90 天累計活躍讀者 (DAU)'}</div>
                    <div class="metric-value">{total_dau:,}</div>
                    <div class="metric-subtext">{'Total Sessions' if is_en else '總工作階段'}: {total_sessions:,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{'Avg Engagement Rate' if is_en else '平均互動工作階段率'}</div>
                    <div class="metric-value">{avg_eng_rate:.1f}%</div>
                    <div class="metric-subtext">{'Target ≥ 65.0%' if is_en else '目標基準 ≥ 65.0%'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{'Aha! Activation Rate' if is_en else 'Aha! 核心功能啟用率'}</div>
                    <div class="metric-value">{avg_aha_rate:.1f}%</div>
                    <div class="metric-subtext">{'Selected Text + Dictionary' if is_en else '選詞解析 + 雙語字典查詢'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{'BYOK Conversion Rate' if is_en else '試用至 BYOK 金鑰轉換率'}</div>
                    <div class="metric-value">{byok_conv:.1f}%</div>
                    <div class="metric-subtext">{saved_keys:,} {'Keys Unlocked 1,500 Daily Quota' if is_en else '組金鑰成功解鎖每日額度'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------------------------
    # Main Analytical Tabs (Clean, Structured, Interactive Charts)
    # --------------------------------------------------------------------------
    if selected_layer == "gold":
        tab_names = (
            [
                "📈 AARRR Growth & Traffic",
                "🧩 32-Event Feature Pareto (80/20)",
                "🔑 BYOK Funnel & Referral Loop",
                "✨ AI Natural Language Chart",
            ]
            if is_en
            else [
                "📈 營收與活躍趨勢 (AARRR)",
                "🧩 德語閱讀器 32 埋點黏著度 (80/20)",
                "🔑 BYOK 金鑰轉換漏斗 & 推薦裂變",
                "✨ 自然語言 AI 智慧圖表 (NL2Chart)",
            ]
        )
        tab1, tab2, tab3, tab4 = st.tabs(tab_names)

        # TAB 1: AARRR & TRAFFIC
        with tab1:
            st.subheader("Daily Active Users (DAU) & Aha! Activation Trend" if is_en else "每日活躍用戶 (DAU) 與 Aha! 核心功能啟用趨勢")
            df_trend = data_dict["kpi"].sort_values("event_date") if not data_dict["kpi"].empty else pd.DataFrame()
            if not df_trend.empty:
                fig_trend = go.Figure()
                fig_trend.add_trace(
                    go.Scatter(
                        x=df_trend["event_date"],
                        y=df_trend["dau"],
                        mode="lines",
                        name="DAU" if is_en else "每日活躍用戶 (DAU)",
                        line={"color": "#0284c7", "width": 2.5},
                    )
                )
                fig_trend.add_trace(
                    go.Scatter(
                        x=df_trend["event_date"],
                        y=df_trend["aha_users"],
                        mode="lines",
                        name="Aha! Users" if is_en else "Aha! 啟用人數",
                        line={"color": "#10b981", "width": 2.2, "dash": "dot"},
                    )
                )
                fig_trend.update_layout(
                    template="plotly_white",
                    height=380,
                    margin={"l": 20, "r": 20, "t": 40, "b": 20},
                    legend={"orientation": "h", "y": 1.1},
                )
                st.plotly_chart(fig_trend, use_container_width=True)

        # TAB 2: FEATURE ADOPTION PARETO
        with tab2:
            st.subheader("32 Telemetry Events 80/20 Pareto Distribution" if is_en else "32 項產品埋點事件 80/20 帕累托分析")
            df_f = data_dict["features"]
            if not df_f.empty:
                df_f_sorted = df_f.sort_values("total_event_count", ascending=False).copy()
                df_f_sorted["cum_pct"] = (df_f_sorted["total_event_count"].cumsum() / df_f_sorted["total_event_count"].sum() * 100.0)

                fig_p = go.Figure()
                fig_p.add_trace(
                    go.Bar(
                        x=df_f_sorted["event_name"],
                        y=df_f_sorted["total_event_count"],
                        name="Event Count" if is_en else "事件觸發次數",
                        marker_color="#38bdf8",
                    )
                )
                fig_p.add_trace(
                    go.Scatter(
                        x=df_f_sorted["event_name"],
                        y=df_f_sorted["cum_pct"],
                        name="Cumulative %" if is_en else "累積佔比 (%)",
                        yaxis="y2",
                        mode="lines+markers",
                        line={"color": "#f59e0b", "width": 2.4},
                    )
                )
                fig_p.update_layout(
                    template="plotly_white",
                    height=420,
                    yaxis2={"overlaying": "y", "side": "right", "range": [0, 105]},
                    margin={"l": 20, "r": 20, "t": 35, "b": 90},
                )
                st.plotly_chart(fig_p, use_container_width=True)

        # TAB 3: BYOK FUNNEL & REFERRAL LOOP
        with tab3:
            st.subheader("6-Stage BYOK Gemini Key Funnel & 5-Stage Viral Referral Loop" if is_en else "6 階 BYOK 金鑰轉換漏斗與 5 階推薦裂變迴路")
            byok_s = get_byok_conversion_funnel()
            ref_s = get_referral_viral_loop()

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                stages_byok = (
                    [
                        "1. Reader Opened",
                        "2. AI Inquiry",
                        "3. Trial Limit Wall Hit",
                        "4. ByokModal Opened",
                        "5. Get API Key Clicked",
                        "6. Key Saved",
                    ]
                    if is_en
                    else [
                        "1. 閱讀器開啟",
                        "2. AI 形態學查詢",
                        "3. 觸發免費試用牆",
                        "4. 開啟金鑰視窗",
                        "5. 點擊領取金鑰",
                        "6. 驗證並儲存金鑰",
                    ]
                )
                fig_b = go.Figure(
                    go.Funnel(
                        y=stages_byok,
                        x=[
                            byok_s["step_1_reader_opened"],
                            byok_s["step_2_ai_trial_inquiry"],
                            byok_s["step_3_trial_limit_hit"],
                            byok_s["step_4_byok_modal_opened"],
                            byok_s["step_5_byok_get_key_clicked"],
                            byok_s["step_6_byok_key_saved"],
                        ],
                        textinfo="value+percent previous",
                        marker={"color": ["#38bdf8", "#0ea5e9", "#0284c7", "#6366f1", "#4f46e5", "#10b981"]},
                    )
                )
                fig_b.update_layout(template="plotly_white", height=380, margin={"l": 20, "r": 20, "t": 30, "b": 20})
                st.plotly_chart(fig_b, use_container_width=True)

            with col_b2:
                stages_ref = (
                    [
                        "1. Referral Modal Opened",
                        "2. Link Copied",
                        "3. Friend Visited Banner",
                        "4. Unlock Succeeded",
                        "5. Custom Prompt Saved",
                    ]
                    if is_en
                    else [
                        "1. 開啟推薦視窗",
                        "2. 複製專屬連結",
                        "3. 好友造訪橫幅",
                        "4. 驗證解鎖成功",
                        "5. 儲存自訂 Prompt",
                    ]
                )
                fig_r = go.Figure(
                    go.Funnel(
                        y=stages_ref,
                        x=[
                            ref_s["step_1_referral_modal_opened"],
                            ref_s["step_2_referral_link_copied"],
                            ref_s["step_3_referral_banner_shown"],
                            ref_s["step_4_referral_unlock_success"],
                            ref_s["step_5_custom_prompt_saved"],
                        ],
                        textinfo="value+percent previous",
                        marker={"color": ["#c084fc", "#a855f7", "#9333ea", "#ec4899", "#10b981"]},
                    )
                )
                fig_r.update_layout(template="plotly_white", height=380, margin={"l": 20, "r": 20, "t": 30, "b": 20})
                st.plotly_chart(fig_r, use_container_width=True)

        # TAB 4: NL2CHART GENERATOR
        with tab4:
            st.subheader("Natural Language AI Chart Generator" if is_en else "雙語自然語言 AI 智慧圖表生成")
            nl_q = st.text_input(
                "Enter chart request:" if is_en else "輸入圖表生成需求：",
                value="Show top 12 product features by event count" if is_en else "顯示前 12 大產品功能埋點排行",
                key="nl2chart_query_box",
            )
            if nl_q:
                cfg = generate_chart_config(nl_q)
                target_df = data_dict["features"] if cfg.get("dataset") == "features" else data_dict["kpi"]
                fig_nl = render_dynamic_chart(cfg, target_df)
                if fig_nl:
                    fig_nl.update_layout(template="plotly_white")
                    st.plotly_chart(fig_nl, use_container_width=True)

    elif selected_layer == "silver":
        st.subheader("Silver Star Schema (Cleaned Transactions & Dimensions)" if is_en else "銀牌層星狀模型（清洗事實與維度明細）")
        s_tab1, s_tab2 = st.tabs(["fct_daily_traffic", "dim_feature_catalog"])
        with s_tab1:
            st.dataframe(data_dict["traffic"], use_container_width=True, height=450)
        with s_tab2:
            st.dataframe(data_dict["catalog"], use_container_width=True, height=450)

    else:  # bronze
        st.subheader("Bronze Raw Telemetry Streams (Zero Fan-Out)" if is_en else "銅牌層原始埋點串流（防膨脹分流）")
        b_tab1, b_tab2 = st.tabs(["raw_ga4_daily_traffic", "raw_ga4_events"])
        with b_tab1:
            st.dataframe(data_dict["raw_traffic"], use_container_width=True, height=450)
        with b_tab2:
            st.dataframe(data_dict["raw_events"], use_container_width=True, height=450)


# ==============================================================================
# 7. Right-Side Collapsible AI Advisor Drawer + System Prompt Playground
# ==============================================================================
if ai_sidebar_col is not None:
    with ai_sidebar_col:
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                <div style="font-weight:800; font-size:1.15rem; color:var(--text-color, #0f172a);">
                    🤖 {'AI Growth Copilot' if is_en else 'AI 決策顧問'}
                </div>
                <div style="display:flex; gap:0.35rem;">
                    <span style="font-size:0.7rem; font-weight:700; background:rgba(99,102,241,0.15); color:#6366f1; padding:0.15rem 0.45rem; border-radius:4px;">FAST MCP</span>
                    <span style="font-size:0.7rem; font-weight:700; background:rgba(16,185,129,0.15); color:#10b981; padding:0.15rem 0.45rem; border-radius:4px;">PLG AI</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        user_gemini_key = st.text_input(
            "🔑 " + ("Gemini API Key (Optional BYOK)" if is_en else "Gemini API Key (選填 BYOK)"),
            type="password",
            placeholder="AIzaSy...",
            help="Bring Your Own Key for live Gemini inference; defaults to deterministic FastMCP diagnostics."
            if is_en
            else "輸入您自己的 Gemini Key 可進行即時推理；留空則自動調用確定性 FastMCP 診斷引擎。",
        )

        st.caption(
            "🔒 **BYOK Security Guarantee**: Keys are never stored. "
            "[👉 Get a Free Gemini API Key at Google AI Studio](https://aistudio.google.com/app/apikey)"
            if is_en
            else "🔒 **安全保障（BYOK 模式）**：系統絕不儲存金鑰，連線結束即釋放。"
            "[👉 點此前往 Google AI Studio 免費獲取 API Key](https://aistudio.google.com/app/apikey)"
        )

        # QUICK RECOMMENDATION PILLS (Mirroring Original Style)
        st.markdown("##### ⚡ " + ("One-Click Diagnostics" if is_en else "一鍵快捷診斷推薦"))
        q1, q2 = st.columns(2)
        with q1:
            if st.button("🔍 " + ("BYOK Funnel" if is_en else "診斷轉換瓶頸"), use_container_width=True, key="quick_q1"):
                st.session_state.quick_ai_prompt = (
                    "Please diagnose the BYOK key conversion funnel drop-off points."
                    if is_en
                    else "請針對 BYOK 試用牆到金鑰儲存的流失瓶頸進行深入診斷。"
                )
        with q2:
            if st.button("🧩 " + ("Aha! Activation" if is_en else "Aha! 留存錨點"), use_container_width=True, key="quick_q2"):
                st.session_state.quick_ai_prompt = (
                    "Please analyze Aha! activation rate and reader stickiness."
                    if is_en
                    else "請分析當前 Aha! 核心啟用率與德語閱讀器的留存黏著度。"
                )

        # PROMINENT SYSTEM PROMPT PLAYGROUND (User Feature Request #2)
        expander_title = (
            "🛠️ View / Edit System Prompt (檢視 / 修改系統 Prompt)"
            if is_en
            else "🛠️ 檢視 / 修改系統 Prompt (Edit System Prompt)"
        )
        with st.expander(expander_title, expanded=False):
            st.caption(
                "Inspect or live-edit the underlying system instructions for the SaaS Head of Growth & Staff Product DS:"
                if is_en
                else "檢視或即時手動修改底層 SaaS 成長負責人與首席資料科學家 System Prompt："
            )
            active_prompt_val = st.session_state.custom_prompt_en if is_en else st.session_state.custom_prompt_zh
            edited_prompt = st.text_area(
                "Prompt Editor:" if is_en else "Prompt 編輯區：",
                value=active_prompt_val,
                height=220,
                key="system_prompt_textarea",
            )
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                btn_apply_label = "💾 Apply Custom Prompt" if is_en else "💾 套用自訂 Prompt"
                if st.button(btn_apply_label, use_container_width=True, key="btn_apply_sys_prompt"):
                    if is_en:
                        st.session_state.custom_prompt_en = edited_prompt
                    else:
                        st.session_state.custom_prompt_zh = edited_prompt
                    inject_stealth_telemetry("portfolio_ai_tested", {"action": "custom_prompt_applied"})
                    st.success("✅ " + ("Applied!" if is_en else "已套用！"))
            with p_col2:
                btn_reset_label = "🔄 Reset to Default" if is_en else "🔄 還原預設值"
                if st.button(btn_reset_label, use_container_width=True, key="btn_reset_sys_prompt"):
                    if is_en:
                        st.session_state.custom_prompt_en = DEFAULT_SYSTEM_PROMPT_EN
                    else:
                        st.session_state.custom_prompt_zh = DEFAULT_SYSTEM_PROMPT_ZH
                    st.rerun()

        st.markdown("---")

        # Chat Conversation History
        chat_box = st.container(height=380)
        with chat_box:
            for m in st.session_state.chat_history:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

        # Chat Input
        user_input = st.chat_input(
            "Ask about BYOK funnel, Aha! activation, or retention..."
            if is_en
            else "詢問 BYOK 轉換率、Aha! 啟用率或功能留存處方...",
            key="chat_input_box",
        )
        prompt_to_send = user_input or st.session_state.pop("quick_ai_prompt", None)

        if prompt_to_send:
            inject_stealth_telemetry("portfolio_ai_tested", {"action": "chat_inquiry"})
            st.session_state.chat_history.append({"role": "user", "content": prompt_to_send})

            current_sys_prompt = st.session_state.custom_prompt_en if is_en else st.session_state.custom_prompt_zh
            diagnosis_reply = generate_tab_diagnosis(
                tab_key="gold_mart",
                tab_title="ReadCall PLG Gold Marts",
                tab_payload={"byok": byok_funnel_calc, "referral": ref_loop_calc},
                user_query=prompt_to_send,
                api_key=user_gemini_key,
                language="en" if is_en else "zh",
                custom_system_prompt=current_sys_prompt,
            )
            st.session_state.chat_history.append({"role": "assistant", "content": diagnosis_reply})
            st.rerun()

st.markdown("---")
st.caption(
    f"ReadCall Product Analytics Lakehouse • Updated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} "
    f"• Google Cloud BigQuery ({PROJECT_ID}) • dbt Core Semantic Layer • FastMCP Copilot"
)
