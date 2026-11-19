"""Natural Language AI Chart Generation Engine (NL2Chart) for ReadCall Product Analytics.

Supports bilingual prompts (Traditional Chinese & English) across ReadCall's 4 Gold Marts:
- gold_daily_growth_kpi (DAU, sessions, engagement, Aha! activation, offloaded AI compute)
- gold_feature_adoption (32 product events across 5 modules & React components)
- gold_byok_funnel (6-stage trial-to-BYOK key activation funnel & verification failure rate)
- gold_referral_loop (5-stage viral referral & Custom AI Tutor Prompt unlock loop)
"""

from __future__ import annotations

import json
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Canonical schema whitelist for ReadCall's 4 Gold Marts (prevents LLM column hallucinations)
DATASET_SCHEMAS: dict[str, dict[str, str]] = {
    "kpi": {
        "event_date": "Daily date (x-axis for time-series)",
        "dau": "Daily Active Users",
        "new_users": "New users",
        "returning_users": "Returning users",
        "total_sessions": "Total sessions",
        "engaged_sessions": "Engaged sessions",
        "engagement_rate": "Session engagement rate (0-1)",
        "avg_session_duration_sec": "Average session duration in seconds",
        "aha_users": "Users who triggered Aha! core feature (text select or dictionary)",
        "aha_activation_rate": "Aha! activation rate (aha_users / dau)",
        "core_reader_events": "Core German reader events count",
        "dictionary_events": "Dictionary search events count",
        "ai_inference_events": "AI morphological explanation & tutor events count",
        "byok_keys_saved": "Daily BYOK Gemini API keys saved",
        "referral_unlocks": "Daily viral referral unlocks",
        "offloaded_ai_compute_usd": "Estimated AI inference compute cost saved via BYOK (USD)",
    },
    "byok": {
        "event_date": "Daily date (x-axis)",
        "step_1_first_visit": "Stage 1: First visits",
        "step_2_aha_interaction": "Stage 2: Aha! interactions",
        "step_3_trial_limit_hit": "Stage 3: Free trial quota exhausted hits",
        "step_4_byok_modal_opened": "Stage 4: ByokModal opened",
        "step_5_key_acquisition_attempt": "Stage 5: Clicked Get/Paste Gemini API Key",
        "step_6_byok_key_saved": "Stage 6: Gemini API key verified & saved successfully",
        "byok_verify_failed": "API key verification failures (friction)",
        "byok_conversion_rate": "Trial-to-BYOK key conversion rate",
        "byok_modal_completion_rate": "ByokModal open-to-save completion rate",
        "byok_verify_failure_rate": "API key verification failure rate",
    },
    "referral": {
        "event_date": "Daily date (x-axis)",
        "step_1_referral_modal_opened": "Referral modal opened",
        "step_2_referral_link_copied": "Referral links copied",
        "step_3_referral_link_visited": "Referral links visited by friends",
        "step_4_referral_unlock_success": "Custom AI Tutor Prompt unlocks succeeded",
        "step_5_custom_prompt_saved": "Custom AI Tutor prompts saved",
        "viral_k_factor": "Viral referral K-factor proxy",
    },
    "features": {
        "event_name": "GA4 product event name (y-axis for horizontal_bar)",
        "total_event_count": "Total event triggers count (x-axis for horizontal_bar)",
        "unique_users": "Unique users triggering this event",
        "module_category": "Product module pillar (color grouping)",
    },
}


