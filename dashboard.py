"""ReadCall 產品分析、PLG 成長實驗室與 AI 成長顧問戰情室 (Traditional Chinese Cockpit).

Standalone SaaS Product Analytics & PLG Lakehouse Dashboard for ReadCall (https://readcall.app).
Features:
1. 4 SaaS PLG Analytical Tabs (AARRR Overview, 32-Event Feature Pareto, 6-Step BYOK & 5-Step Referral Funnels, AI NL2Chart).
2. Interactive System Prompt Playground (`🛠️ 檢視 / 修改系統 Prompt`) in the AI Growth Lead Drawer.
3. 0px Stealth Recruiter Telemetry (`recruiter_telemetry.py`) with `?developer=true` opt-out and zero visual footprint.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from chart_generator import generate_chart_config, render_dynamic_chart
from fastmcp_diagnostic import (
    DEFAULT_SYSTEM_PROMPT_ZH,
    generate_chart_diagnosis,
    generate_tab_diagnosis,
)
from mcp_server.server import (
    get_byok_conversion_funnel,
    get_daily_growth_kpis,
    get_feature_adoption_matrix,
    get_referral_viral_loop,
    get_semantic_kpi_definitions,
    load_gold_dataframe,
)
from recruiter_telemetry import inject_stealth_telemetry

st.set_page_config(
    page_title="ReadCall PLG 產品數據戰情室 | AI Growth Cockpit",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject 0px stealth recruiter open telemetry (strictly invisible, respects ?developer=true)
inject_stealth_telemetry("portfolio_opened", {"cockpit_lang": "zh-TW"})

# Custom SaaS Dark/Light Adaptive Styling
st.markdown(
    """
    <style>
    .plg-header-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
        padding: 1.35rem 1.6rem;
        border-radius: 14px;
        border: 1px solid rgba(56, 189, 248, 0.28);
        margin-bottom: 1.1rem;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
    }
    .plg-badge {
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 600;
        background: rgba(56, 189, 248, 0.16);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.35);
        margin-right: 0.45rem;
    }
    .prompt-active-pill {
        display: inline-block;
        padding: 0.18rem 0.6rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.35);
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=600)
def load_cockpit_datasets() -> dict[str, pd.DataFrame]:
    """Load ReadCall Gold & Silver tables via unified BigQuery / DuckDB / In-Memory loader."""
    return {
        "kpi": load_gold_dataframe("gold_daily_growth_kpi"),
        "features": load_gold_dataframe("gold_feature_adoption"),
        "byok": load_gold_dataframe("gold_byok_funnel"),
        "referral": load_gold_dataframe("gold_referral_loop"),
        "traffic": load_gold_dataframe("fct_daily_traffic"),
    }


def init_session_state() -> None:
    """Initialize Streamlit session state variables for AI drawer & System Prompt Playground."""
    if "show_ai_panel" not in st.session_state:
        st.session_state.show_ai_panel = True
    if "custom_system_prompt_zh" not in st.session_state:
        st.session_state.custom_system_prompt_zh = DEFAULT_SYSTEM_PROMPT_ZH
    if "prompt_is_customized_zh" not in st.session_state:
        st.session_state.prompt_is_customized_zh = False
    if "tab_diagnoses_zh" not in st.session_state:
        st.session_state.tab_diagnoses_zh = {}
    if "chat_messages_zh" not in st.session_state:
        st.session_state.chat_messages_zh = [
            {
                "role": "assistant",
                "content": (
                    "您好！我是 **ReadCall 產品成長負責人與首席資料科學家 (SaaS Head of Growth & Staff Product DS)**。\n\n"
                    "您可以點擊上方 **「🛠️ 檢視 / 修改系統 Prompt」** 隨時查看或改寫我的底層分析指令，"
                    "或直接要求我診斷 **Aha! 啟用率**、**`ByokModal.tsx` 金鑰轉換漏斗** 與 **32 項埋點帕累托分佈**。"
                ),
            }
        ]


