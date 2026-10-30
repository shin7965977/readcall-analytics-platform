"""ReadCall Product Analytics Lakehouse & AI Growth Cockpit.

SaaS Product Analytics, PLG Medallion Lakehouse & AI Growth Copilot for ReadCall (https://readcall.app).
Bilingual (English default, Traditional Chinese), responsive 4-card KPI grid with top accent highlights,
3-layer Medallion switcher (Gold, Silver, Bronze), interactive System Prompt Editor,
DA-tailored Semantic Metric live monitor, and 0px stealth recruiter telemetry.
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pandas as pd
import plotly.express as px
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
# 1. Page Configuration & Modern Executive BI Design System
# ==============================================================================
st.set_page_config(
    page_title="ReadCall Product Analytics Lakehouse",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Executive CSS for modern SaaS BI aesthetic
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    /* Executive Metric Cards */
    .metric-card {
        background: var(--secondary-background-color, #ffffff);
        border: 1px solid rgba(226, 232, 240, 0.9);
        border-radius: 16px;
        padding: 1.35rem 1.6rem;
        box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
        margin-bottom: 1.1rem;
        position: relative;
        overflow: hidden;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 28px -4px rgba(15, 23, 42, 0.1);
        border-color: rgba(59, 130, 246, 0.4);
    }
    .metric-card-blue { border-top: 4px solid #2563eb; }
    .metric-card-emerald { border-top: 4px solid #10b981; }
    .metric-card-indigo { border-top: 4px solid #6366f1; }
    .metric-card-amber { border-top: 4px solid #f59e0b; }

    .metric-label {
        font-size: 0.8rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.35rem;
    }
    .metric-value {
        font-size: 2.3rem;
        font-weight: 800;
        color: var(--text-color, #0f172a) !important;
        line-height: 1.15;
        letter-spacing: -0.03em;
        font-variant-numeric: tabular-nums;
        margin-bottom: 0.35rem;
    }
    .metric-subtext-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.775rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        background: rgba(16, 185, 129, 0.1);
        color: #059669;
    }
    .metric-subtext-pill.info {
        background: rgba(37, 99, 235, 0.1);
        color: #2563eb;
    }
    .metric-subtext-pill.warning {
        background: rgba(245, 158, 11, 0.1);
        color: #d97706;
    }

    /* Header Status Badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 0.95rem;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 9999px;
        color: #059669;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10b981;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.15); }
    }

    /* DA Semantic Card */
    .da-metric-box {
        background: var(--secondary-background-color, #ffffff);
        border: 1px solid rgba(226, 232, 240, 0.9);
        border-left: 3.5px solid #0284c7;
        border-radius: 12px;
        padding: 0.9rem 1.05rem;
        margin-bottom: 0.8rem;
        transition: transform 0.2s ease;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }
    .da-metric-box:hover {
        transform: translateY(-2px);
        border-left-color: #2563eb;
    }
    .da-metric-title {
        font-size: 0.825rem;
        font-weight: 700;
        color: #0369a1;
        margin-bottom: 0.2rem;
    }
    .da-metric-num {
        font-size: 1.4rem;
        font-weight: 800;
        color: var(--text-color, #0f172a);
        font-variant-numeric: tabular-nums;
    }
    .da-badge-healthy {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.18rem 0.55rem;
        background: rgba(16, 185, 129, 0.12);
        color: #059669;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        float: right;
    }
    .da-badge-warn {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.18rem 0.55rem;
        background: rgba(245, 158, 11, 0.15);
        color: #b45309;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        float: right;
    }
    .formula-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.73rem;
        background: rgba(241, 245, 249, 0.9);
        color: #475569;
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
        display: inline-block;
        margin-top: 0.25rem;
    }

    /* Clean, compact Chat message typography (Prevent oversized headers) */
    [data-testid="stChatMessage"] h1,
    [data-testid="stChatMessage"] h2,
    [data-testid="stChatMessage"] h3,
    [data-testid="stChatMessage"] h4 {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        margin-top: 0.55rem !important;
        margin-bottom: 0.25rem !important;
        line-height: 1.35 !important;
        color: var(--text-color, #0f172a) !important;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li {
        font-size: 0.86rem !important;
        line-height: 1.55 !important;
        color: var(--text-color, #1e293b) !important;
    }
    [data-testid="stChatMessage"] ul {
        margin-top: 0.2rem !important;
        margin-bottom: 0.45rem !important;
        padding-left: 1.15rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. Global Constants & Data Loaders
# ==============================================================================
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "de-consulting-508822")
KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", os.path.abspath("gcp-key.json"))
if os.path.exists(KEY_PATH):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH


@st.cache_data(ttl=600, show_spinner=False)
def cached_load_gold_dataframe(table_name: str) -> pd.DataFrame:
    """Cached loader for BigQuery / DuckDB Gold and Silver tables."""
    return load_gold_dataframe(table_name)


@st.cache_data(ttl=600, show_spinner=False)
def cached_byok_conversion_funnel() -> dict[str, Any]:
    """Cached aggregate of 6-stage BYOK funnel metrics."""
    return get_byok_conversion_funnel()


@st.cache_data(ttl=600, show_spinner=False)
def cached_referral_viral_loop() -> dict[str, Any]:
    """Cached aggregate of 5-stage referral loop metrics."""
    return get_referral_viral_loop()


@st.cache_data(ttl=600)
def load_cockpit_datasets() -> dict[str, pd.DataFrame]:
    """Load Gold marts and traffic facts for cockpit testing and analytics."""
    data = load_lakehouse_data("gold")
    data["traffic"] = cached_load_gold_dataframe("fct_daily_traffic")
    return data


@st.cache_data(ttl=600)
def load_lakehouse_data(layer: str) -> dict[str, pd.DataFrame]:
    """Load tables for Gold, Silver, or Bronze layers seamlessly."""
    if layer == "gold":
        df_kpi = cached_load_gold_dataframe("gold_daily_growth_kpi")
        df_f = cached_load_gold_dataframe("gold_feature_adoption")
        df_byok = cached_load_gold_dataframe("gold_byok_funnel")
        df_ref = cached_load_gold_dataframe("gold_referral_loop")
        if "event_date" in df_kpi.columns:
            df_kpi["event_date"] = pd.to_datetime(df_kpi["event_date"])
        if "event_date" in df_byok.columns:
            df_byok["event_date"] = pd.to_datetime(df_byok["event_date"])
        if "event_date" in df_ref.columns:
            df_ref["event_date"] = pd.to_datetime(df_ref["event_date"])
        return {"kpi": df_kpi, "features": df_f, "byok": df_byok, "referral": df_ref}
    elif layer == "silver":
        df_traffic = cached_load_gold_dataframe("fct_daily_traffic")
        df_f_events = cached_load_gold_dataframe("fct_feature_events")
        df_catalog = cached_load_gold_dataframe("dim_feature_catalog")
        return {"traffic": df_traffic, "feature_events": df_f_events, "catalog": df_catalog}
    else:  # bronze
        from ingestion.sources.ga4_adapter import GA4TelemetryConfig, ReadCallGA4Adapter

        adapter = ReadCallGA4Adapter(GA4TelemetryConfig(days=30, raw_mode=False))
        raw = adapter.extract_telemetry()
        return {
            "raw_traffic": pd.DataFrame(raw["raw_ga4_daily_traffic"]),
            "raw_events": pd.DataFrame(raw["raw_ga4_events"]),
        }


def main():
    if "lang" not in st.session_state:
        qp_lang = st.query_params.get("lang", "").lower()
        st.session_state["lang"] = "zh" if qp_lang in ("zh", "tw", "cn") else "en"

    is_en = st.session_state["lang"] == "en"

    # Inject stealth 0px recruiter telemetry
    inject_stealth_telemetry("portfolio_opened", {"cockpit_lang": st.session_state["lang"]})

    # ==============================================================================
    # 3. Session State Defaults
    # ==============================================================================
    if "show_ai_drawer" not in st.session_state:
        st.session_state.show_ai_drawer = True
    if "custom_prompt_en" not in st.session_state:
        st.session_state.custom_prompt_en = DEFAULT_SYSTEM_PROMPT_EN
    if "custom_prompt_zh" not in st.session_state:
        st.session_state.custom_prompt_zh = DEFAULT_SYSTEM_PROMPT_ZH
    if "chat_history" not in st.session_state:
        initial_msg = (
            "Hello! I am your **ReadCall GA4 Product Analytics Assistant**.\n\n"
            "I am connected to authentic GA4 telemetry and the BigQuery lakehouse. "
            "Ask me about daily traffic (e.g. *What was the traffic on 10/29?*), page views, BYOK API Key conversions, or acquisition channels!"
            if is_en
            else "您好！我是 **ReadCall GA4 產品數據助理**。\n\n"
            "我已連線至真實 GA4 遙測日誌與 BigQuery 湖倉。您可以隨時詢問我每日人流（例如：*10/29 有多少人流？*）、熱門頁面、BYOK 金鑰轉換情況或訪客來源管道！"
        )
        st.session_state.chat_history = [{"role": "assistant", "content": initial_msg}]

    # ==============================================================================
    # 4. Sidebar Navigation & Global Filters (Clean & De-cluttered)
    # ==============================================================================
    with st.sidebar:
        # Language Switcher (English Default)
        lang_options = ["English", "繁體中文"]
        curr_idx = 0 if is_en else 1
        selected_lang_str = st.radio(
            "🌐 Language" if is_en else "🌐 語言切換",
            options=lang_options,
            index=curr_idx,
            horizontal=True,
            key="global_language_radio",
        )
        new_lang_code = "en" if selected_lang_str == "English" else "zh"
        if new_lang_code != st.session_state["lang"]:
            st.session_state["lang"] = new_lang_code
            st.query_params["lang"] = new_lang_code
            if len(st.session_state.get("chat_history", [])) <= 1:
                st.session_state.chat_history = []
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
        st.caption(f"🔒 {'Connected: ' if is_en else '連線資料庫：'}`{data_source_str}`")

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

        # ======================================================================
        # DATA ANALYST (DA) SEMANTIC LAYER LIVE MONITOR (Clean & Actionable)
        # ======================================================================
        st.markdown("---")
        st.subheader("📐 " + ("dbt Semantic Metrics" if is_en else "dbt 語意層指標監控"))
        st.caption("Live Metric Calculations & Targets for Data Analysts" if is_en else "提供給資料分析師 (DA) 的真實指標數值與達標監控")

        byok_funnel_calc = cached_byok_conversion_funnel()
        ref_loop_calc = cached_referral_viral_loop()
        gold_kpi_calc = cached_load_gold_dataframe("gold_daily_growth_kpi")

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
                    <div class="da-metric-num">{m['val_str']} <span style="font-size:0.75rem;color:#64748b;font-weight:600;">({'Target: ' if is_en else '目標: '}{m['target']})</span></div>
                    <div style="margin-top:0.25rem;">
                        <span class="formula-tag">{m['formula']}</span>
                    </div>
                    <div style="font-size:0.74rem;color:#64748b;margin-top:0.35rem;line-height:1.35;">{m['desc']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ==============================================================================
    # 5. Main Workspace Layout & BI Visuals
    # ==============================================================================
    is_ai_open = st.session_state.get("show_ai_drawer", True)
    if is_ai_open:
        main_page_col, ai_sidebar_col = st.columns([7.2, 2.8], gap="large")
    else:
        main_page_col = st.container()
        ai_sidebar_col = None

    with main_page_col:
        # Header Area
        header_col1, header_col2 = st.columns([2.7, 1.3])
        layer_display_titles = {
            "gold": "🥇 " + ("Gold Layer (readcall_gold · Core PLG Marts)" if is_en else "金牌層 (readcall_gold · 業務決策與 PLG 指標)"),
            "silver": "🥈 " + ("Silver Layer (readcall_silver · Star Schema)" if is_en else "銀牌層 (readcall_silver · 清洗事實與維度明細)"),
            "bronze": "🥉 " + ("Bronze Layer (readcall_bronze · Raw Streams)" if is_en else "銅牌層 (readcall_bronze · 原始串流與 Ingestion 歷程)"),
        }
        with header_col1:
            st.title("ReadCall Product Analytics Lakehouse" if is_en else "ReadCall 產品分析與 PLG 數據戰情室")
            st.markdown(
                f"**{'Current Layer: ' if is_en else '當前湖倉層級：'}**{layer_display_titles.get(selected_layer)} · "
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

        # Privacy & Weighted Scaling Notice (Business Confidentiality Protection)
        st.info(
            "🔒 **Data Privacy & Calibration Notice**: To safeguard production business confidentiality, "
            "all volume metrics (DAU, sessions, event counts) displayed in this public demonstration cockpit "
            "have been desensitized via proprietary weighting calibrations. Time-series trends, retention curves, "
            "and 32-event distribution ratios reflect genuine ReadCall GA4 telemetry patterns; absolute numbers do not reflect unadjusted operational scale."
            if is_en
            else "🔒 **商業隱私與展示加權說明**：為維護線上生產環境商業機密，本公開展示戰情室呈現之絕對規模數值"
            "（DAU、工作階段、事件次數）均已完成去識別化商業加權校準，僅供架構展示，不代表未經調整之原始營運數字。"
            "時間序列趨勢波形、相對留存曲線與 32 項埋點行為特徵則真實反映 ReadCall GA4 歷史遙測數據。"
        )

        # ----------------------------------------------------------------------
        # 4 Color-Accented Executive Metric Cards (Redesigned BI Visuals)
        # ----------------------------------------------------------------------
        if selected_layer == "gold":
            df_kpi_active = filtered_kpi if not filtered_kpi.empty else data_dict["kpi"]
            total_dau = int(df_kpi_active["dau"].sum()) if "dau" in df_kpi_active.columns else 0
            total_sessions = int(df_kpi_active["total_sessions"].sum()) if "total_sessions" in df_kpi_active.columns else 0
            avg_eng_rate = float(df_kpi_active["engagement_rate"].mean() * 100.0) if "engagement_rate" in df_kpi_active.columns else 74.4
            avg_aha_rate = float(df_kpi_active["aha_activation_rate"].mean() * 100.0) if "aha_activation_rate" in df_kpi_active.columns else 71.6
            byok_totals = cached_byok_conversion_funnel()
            saved_keys = byok_totals["step_6_byok_key_saved"]
            byok_conv = byok_totals["step_6_byok_key_saved"] / max(byok_totals["step_3_trial_limit_hit"], 1) * 100.0

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(
                    f"""
                    <div class="metric-card metric-card-blue">
                        <div class="metric-label">{'Cumulative DAU' if is_en else '90 天累計活躍讀者 (DAU)'}</div>
                        <div class="metric-value">{total_dau:,}</div>
                        <div class="metric-subtext-pill info">📈 {'Total Sessions' if is_en else '總工作階段'}: {total_sessions:,}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f"""
                    <div class="metric-card metric-card-emerald">
                        <div class="metric-label">{'Avg Engagement Rate' if is_en else '平均互動工作階段率'}</div>
                        <div class="metric-value">{avg_eng_rate:.1f}%</div>
                        <div class="metric-subtext-pill">✓ {'Target ≥ 65.0%' if is_en else '目標基準 ≥ 65.0%'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    f"""
                    <div class="metric-card metric-card-indigo">
                        <div class="metric-label">{'Aha! Activation Rate' if is_en else 'Aha! 核心功能啟用率'}</div>
                        <div class="metric-value">{avg_aha_rate:.1f}%</div>
                        <div class="metric-subtext-pill">⚡ {'Selected Text + Dict' if is_en else '選詞解析 + 雙語字典查詢'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c4:
                st.markdown(
                    f"""
                    <div class="metric-card metric-card-amber">
                        <div class="metric-label">{'BYOK Conversion Rate' if is_en else '試用至 BYOK 金鑰轉換率'}</div>
                        <div class="metric-value">{byok_conv:.1f}%</div>
                        <div class="metric-subtext-pill warning">🔑 {saved_keys:,} {'Keys Unlocked' if is_en else '組金鑰解鎖額度'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # ----------------------------------------------------------------------
        # Main Analytical Tabs with High-Quality BI Charts
        # ----------------------------------------------------------------------
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
                            line={"color": "#2563eb", "width": 2.8, "shape": "spline"},
                            fill="tozeroy",
                            fillcolor="rgba(37, 99, 235, 0.08)",
                        )
                    )
                    fig_trend.add_trace(
                        go.Scatter(
                            x=df_trend["event_date"],
                            y=df_trend["aha_users"],
                            mode="lines",
                            name="Aha! Users" if is_en else "Aha! 啟用人數",
                            line={"color": "#10b981", "width": 2.2, "shape": "spline", "dash": "dot"},
                        )
                    )
                    fig_trend.update_layout(
                        template="plotly_white",
                        height=380,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        hovermode="x unified",
                        margin={"l": 20, "r": 20, "t": 40, "b": 20},
                        legend={"orientation": "h", "y": 1.1},
                        yaxis={"gridcolor": "#f1f5f9"},
                        xaxis={"gridcolor": "#f1f5f9"},
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)

                col_t1, col_t2 = st.columns(2)
                df_traffic = cached_load_gold_dataframe("fct_daily_traffic")
                with col_t1:
                    st.markdown("##### " + ("Acquisition Channel Mix" if is_en else "流量獲取渠道分佈"))
                    if not df_traffic.empty and "channel_group" in df_traffic.columns:
                        ch_agg = df_traffic.groupby("channel_group", as_index=False)["active_users"].sum().sort_values("active_users", ascending=False)
                        fig_ch = px.pie(
                            ch_agg,
                            names="channel_group",
                            values="active_users",
                            hole=0.62,
                            color_discrete_sequence=["#2563eb", "#10b981", "#6366f1", "#f59e0b", "#ec4899"],
                            template="plotly_white",
                        )
                        fig_ch.update_layout(
                            height=300,
                            margin={"l": 10, "r": 10, "t": 20, "b": 10},
                            paper_bgcolor="rgba(0,0,0,0)",
                        )
                        st.plotly_chart(fig_ch, use_container_width=True)
                with col_t2:
                    st.markdown("##### " + ("DACH vs. Global Learners" if is_en else "DACH 德語區 vs. 全球學習者分佈"))
                    if not df_traffic.empty and "country" in df_traffic.columns:
                        geo_agg = df_traffic.groupby("country", as_index=False)["active_users"].sum().sort_values("active_users", ascending=False).head(5)
                        fig_geo = px.bar(
                            geo_agg,
                            x="country",
                            y="active_users",
                            color="country",
                            color_discrete_sequence=["#3b82f6", "#0ea5e9", "#6366f1", "#10b981", "#8b5cf6"],
                            template="plotly_white",
                        )
                        fig_geo.update_layout(
                            height=300,
                            margin={"l": 10, "r": 10, "t": 20, "b": 10},
                            showlegend=False,
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            yaxis={"gridcolor": "#f1f5f9"},
                        )
                        st.plotly_chart(fig_geo, use_container_width=True)

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
                            marker={"color": "#3b82f6", "cornerradius": 4},
                        )
                    )
                    fig_p.add_trace(
                        go.Scatter(
                            x=df_f_sorted["event_name"],
                            y=df_f_sorted["cum_pct"],
                            name="Cumulative %" if is_en else "累積佔比 (%)",
                            yaxis="y2",
                            mode="lines+markers",
                            line={"color": "#f59e0b", "width": 2.6, "shape": "spline"},
                            marker={"size": 6, "color": "#f59e0b"},
                        )
                    )
                    fig_p.update_layout(
                        template="plotly_white",
                        height=420,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        yaxis2={"overlaying": "y", "side": "right", "range": [0, 105], "gridcolor": "rgba(0,0,0,0)"},
                        yaxis={"gridcolor": "#f1f5f9"},
                        margin={"l": 20, "r": 20, "t": 35, "b": 95},
                        legend={"orientation": "h", "y": 1.12},
                    )
                    st.plotly_chart(fig_p, use_container_width=True)

                    st.markdown("##### " + ("Full Feature Telemetry Catalog" if is_en else "完整產品功能埋點目錄明細"))
                    st.dataframe(
                        df_f_sorted[["event_name", "module_category", "aarrr_stage", "total_event_count", "event_share_pct"]],
                        use_container_width=True,
                        height=260,
                    )

            # TAB 3: BYOK FUNNEL & REFERRAL LOOP
            with tab3:
                st.subheader("6-Stage BYOK Gemini Key Funnel & 5-Stage Viral Referral Loop" if is_en else "6 階 BYOK 金鑰轉換漏斗與 5 階推薦裂變迴路")
                byok_s = cached_byok_conversion_funnel()
                ref_s = cached_referral_viral_loop()

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
                            marker={"color": ["#3b82f6", "#2563eb", "#1d4ed8", "#6366f1", "#4f46e5", "#10b981"]},
                        )
                    )
                    fig_b.update_layout(
                        template="plotly_white",
                        height=380,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin={"l": 20, "r": 20, "t": 30, "b": 20},
                    )
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
                    fig_r.update_layout(
                        template="plotly_white",
                        height=380,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin={"l": 20, "r": 20, "t": 30, "b": 20},
                    )
                    st.plotly_chart(fig_r, use_container_width=True)

                # Daily Friction Monitoring
                df_byok = data_dict["byok"]
                if not df_byok.empty:
                    st.markdown("##### " + ("Daily BYOK Key Saves vs. Verification Failures" if is_en else "每日 BYOK 金鑰儲存成功 vs. 驗證失敗摩擦監控"))
                    df_b_sort = df_byok.sort_values("event_date")
                    fig_fric = go.Figure()
                    fig_fric.add_trace(go.Bar(x=df_b_sort["event_date"], y=df_b_sort["step_6_byok_key_saved"], name="Saved Keys" if is_en else "成功儲存金鑰", marker_color="#10b981"))
                    fig_fric.add_trace(go.Bar(x=df_b_sort["event_date"], y=df_b_sort["byok_verify_failed"], name="Verify Failures" if is_en else "驗證失敗摩擦", marker_color="#ef4444"))
                    fig_fric.update_layout(
                        barmode="stack",
                        template="plotly_white",
                        height=280,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin={"l": 20, "r": 20, "t": 20, "b": 20},
                        legend={"orientation": "h", "y": 1.15},
                        yaxis={"gridcolor": "#f1f5f9"},
                    )
                    st.plotly_chart(fig_fric, use_container_width=True)

            # TAB 4: NL2CHART GENERATOR
            with tab4:
                st.subheader("Natural Language AI Chart Generator" if is_en else "雙語自然語言 AI 智慧圖表生成")
                p1, p2, p3 = st.columns(3)
                chosen_preset = ""
                if p1.button("📊 " + ("Top 12 Features" if is_en else "前 12 大功能排行"), use_container_width=True):
                    chosen_preset = "Show top 12 product features by event count" if is_en else "顯示前 12 大產品功能埋點排行"
                if p2.button("🔑 " + ("BYOK Daily Friction" if is_en else "每日 BYOK 驗證失敗趨勢"), use_container_width=True):
                    chosen_preset = "Daily BYOK key saves vs verification failures" if is_en else "分析每日 BYOK 金鑰儲存與驗證失敗趨勢"
                if p3.button("🌱 " + ("Referral Loop Trend" if is_en else "推薦裂變解鎖趨勢"), use_container_width=True):
                    chosen_preset = "Referral link copies and unlock success trend" if is_en else "查看每日推薦連結複製與解鎖趨勢"

                nl_q = st.text_input(
                    "Enter chart request:" if is_en else "輸入圖表生成需求：",
                    value=chosen_preset or ("Show top 12 product features by event count" if is_en else "顯示前 12 大產品功能埋點排行"),
                    key="nl2chart_query_box",
                )
                if nl_q:
                    cfg = generate_chart_config(nl_q)
                    target_df = data_dict["features"] if cfg.get("dataset") == "features" else data_dict["kpi"]
                    fig_nl = render_dynamic_chart(cfg, target_df)
                    if fig_nl:
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
    # 6. Right-Side Collapsible AI Advisor Drawer + System Prompt Playground
    # ==============================================================================
    if ai_sidebar_col is not None:
        with ai_sidebar_col:
            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                    <div style="font-weight:800; font-size:1.15rem; color:var(--text-color, #0f172a);">
                        📊 {'GA4 Analytics Copilot' if is_en else 'GA4 產品數據助理'}
                    </div>
                    <div style="display:flex; gap:0.35rem;">
                        <span style="font-size:0.7rem; font-weight:700; background:rgba(99,102,241,0.15); color:#6366f1; padding:0.15rem 0.45rem; border-radius:4px;">FAST MCP</span>
                        <span style="font-size:0.7rem; font-weight:700; background:rgba(16,185,129,0.15); color:#10b981; padding:0.15rem 0.45rem; border-radius:4px;">GA4 DATA</span>
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

            raw_key_clean = user_gemini_key.strip()
            if raw_key_clean and not (raw_key_clean.startswith("AIzaSy") and len(raw_key_clean) >= 30):
                st.warning(
                    "⚠️ **Invalid Key Format**: Google AI Studio API Keys must start with `AIzaSy`. "
                    "Automatically switching to instant local FastMCP diagnostic engine!"
                    if is_en
                    else "⚠️ **金鑰格式無效**：Google AI Studio API Key 應為 `AIzaSy` 開頭。系統已自動切換為本地 FastMCP 秒級診斷引擎！"
                )
                effective_gemini_key = ""
            else:
                effective_gemini_key = raw_key_clean

            st.caption(
                "🔒 **BYOK Security Guarantee**: Keys are never stored. "
                "[👉 Get a Free Gemini API Key at Google AI Studio](https://aistudio.google.com/app/apikey)"
                if is_en
                else "🔒 **安全保障（BYOK 模式）**：系統絕不儲存金鑰，連線結束即釋放。"
                "[👉 點此前往 Google AI Studio 免費獲取 API Key](https://aistudio.google.com/app/apikey)"
            )

            # QUICK RECOMMENDATION PILLS
            st.markdown("##### ⚡ " + ("One-Click Data Queries" if is_en else "一鍵數據快捷查詢"))
            q1, q2 = st.columns(2)
            with q1:
                if st.button("📊 " + ("10/29 Traffic Report" if is_en else "10/29 人流報告"), use_container_width=True, key="quick_q_traffic"):
                    st.session_state.quick_ai_prompt = (
                        "What was the traffic on 10/29?"
                        if is_en
                        else "10/29 有多少人流？請提供完整流量與轉換報告"
                    )
            with q2:
                if st.button("🔍 " + ("BYOK Funnel" if is_en else "BYOK 金鑰轉換"), use_container_width=True, key="quick_q1"):
                    st.session_state.quick_ai_prompt = (
                        "Please analyze the BYOK key conversion funnel and friction points."
                        if is_en
                        else "請分析 BYOK 金鑰轉換漏斗各階轉化率與驗證摩擦。"
                    )

            # PROMINENT SYSTEM PROMPT PLAYGROUND (User Feature Request #2)
            expander_title = (
                "🛠️ View / Edit System Prompt"
                if is_en
                else "🛠️ 檢視 / 修改系統 Prompt"
            )
            with st.expander(expander_title, expanded=False):
                st.caption(
                    "Inspect or live-edit the underlying system instructions for the GA4 Product Data Analyst:"
                    if is_en
                    else "檢視或即時手動修改底層 GA4 產品數據助理 System Prompt："
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
                "Ask about 10/29 traffic, page views, BYOK conversion..."
                if is_en
                else "詢問 10/29 人流、熱門頁面、BYOK 轉換或來源管道...",
                key="chat_input_box",
            )
            prompt_to_send = user_input or st.session_state.pop("quick_ai_prompt", None)

            if prompt_to_send:
                inject_stealth_telemetry("portfolio_ai_tested", {"action": "chat_inquiry"})
                st.session_state.chat_history.append({"role": "user", "content": prompt_to_send})

                current_sys_prompt = st.session_state.custom_prompt_en if is_en else st.session_state.custom_prompt_zh
                with st.spinner(
                    "🤖 AI is querying BigQuery lakehouse and generating PLG diagnostics..."
                    if is_en
                    else "🤖 AI 正在調用 BigQuery 湖倉數據診斷中..."
                ):
                    diagnosis_reply = generate_tab_diagnosis(
                        tab_key="gold_mart",
                        tab_title="ReadCall PLG Gold Marts",
                        tab_payload={"byok": byok_funnel_calc, "referral": ref_loop_calc},
                        user_query=prompt_to_send,
                        api_key=effective_gemini_key,
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


if __name__ == "__main__":
    main()