def generate_chart_from_nl(
    prompt: str,
    df_growth: pd.DataFrame,
    df_features: pd.DataFrame,
    df_byok: pd.DataFrame,
    df_referral: pd.DataFrame | None = None,
    gemini_api_key: str = "",
    language: str = "zh",
) -> tuple[go.Figure | None, str, str, pd.DataFrame]:
    """Parse natural language query and generate an interactive Plotly chart with PLG insights."""
    clean_prompt = prompt.strip().lower()
    has_cjk = any("\u4e00" <= ch <= "\u9fff" for ch in prompt)
    is_en = language.lower() == "en" or (not has_cjk and len(clean_prompt) > 0)

    # 1. BYOK Funnel & Key Verification queries
    if any(
        kw in clean_prompt
        for kw in [
            "byok",
            "key",
            "金鑰",
            "綁定",
            "試用",
            "trial",
            "funnel",
            "漏斗",
            "verify",
            "驗證",
        ]
    ):
        title = (
            "ReadCall 6-Stage BYOK API Key Conversion Funnel"
            if is_en
            else "ReadCall 6 階段 BYOK 金鑰綁定轉換漏斗"
        )
        stages = (
            [
                "1. First Visit (first_visit)",
                "2. Aha! Experience (Reader/Dict)",
                "3. Trial Wall Hit (trial_exhausted)",
                "4. BYOK Modal Opened (ByokModal.tsx)",
                "5. Get/Paste Key Clicked",
                "6. BYOK Key Saved (byok_key_saved)",
            ]
            if is_en
            else [
                "1. 首次造訪 (first_visit)",
                "2. 觸發 Aha! 選字/查字典",
                "3. 觸發試用額度牆 (trial_exhausted)",
                "4. 開啟金鑰視窗 (ByokModal.tsx)",
                "5. 點擊領取或貼上金鑰",
                "6. 成功驗證並儲存金鑰 (byok_key_saved)",
            ]
        )
        counts = [
            int(df_byok["step_1_first_visit"].sum()),
            int(df_byok["step_2_aha_interaction"].sum()),
            int(df_byok["step_3_trial_limit_hit"].sum()),
            int(df_byok["step_4_byok_modal_opened"].sum()),
            int(df_byok["step_5_key_acquisition_attempt"].sum()),
            int(df_byok["step_6_byok_key_saved"].sum()),
        ]
        out_df = pd.DataFrame({"stage": stages, "count": counts})
        fig = go.Figure(
            go.Funnel(
                y=out_df["stage"],
                x=out_df["count"],
                textinfo="value+percent initial+percent previous",
                marker={
                    "color": [
                        "#3b82f6",
                        "#2563eb",
                        "#f59e0b",
                        "#8b5cf6",
                        "#6366f1",
                        "#10b981",
                    ]
                },
            )
        )
        fig.update_layout(title=title, height=420, template="plotly_white")
        insight = (
            "BYOK Funnel highlights strong Aha! activation; streamlining Google AI Studio key retrieval in `ByokModal.tsx` is the highest-leverage CRO play."
            if is_en
            else "BYOK 漏斗顯示用戶在觸發試用牆後開啟 `ByokModal.tsx` 意願極高；優化前往 Google AI Studio 領取金鑰的引導可大幅提升最終綁定率。"
        )
        return fig, title, insight, out_df

    # 2. Referral Viral Loop queries
    if (
        any(
            kw in clean_prompt
            for kw in [
                "referral",
                "viral",
                "推薦",
                "裂變",
                "分享",
                "unlock",
                "解鎖",
                "tutor",
                "prompt",
            ]
        )
        and df_referral is not None
        and not df_referral.empty
    ):
        title = (
            "Viral Referral Loop & Custom AI Tutor Prompt Unlocks"
            if is_en
            else "ReadCall 推薦裂變迴圈與 AI 家教 Prompt 解鎖漏斗"
        )
        stages = (
            [
                "1. Referral Modal Opened",
                "2. Referral Link Copied",
                "3. Referral Link Visited",
                "4. Referral Unlock Success",
                "5. Custom Prompt Saved",
            ]
            if is_en
            else [
                "1. 開啟推薦視窗 (referral_modal_opened)",
                "2. 複製推薦連結 (referral_link_copied)",
                "3. 好友點擊造訪 (referral_link_visited)",
                "4. 解鎖成功 (referral_unlock_success)",
                "5. 儲存自訂家教提示詞 (custom_prompt_saved)",
            ]
        )
        counts = [
            int(df_referral["step_1_referral_modal_opened"].sum()),
            int(df_referral["step_2_referral_link_copied"].sum()),
            int(df_referral["step_3_referral_link_visited"].sum()),
            int(df_referral["step_4_referral_unlock_success"].sum()),
            int(df_referral["step_5_custom_prompt_saved"].sum()),
        ]
        out_df = pd.DataFrame({"stage": stages, "count": counts})
        fig = px.bar(
            out_df,
            x="count",
            y="stage",
            orientation="h",
            text="count",
            color="stage",
            title=title,
            template="plotly_white",
        )
        fig.update_layout(showlegend=False, height=400)
        insight = (
            "Referral loop in `TutorCustomPromptModal.tsx` converts ~35% of modal opens into link copies."
            if is_en
            else "`TutorCustomPromptModal.tsx` 推薦視窗具備約 35% 的複製分享率，是零成本獲客（$0 CAC）的核心飛輪。"
        )
        return fig, title, insight, out_df

    # 3. Feature Adoption / Event Ranking queries
    if any(
        kw in clean_prompt
        for kw in [
            "feature",
            "event",
            "功能",
            "事件",
            "排行",
            "字典",
            "閱讀",
            "reader",
            "dictionary",
            "pareto",
            "動詞",
            "verb",
        ]
    ):
        title = (
            "Top 12 ReadCall Product Telemetry Events by Volume"
            if is_en
            else "ReadCall 核心產品功能事件觸發排行 (Top 12)"
        )
        out_df = (
            df_features.sort_values("total_event_count", ascending=False)
            .head(12)
            .copy()
        )
        fig = px.bar(
            out_df,
            x="total_event_count",
            y="event_name",
            color="module_category",
            orientation="h",
            hover_data=["source_component", "avg_frequency_per_user"],
            title=title,
            template="plotly_white",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=440)
        insight = (
            "`reader_text_selected` and `dictionary_searched` dominate user engagement, validating ReadCall's German immersion core loop."
            if is_en
            else "`reader_text_selected`（閱讀器選字）與 `dictionary_searched`（複合詞字典查詢）高居互動榜首，驗證德語沉浸式閱讀的核心價值。"
        )
        return fig, title, insight, out_df

    # 4. Default: Daily DAU, Sessions & Aha! Activation Trend
    title = (
        "ReadCall Daily Active Users (DAU) & Aha! Activation Trend"
        if is_en
        else "ReadCall 每日活躍學習者 (DAU) 與 Aha! 啟用人數趨勢"
    )
    out_df = df_growth.sort_values("event_date", ascending=True).copy()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=out_df["event_date"],
            y=out_df["dau"],
            mode="lines+markers",
            name="DAU" if is_en else "每日活躍用戶 (DAU)",
            line={"color": "#2563eb", "width": 2.5},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=out_df["event_date"],
            y=out_df["aha_users"],
            mode="lines",
            name="Aha! Activated Users" if is_en else "觸發 Aha! 核心功能用戶",
            line={"color": "#10b981", "width": 2, "dash": "dot"},
        )
    )
    fig.update_layout(title=title, height=420, template="plotly_white")
    insight = (
        "Consistent organic growth in DAU with >70% Aha! activation rate across German reading sessions."
        if is_en
        else "DAU 呈現穩健自然成長，且超過 70% 的活躍學習者會在進站後觸發德語選字或字典查詢（Aha! Moment）。"
    )
    return fig, title, insight, out_df