def run_chat_turn(user_query: str, active_system_prompt: str, api_key: str | None) -> str:
    """Execute a conversational turn using Gemini tool-calling or deterministic FastMCP fallback."""
    effective_key = api_key or os.getenv("GEMINI_API_KEY")
    if effective_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=effective_key)
            context_snapshot = {
                "daily_growth": get_daily_growth_kpis(days=30),
                "byok_funnel": get_byok_conversion_funnel(),
                "referral_loop": get_referral_viral_loop(),
                "top_features": get_feature_adoption_matrix()[:10],
            }
            prompt = (
                f"【ReadCall Gold Mart 即時快照 (FastMCP)】\n{context_snapshot}\n\n"
                f"【使用者問題】\n{user_query}\n\n"
                "請根據系統指令與上述真實埋點數據回答，並標註對應的 React 元件路徑（如 `src/components/ByokModal.tsx`）。"
            )
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=active_system_prompt,
                    temperature=0.25,
                ),
            )
            if resp and resp.text:
                return resp.text
        except Exception:
            pass

    # Deterministic offline fallback using FastMCP tools
    q_lower = user_query.lower()
    if "byok" in q_lower or "key" in q_lower or "金鑰" in q_lower:
        return generate_tab_diagnosis(
            "Tab 3: BYOK Conversion Funnel",
            get_byok_conversion_funnel(),
            lang="zh-TW",
            custom_system_prompt=active_system_prompt,
        )
    if "feature" in q_lower or "功能" in q_lower or "pareto" in q_lower or "字典" in q_lower:
        return generate_tab_diagnosis(
            "Tab 2: Feature Stickiness Pareto",
            {"top_features": get_feature_adoption_matrix()[:8]},
            lang="zh-TW",
            custom_system_prompt=active_system_prompt,
        )
    return generate_tab_diagnosis(
        "Tab 1: AARRR Growth Overview",
        {"growth": get_daily_growth_kpis(days=30), "byok": get_byok_conversion_funnel()},
        lang="zh-TW",
        custom_system_prompt=active_system_prompt,
    )