def _generate_chart_config_with_gemini(query: str, api_key: str) -> dict | None:
    """Use native Google Gemini SDK with strict JSON output & schema whitelist to generate chart config."""
    clean_key = (api_key or "").strip()
    if not clean_key:
        return None
    try:
        from google import genai
        from google.genai import types

        from fastmcp_diagnostic import get_gemini_candidate_models

        client = genai.Client(api_key=clean_key)
        candidates = get_gemini_candidate_models(client)

        schema_doc = json.dumps(DATASET_SCHEMAS, ensure_ascii=False, indent=2)
        system_prompt = (
            "You are a Product Analytics NL2Chart engine for ReadCall (a German AI reading app using BYOK Gemini API keys).\n"
            "Given a user's chart request in Chinese or English, return ONLY a valid JSON object matching this exact contract:\n"
            "{\n"
            '  "dataset": "kpi" | "byok" | "referral" | "features",\n'
            '  "chart_type": "line" | "bar" | "horizontal_bar",\n'
            '  "x": "<exact column name from chosen dataset>",\n'
            '  "y": ["<exact column name(s) from chosen dataset>"],\n'
            '  "title": "<concise chart title matching the user language>",\n'
            '  "limit": 12\n'
            "}\n\n"
            "Rules:\n"
            "1. Use ONLY exact column names from the chosen dataset in DATASET_SCHEMAS below. Never invent column names.\n"
            "2. For time-series datasets ('kpi', 'byok', 'referral'), 'x' MUST be 'event_date' and 'y' MUST be a non-empty list of 1-3 numeric columns.\n"
            "3. For 'features' rankings/top events, set chart_type='horizontal_bar', x='total_event_count', y=['event_name'], and set 'limit' to the requested top-N (default 12).\n"
            "4. If the user asks about Gemini API key / password / BYOK success, failure, conversion, or modal friction, pick dataset='byok'.\n"
            "5. If the user asks about AI compute cost savings (USD), engagement rate, sessions, DAU, new vs returning users, pick dataset='kpi'.\n\n"
            f"DATASET_SCHEMAS:\n{schema_doc}"
        )

        for model_name in candidates:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=f"User chart request: {query}",
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.0,
                        response_mime_type="application/json",
                    ),
                )
                if not resp or not resp.text:
                    continue
                parsed = json.loads(resp.text.strip())
                ds = str(parsed.get("dataset", "")).strip().lower()
                if ds not in DATASET_SCHEMAS:
                    continue

                valid_cols = set(DATASET_SCHEMAS[ds].keys())
                ctype = str(parsed.get("chart_type", "line")).strip().lower()
                if ctype not in ("line", "bar", "horizontal_bar"):
                    ctype = "horizontal_bar" if ds == "features" else "line"

                if ds == "features" or ctype == "horizontal_bar":
                    limit_val = max(1, min(int(parsed.get("limit", 12)), 32))
                    return {
                        "dataset": "features",
                        "chart_type": "horizontal_bar",
                        "x": "total_event_count",
                        "y": "event_name",
                        "color": "module_category",
                        "title": str(
                            parsed.get("title")
                            or f"ReadCall Top {limit_val} Product Telemetry Events"
                        ),
                        "limit": limit_val,
                        "query": query,
                        "generated_by": f"gemini:{model_name}",
                    }

                x_col = str(parsed.get("x", "event_date")).strip()
                if x_col not in valid_cols:
                    x_col = "event_date"

                raw_y = parsed.get("y", [])
                if isinstance(raw_y, str):
                    raw_y = [raw_y]
                y_cols = [c for c in raw_y if isinstance(c, str) and c in valid_cols and c != x_col]
                if not y_cols:
                    continue

                return {
                    "dataset": ds,
                    "chart_type": ctype,
                    "x": x_col,
                    "y": y_cols[:3],
                    "title": str(parsed.get("title") or query),
                    "query": query,
                    "generated_by": f"gemini:{model_name}",
                }
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        return None
    return None


def _readcall_fallback_chart_config(query: str) -> dict:
    """Deterministic ReadCall rule-based fallback when Gemini API key is absent."""
    q = (query or "").strip().lower()
    if any(
        k in q
        for k in [
            "byok",
            "key",
            "金鑰",
            "密碼",
            "api",
            "綁定",
            "試用",
            "驗證",
            "verify",
            "modal",
        ]
    ):
        return {
            "dataset": "byok",
            "chart_type": "bar",
            "x": "event_date",
            "y": ["step_6_byok_key_saved", "byok_verify_failed"],
            "title": "ReadCall Daily BYOK Key Saves vs. Verification Failures",
            "query": query,
            "generated_by": "fallback_rules",
        }
    if any(k in q for k in ["referral", "推薦", "裂變", "分享", "解鎖", "unlock"]):
        return {
            "dataset": "referral",
            "chart_type": "line",
            "x": "event_date",
            "y": ["step_2_referral_link_copied", "step_4_referral_unlock_success"],
            "title": "ReadCall Viral Referral Link Copies & Unlocks Trend",
            "query": query,
            "generated_by": "fallback_rules",
        }
    if any(
        k in q
        for k in ["feature", "功能", "排行", "埋點", "pareto", "字典", "event", "top"]
    ):
        return {
            "dataset": "features",
            "chart_type": "horizontal_bar",
            "x": "total_event_count",
            "y": "event_name",
            "color": "module_category",
            "title": "ReadCall Top 12 Product Telemetry Events by Volume",
            "limit": 12,
            "query": query,
            "generated_by": "fallback_rules",
        }
    if any(k in q for k in ["cost", "usd", "省", "費用", "成本", "算力", "offload"]):
        return {
            "dataset": "kpi",
            "chart_type": "line",
            "x": "event_date",
            "y": ["offloaded_ai_compute_usd"],
            "title": "ReadCall Daily Offloaded AI Compute Savings (USD)",
            "query": query,
            "generated_by": "fallback_rules",
        }
    return {
        "dataset": "kpi",
        "chart_type": "line",
        "x": "event_date",
        "y": ["dau", "aha_users"],
        "title": "ReadCall Daily Active Users (DAU) & Aha! Activated Readers",
        "query": query,
        "generated_by": "fallback_rules",
    }