def main() -> None:
    init_session_state()
    datasets = load_cockpit_datasets()
    df_kpi = datasets["kpi"]
    df_features = datasets["features"]
    df_byok = datasets["byok"]
    datasets["referral"]
    df_traffic = datasets["traffic"]

    # Sidebar Configuration & Governance Controls
    with st.sidebar:
        st.markdown("### 📘 ReadCall PLG 數據中台")
        st.caption("Source: GA4 Property `559361789` (`G-CR2LW8PH5M`) → `dlt` → `dbt` → `FastMCP`")
        st.divider()

        st.session_state.show_ai_panel = st.toggle(
            "🤖 開啟 AI 成長顧問抽屜 (AI Advisor)",
            value=st.session_state.show_ai_panel,
        )

        user_gemini_key = st.text_input(
            "🔑 Google Gemini API Key (選填 BYOK)",
            type="password",
            help="輸入您的 Gemini API Key 可啟用即時 LLM 推理；未輸入時自動使用內建確定性 PLG 診斷引擎。",
        )

        st.divider()
        st.markdown("#### 📐 dbt Semantic Layer 治理指標")
        sem_metrics = get_semantic_kpi_definitions()
        for m in sem_metrics:
            with st.expander(f"📏 {m['label']}", expanded=False):
                st.code(m["formula"], language="sql")
                st.caption(f"**Owner:** `{m['owner']}`")
                st.caption(f"**React 元件:** `{', '.join(m.get('source_components', []))}`")
                st.caption(f"**行動建議:** {m['recommended_action']}")

    # Top Header Banner
    st.markdown(
        """
        <div class="plg-header-card">
            <div>
                <span class="plg-badge">GA4 Property 559361789</span>
                <span class="plg-badge">Medallion Lakehouse (readcall_bronze / silver / gold)</span>
                <span class="plg-badge">dbt Semantic Layer + FastMCP</span>
            </div>
            <h2 style="margin: 0.55rem 0 0.25rem 0; color: #f8fafc;">
                📘 ReadCall 德語 AI 閱讀器 — 產品分析與 PLG 成長數據戰情室
            </h2>
            <p style="margin: 0; color: #94a3b8; font-size: 0.92rem;">
                追蹤 32 項前端真實 GA4 埋點事件、Aha! 核心閱讀啟用率、6 階 BYOK Gemini 金鑰轉換漏斗與 5 階推薦裂變迴路（90 天隱私校準視窗）
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Split Layout: Main Analytical Canvas vs. Right-Side AI Growth Lead Drawer
    if st.session_state.show_ai_panel:
        col_main, col_ai = st.columns([6.8, 3.2], gap="large")
    else:
        col_main = st.container()
        col_ai = None

    with col_main:
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "📈 Tab 1: AARRR 成長總覽與 DACH 獲客",
                "🧩 Tab 2: 德語閱讀器與 32 埋點黏著度 (80/20)",
                "🔑 Tab 3: BYOK 金鑰轉換漏斗 & 推薦裂變",
                "✨ Tab 4: AI 自然語言圖表生成 (NL2Chart)",
            ]
        )

        # =====================================================================
        # TAB 1: AARRR GROWTH OVERVIEW & DACH ACQUISITION
        # =====================================================================
        with tab1:
            total_dau = int(df_kpi["dau"].sum()) if not df_kpi.empty else 0
            total_sessions = int(df_kpi["total_sessions"].sum()) if not df_kpi.empty else 0
            avg_eng_rate = float(df_kpi["engagement_rate"].mean()) if not df_kpi.empty else 0.0
            avg_aha_rate = float(df_kpi["aha_activation_rate"].mean()) if not df_kpi.empty else 0.0
            avg_ai_depth = float(df_kpi["ai_morphological_depth"].mean()) if not df_kpi.empty else 0.0

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("90 天累計活躍讀者 (Cumulative DAU)", f"{total_dau:,}", f"{total_sessions:,} 總工作階段")
            k2.metric("平均互動工作階段率 (Engagement Rate)", f"{avg_eng_rate * 100:.1f}%", "目標基準 ≥ 65.0%")
            k3.metric(
                "Aha! 核心功能啟用率 (Aha! Activation)",
                f"{avg_aha_rate * 100:.1f}%",
                "選詞解析 + 雙語字典查詢",
            )
            k4.metric(
                "AI 形態學深度解析率 (AI Depth Ratio)",
                f"{avg_ai_depth * 100:.2f}%",
                "LinguisticInspectorContent.tsx",
            )

            if st.button("⚡ 由 AI 成長負責人診斷 Tab 1 (AARRR & DACH)", key="btn_diag_tab1"):
                inject_stealth_telemetry("portfolio_tab_viewed", {"tab": "tab1_aarrr"})
                st.session_state.tab_diagnoses_zh["tab1"] = generate_tab_diagnosis(
                    "Tab 1: AARRR 成長總覽與 DACH 獲客",
                    {
                        "total_dau": total_dau,
                        "engagement_rate": round(avg_eng_rate, 4),
                        "aha_activation_rate": round(avg_aha_rate, 4),
                        "ai_morphological_depth": round(avg_ai_depth, 4),
                    },
                    api_key=user_gemini_key,
                    lang="zh-TW",
                    custom_system_prompt=st.session_state.custom_system_prompt_zh,
                )

            if "tab1" in st.session_state.tab_diagnoses_zh:
                st.info(st.session_state.tab_diagnoses_zh["tab1"])

            c_left, c_right = st.columns([6, 4])
            with c_left:
                if not df_kpi.empty:
                    df_plot = df_kpi.sort_values("event_date")
                    fig_trend = go.Figure()
                    fig_trend.add_trace(
                        go.Scatter(
                            x=df_plot["event_date"],
                            y=df_plot["dau"],
                            mode="lines",
                            name="每日活躍用戶 (DAU)",
                            line={"color": "#38bdf8", "width": 2.5},
                        )
                    )
                    fig_trend.add_trace(
                        go.Scatter(
                            x=df_plot["event_date"],
                            y=df_plot["aha_users"],
                            mode="lines",
                            name="Aha! 核心啟用讀者 (Aha! Users)",
                            line={"color": "#10b981", "width": 2.2, "dash": "dot"},
                        )
                    )
                    fig_trend.update_layout(
                        title="90 天每日活躍用戶 (DAU) 與 Aha! 核心功能啟用趨勢",
                        template="plotly_dark",
                        height=360,
                        margin={"l": 20, "r": 20, "t": 45, "b": 20},
                        legend={"orientation": "h", "y": 1.12},
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)

            with c_right:
                if not df_traffic.empty and "session_default_channel_group" in df_traffic.columns:
                    ch_agg = (
                        df_traffic.groupby("session_default_channel_group", as_index=False)["active_users"]
                        .sum()
                        .sort_values("active_users", ascending=False)
                    )
                    fig_ch = px.pie(
                        ch_agg,
                        names="session_default_channel_group",
                        values="active_users",
                        hole=0.48,
                        title="流量獲取渠道結構 (Acquisition Channel Mix)",
                        template="plotly_dark",
                    )
                    fig_ch.update_layout(height=360, margin={"l": 20, "r": 20, "t": 45, "b": 20})
                    st.plotly_chart(fig_ch, use_container_width=True)

            if not df_traffic.empty and "country" in df_traffic.columns:
                geo_agg = (
                    df_traffic.groupby(["country", "is_dach_region"], as_index=False)[
                        ["active_users", "engaged_sessions"]
                    ]
                    .sum()
                    .sort_values("active_users", ascending=False)
                )
                geo_agg["Region Group"] = geo_agg["is_dach_region"].map(
                    {True: "DACH 德語核心區 (DE/AT/CH)", False: "Global 全球學習市場"}
                )
                fig_geo = px.bar(
                    geo_agg,
                    x="country",
                    y="active_users",
                    color="Region Group",
                    title="DACH 德語區 (DE/AT/CH) vs. 全球市場讀者分佈",
                    template="plotly_dark",
                    color_discrete_map={
                        "DACH 德語核心區 (DE/AT/CH)": "#38bdf8",
                        "Global 全球學習市場": "#818cf8",
                    },
                )
                fig_geo.update_layout(height=320, margin={"l": 20, "r": 20, "t": 45, "b": 20})
                st.plotly_chart(fig_geo, use_container_width=True)

        # =====================================================================
        # TAB 2: GERMAN READER & 32-EVENT STICKINESS PARETO
        # =====================================================================
        with tab2:
            st.markdown("#### 🧩 ReadCall 32 項前端 GA4 埋點事件 — 80/20 帕累托集中度與 React 元件映射")
            if st.button("⚡ 由 AI 成長負責人診斷 Tab 2 (功能黏著度與 AI 深度)", key="btn_diag_tab2"):
                inject_stealth_telemetry("portfolio_tab_viewed", {"tab": "tab2_feature_pareto"})
                st.session_state.tab_diagnoses_zh["tab2"] = generate_tab_diagnosis(
                    "Tab 2: 德語閱讀器與 32 埋點黏著度",
                    {"top_10_events": df_features.head(10).to_dict(orient="records")},
                    api_key=user_gemini_key,
                    lang="zh-TW",
                    custom_system_prompt=st.session_state.custom_system_prompt_zh,
                )

            if "tab2" in st.session_state.tab_diagnoses_zh:
                st.info(st.session_state.tab_diagnoses_zh["tab2"])

            if not df_features.empty:
                df_f_sorted = df_features.sort_values("total_event_count", ascending=False).copy()
                df_f_sorted["cumulative_pct"] = (
                    df_f_sorted["total_event_count"].cumsum() / df_f_sorted["total_event_count"].sum() * 100.0
                )

                fig_pareto = go.Figure()
                fig_pareto.add_trace(
                    go.Bar(
                        x=df_f_sorted["event_name"],
                        y=df_f_sorted["total_event_count"],
                        name="事件觸發總量 (Event Count)",
                        marker_color="#38bdf8",
                    )
                )
                fig_pareto.add_trace(
                    go.Scatter(
                        x=df_f_sorted["event_name"],
                        y=df_f_sorted["cumulative_pct"],
                        name="累積佔比 (Cumulative %)",
                        yaxis="y2",
                        mode="lines+markers",
                        line={"color": "#f59e0b", "width": 2.5},
                    )
                )
                fig_pareto.update_layout(
                    title="32 項產品埋點事件 80/20 帕累托分析 (Core Reader vs. Dictionary vs. AI Morphology)",
                    template="plotly_dark",
                    height=420,
                    yaxis={"title": "事件觸發次數 (Count)"},
                    yaxis2={
                        "title": "累積百分比 (%)",
                        "overlaying": "y",
                        "side": "right",
                        "range": [0, 105],
                    },
                    margin={"l": 20, "r": 20, "t": 45, "b": 85},
                )
                st.plotly_chart(fig_pareto, use_container_width=True)

                mod_col1, mod_col2 = st.columns([4.5, 5.5])
                with mod_col1:
                    mod_summary = (
                        df_features.groupby("module_category", as_index=False)["total_event_count"]
                        .sum()
                        .sort_values("total_event_count", ascending=False)
                    )
                    fig_mod = px.bar(
                        mod_summary,
                        x="total_event_count",
                        y="module_category",
                        orientation="h",
                        color="module_category",
                        title="五大產品模組互動總量分佈",
                        template="plotly_dark",
                    )
                    fig_mod.update_layout(
                        height=340,
                        showlegend=False,
                        margin={"l": 20, "r": 20, "t": 45, "b": 20},
                    )
                    st.plotly_chart(fig_mod, use_container_width=True)

                with mod_col2:
                    st.markdown("##### 🔍 32 項埋點與前端 React (`.tsx`) 元件對照表")
                    display_cols = [
                        "event_name",
                        "module_category",
                        "aarrr_stage",
                        "source_component",
                        "total_event_count",
                        "event_share_pct",
                    ]
                    avail_cols = [c for c in display_cols if c in df_f_sorted.columns]
                    st.dataframe(
                        df_f_sorted[avail_cols],
                        use_container_width=True,
                        height=310,
                    )

        # =====================================================================
        # TAB 3: 6-STEP BYOK CONVERSION FUNNEL & 5-STEP REFERRAL VIRAL LOOP
        # =====================================================================
        with tab3:
            byok_summary = get_byok_conversion_funnel()
            ref_summary = get_referral_viral_loop()

            b1, b2, b3, b4 = st.columns(4)
            b1.metric(
                "試用牆觸發總次數 (Trial Wall Hits)",
                f"{byok_summary['step_3_trial_limit_hit']:,}",
                "trial_exhausted + banner_cta",
            )
            b2.metric(
                "ByokModal 開啟至儲存完成率",
                f"{byok_summary['byok_modal_to_save_rate'] * 100:.1f}%",
                f"{byok_summary['step_6_byok_key_saved']:,} 組金鑰成功綁定",
            )
            b3.metric(
                "API 金鑰驗證失敗摩擦率",
                f"{byok_summary['byok_verify_failure_rate'] * 100:.1f}%",
                f"{byok_summary['byok_verify_failed']:,} 次 byok_verify_failed",
                delta_color="inverse",
            )
            b4.metric(
                "推薦裂變解鎖率 (Viral K-Factor Proxy)",
                f"{ref_summary['viral_k_factor_proxy'] * 100:.1f}%",
                f"{ref_summary['step_4_referral_unlock_success']:,} 人解鎖自訂 AI 家教",
            )

            if st.button("⚡ 由 AI 成長負責人診斷 Tab 3 (BYOK 漏斗與推薦裂變)", key="btn_diag_tab3"):
                inject_stealth_telemetry("portfolio_tab_viewed", {"tab": "tab3_byok_referral"})
                st.session_state.tab_diagnoses_zh["tab3"] = generate_tab_diagnosis(
                    "Tab 3: 6 階 BYOK 金鑰轉換漏斗與 5 階推薦裂變迴路",
                    {"byok_funnel": byok_summary, "referral_loop": ref_summary},
                    api_key=user_gemini_key,
                    lang="zh-TW",
                    custom_system_prompt=st.session_state.custom_system_prompt_zh,
                )

            if "tab3" in st.session_state.tab_diagnoses_zh:
                st.info(st.session_state.tab_diagnoses_zh["tab3"])

            f_col1, f_col2 = st.columns(2)
            with f_col1:
                fig_byok = go.Figure(
                    go.Funnel(
                        y=[
                            "1. 閱讀器開啟 (reader_opened)",
                            "2. AI 形態學/家教查詢 (AI Inquiry)",
                            "3. 觸發免費試用上限牆 (Trial Limit Hit)",
                            "4. 開啟 ByokModal.tsx (byok_modal_opened)",
                            "5. 點擊取得 Google AI Key (get_key_clicked)",
                            "6. 驗證並儲存金鑰 (byok_key_saved)",
                        ],
                        x=[
                            byok_summary["step_1_reader_opened"],
                            byok_summary["step_2_ai_trial_inquiry"],
                            byok_summary["step_3_trial_limit_hit"],
                            byok_summary["step_4_byok_modal_opened"],
                            byok_summary["step_5_byok_get_key_clicked"],
                            byok_summary["step_6_byok_key_saved"],
                        ],
                        textinfo="value+percent previous",
                        marker={"color": ["#38bdf8", "#0ea5e9", "#0284c7", "#6366f1", "#4f46e5", "#10b981"]},
                    )
                )
                fig_byok.update_layout(
                    title="6 階免費試用至 BYOK 金鑰綁定轉換漏斗 (ByokModal.tsx)",
                    template="plotly_dark",
                    height=400,
                    margin={"l": 20, "r": 20, "t": 45, "b": 20},
                )
                st.plotly_chart(fig_byok, use_container_width=True)

            with f_col2:
                fig_ref = go.Figure(
                    go.Funnel(
                        y=[
                            "1. 開啟推薦視窗 (referral_modal_opened)",
                            "2. 複製專屬推薦連結 (referral_link_copied)",
                            "3. 新讀者推薦橫幅曝光 (referral_banner_shown)",
                            "4. 推薦碼驗證解鎖成功 (referral_unlock_success)",
                            "5. 儲存自訂 AI 家教 Prompt (custom_prompt_saved)",
                        ],
                        x=[
                            ref_summary["step_1_referral_modal_opened"],
                            ref_summary["step_2_referral_link_copied"],
                            ref_summary["step_3_referral_banner_shown"],
                            ref_summary["step_4_referral_unlock_success"],
                            ref_summary["step_5_custom_prompt_saved"],
                        ],
                        textinfo="value+percent previous",
                        marker={"color": ["#a855f7", "#9333ea", "#7e22ce", "#ec4899", "#10b981"]},
                    )
                )
                fig_ref.update_layout(
                    title="5 階病毒式推薦與自訂 AI 家教 Prompt 解鎖漏斗",
                    template="plotly_dark",
                    height=400,
                    margin={"l": 20, "r": 20, "t": 45, "b": 20},
                )
                st.plotly_chart(fig_ref, use_container_width=True)

            if not df_byok.empty:
                df_byok_sorted = df_byok.sort_values("event_date")
                fig_friction = go.Figure()
                fig_friction.add_trace(
                    go.Bar(
                        x=df_byok_sorted["event_date"],
                        y=df_byok_sorted["step_6_byok_key_saved"],
                        name="成功儲存金鑰 (byok_key_saved)",
                        marker_color="#10b981",
                    )
                )
                fig_friction.add_trace(
                    go.Bar(
                        x=df_byok_sorted["event_date"],
                        y=df_byok_sorted["byok_verify_failed"],
                        name="金鑰驗證失敗 (byok_verify_failed)",
                        marker_color="#ef4444",
                    )
                )
                fig_friction.update_layout(
                    barmode="stack",
                    title="每日 BYOK 金鑰綁定成功 vs. 驗證失敗摩擦監控 (`src/components/ByokModal.tsx`)",
                    template="plotly_dark",
                    height=310,
                    margin={"l": 20, "r": 20, "t": 45, "b": 20},
                )
                st.plotly_chart(fig_friction, use_container_width=True)

        # =====================================================================
        # TAB 4: BILINGUAL AI NL2CHART GENERATOR
        # =====================================================================
        with tab4:
            st.markdown("#### ✨ 雙語自然語言轉圖表引擎 (AI NL2Chart Generator)")
            st.caption("直接輸入中文或英文分析問題，系統將自動選擇最佳資料集並繪製互動式 Plotly 圖表。")

            preset_col1, preset_col2, preset_col3 = st.columns(3)
            selected_preset = ""
            if preset_col1.button("📊 顯示前 12 大產品功能埋點排行", use_container_width=True):
                selected_preset = "顯示前 12 大產品功能埋點排行 (Top 12 Feature Adoption)"
            if preset_col2.button("🔑 分析每日 BYOK 金鑰儲存與失敗趨勢", use_container_width=True):
                selected_preset = "分析每日 BYOK 金鑰儲存與驗證失敗趨勢"
            if preset_col3.button("🌱 查看每日推薦連結複製與解鎖趨勢", use_container_width=True):
                selected_preset = "查看每日推薦連結複製與解鎖趨勢 (Referral Loop)"

            nl_query = st.text_input(
                "輸入您的自然語言圖表需求：",
                value=selected_preset or "顯示前 12 大產品功能埋點排行",
                key="nl2chart_input_zh",
            )

            if nl_query:
                inject_stealth_telemetry("portfolio_tab_viewed", {"tab": "tab4_nl2chart"})
                cfg = generate_chart_config(nl_query, api_key=user_gemini_key)
                if cfg:
                    ds_key = cfg.get("dataset", "kpi")
                    target_df = datasets.get(ds_key, df_kpi)
                    fig_nl = render_dynamic_chart(cfg, target_df)
                    if fig_nl:
                        st.plotly_chart(fig_nl, use_container_width=True)
                        with st.expander("🧠 檢視 AI NL2Chart 圖表洞察與結構配置", expanded=True):
                            st.write(
                                generate_chart_diagnosis(
                                    nl_query,
                                    cfg,
                                    target_df,
                                    api_key=user_gemini_key,
                                    lang="zh-TW",
                                    custom_system_prompt=st.session_state.custom_system_prompt_zh,
                                )
                            )

    # =========================================================================
    # RIGHT-SIDE COLLAPSIBLE AI GROWTH LEAD DRAWER + SYSTEM PROMPT PLAYGROUND
    # =========================================================================
    if col_ai is not None:
        with col_ai:
            st.markdown("### 🤖 AI 產品成長顧問抽屜")
            if st.session_state.prompt_is_customized_zh:
                st.markdown(
                    '<span class="prompt-active-pill">⚡ 自訂 System Prompt 已啟用</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<span class="prompt-active-pill">🛡️ 預設 PLG Growth Lead Prompt</span>',
                    unsafe_allow_html=True,
                )

            # INTERACTIVE SYSTEM PROMPT PLAYGROUND (Requested Feature #2)
            with st.expander("🛠️ 檢視 / 修改系統 Prompt (Edit System Prompt)", expanded=False):
                st.caption(
                    "開啟即可檢視原始預設的 **SaaS 成長負責人與首席產品資料科學家** System Prompt。"
                    "您可自由手動修改角色設定、分析框架或輸出格式，並立即套用至下方所有 AI 診斷與對話！"
                )
                edited_prompt = st.text_area(
                    "System Prompt 內容（支援即時手動修改）：",
                    value=st.session_state.custom_system_prompt_zh,
                    height=260,
                    key="system_prompt_editor_textarea_zh",
                )
                btn_p1, btn_p2 = st.columns(2)
                if btn_p1.button("💾 套用自訂 Prompt", use_container_width=True, key="apply_prompt_zh"):
                    st.session_state.custom_system_prompt_zh = edited_prompt.strip() or DEFAULT_SYSTEM_PROMPT_ZH
                    st.session_state.prompt_is_customized_zh = (
                        st.session_state.custom_system_prompt_zh != DEFAULT_SYSTEM_PROMPT_ZH
                    )
                    inject_stealth_telemetry(
                        "portfolio_ai_tested",
                        {"action": "custom_prompt_applied", "lang": "zh-TW"},
                    )
                    st.success("✅ 已套用自訂 System Prompt！後續診斷與對話將立即生效。")

                if btn_p2.button("🔄 還原預設值", use_container_width=True, key="reset_prompt_zh"):
                    st.session_state.custom_system_prompt_zh = DEFAULT_SYSTEM_PROMPT_ZH
                    st.session_state.prompt_is_customized_zh = False
                    st.info("🔄 已還原為預設 PLG Growth Lead System Prompt。")
                    st.rerun()

            st.divider()
            st.markdown("##### 💬 與 ReadCall PLG 數據顧問對話")
            chat_container = st.container(height=420)
            with chat_container:
                for msg in st.session_state.chat_messages_zh:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            user_chat_input = st.chat_input(
                "詢問 BYOK 轉換率、Aha! 啟用率或 React 元件優化建議...",
                key="ai_drawer_chat_input_zh",
            )
            if user_chat_input:
                inject_stealth_telemetry(
                    "portfolio_ai_tested",
                    {
                        "action": "chat_query",
                        "prompt_customized": st.session_state.prompt_is_customized_zh,
                    },
                )
                st.session_state.chat_messages_zh.append({"role": "user", "content": user_chat_input})
                reply = run_chat_turn(
                    user_chat_input,
                    active_system_prompt=st.session_state.custom_system_prompt_zh,
                    api_key=user_gemini_key,
                )
                st.session_state.chat_messages_zh.append({"role": "assistant", "content": reply})
                st.rerun()

    st.divider()
    st.caption(
        f"ReadCall Product Analytics & PLG Lakehouse Platform • Updated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} "
        "• Powered by dlt, dbt Core Semantic Layer, DuckDB/BigQuery, FastMCP & Streamlit"
    )


if __name__ == "__main__":
    main()