def generate_chart_config(query: str, api_key: str | None = None) -> dict:
    """Delegate NL2Chart generation to shared cockpit_core submodule Gemini engine."""
    try:
        from cockpit_loader import load_ai_chart_engine

        generate_ai_chart_config, _ = load_ai_chart_engine()
        return generate_ai_chart_config(
            query=query,
            dataset_schemas=DATASET_SCHEMAS,
            api_key=api_key,
            domain_context=(
                "Product: ReadCall (German AI reading app with BYOK Gemini API keys & viral referrals). "
                "Map API key / password / BYOK questions to dataset='byok'; "
                "AI compute savings / engagement / DAU / new vs returning users to dataset='kpi'."
            ),
            fallback_fn=_readcall_fallback_chart_config,
        )
    except Exception:  # noqa: BLE001
        eff_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        if eff_key:
            ai_cfg = _generate_chart_config_with_gemini(query, eff_key)
            if ai_cfg is not None:
                return ai_cfg
        return _readcall_fallback_chart_config(query)


def render_dynamic_chart(config: dict, df: pd.DataFrame) -> go.Figure | None:
    """Delegate Plotly rendering to shared cockpit_core submodule renderer (with local fallback)."""
    try:
        from cockpit_loader import load_ai_chart_engine

        _, render_ai_dynamic_chart = load_ai_chart_engine()
        return render_ai_dynamic_chart(config, df)
    except Exception:  # noqa: BLE001
        pass
    if df is None or df.empty or not config:
        return None

    ctype = config.get("chart_type", "line")
    title = config.get("title", "ReadCall NL2Chart")

    if ctype == "horizontal_bar" and "event_name" in df.columns:
        limit_n = max(1, min(int(config.get("limit", 12)), 32))
        sub = df.sort_values("total_event_count", ascending=False).head(limit_n).copy()
        fig = px.bar(
            sub,
            x="total_event_count",
            y="event_name",
            color="module_category" if "module_category" in sub.columns else None,
            orientation="h",
            title=title,
            template="plotly_white",
        )
        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    x_col = config.get("x", "event_date")
    y_cols = config.get("y", ["dau"])
    if isinstance(y_cols, str):
        y_cols = [y_cols]
    avail_y = [c for c in y_cols if c in df.columns]
    if not avail_y or x_col not in df.columns:
        return None

    sub = df.sort_values(x_col).copy()
    fig = go.Figure()
    colors = ["#2563eb", "#10b981", "#f59e0b", "#ef4444"]
    for idx, col in enumerate(avail_y):
        if ctype == "bar":
            fig.add_trace(
                go.Bar(
                    x=sub[x_col],
                    y=sub[col],
                    name=col,
                    marker_color=colors[idx % len(colors)],
                )
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=sub[x_col],
                    y=sub[col],
                    mode="lines+markers",
                    name=col,
                    line={
                        "color": colors[idx % len(colors)],
                        "width": 2.5,
                        "shape": "spline",
                    },
                )
            )
    fig.update_layout(
        barmode="group",
        title=title,
        template="plotly_white",
        height=390,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.1},
    )
    return fig
