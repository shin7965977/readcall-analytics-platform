import pytest

from fastmcp_diagnostic import (
    DEFAULT_SYSTEM_PROMPT_EN,
    DEFAULT_SYSTEM_PROMPT_ZH,
    generate_chart_diagnosis,
    generate_tab_diagnosis,
)
from mcp_server.server import (
    ALLOWED_DATASET,
    get_byok_funnel,
    get_daily_growth_kpi,
    get_feature_adoption,
    get_referral_loop,
    get_semantic_definitions,
    sanitize_dataset_access,
)


def test_fastmcp_security_boundary_enforces_readcall_gold_only():
    """Verify FastMCP strictly permits only readcall_gold and blocks bronze/silver/platzi."""
    assert ALLOWED_DATASET == "readcall_gold"
    assert sanitize_dataset_access("readcall_gold") == "readcall_gold"
    assert sanitize_dataset_access("  READCALL_GOLD ") == "readcall_gold"

    for forbidden in ("readcall_bronze", "readcall_silver", "platzi_gold"):
        with pytest.raises(ValueError, match="Access denied"):
            sanitize_dataset_access(forbidden)


def test_fastmcp_tools_return_structured_readcall_metrics():
    """Verify all 5 FastMCP tools return non-empty ReadCall PLG & semantic payloads in mock/offline mode."""
    growth = get_daily_growth_kpi(limit=7, mock_mode=True)
    assert len(growth) > 0
    assert "dau" in growth[0]
    assert "aha_activation_rate" in growth[0]

    features = get_feature_adoption(limit=10, mock_mode=True)
    assert len(features) > 0
    assert "event_name" in features[0]
    assert "source_component" in features[0]

    byok = get_byok_funnel(limit=7, mock_mode=True)
    assert len(byok) > 0
    assert "byok_conversion_rate" in byok[0]
    assert "byok_verify_failure_rate" in byok[0]

    referral = get_referral_loop(limit=7, mock_mode=True)
    assert len(referral) > 0
    assert "viral_k_factor" in referral[0]

    sem = get_semantic_definitions()
    assert "metrics" in sem
    metric_names = {m["name"] for m in sem["metrics"]}
    assert "aha_activation_rate" in metric_names
    assert "byok_conversion_rate" in metric_names


def test_default_system_prompt_uses_plg_persona_and_custom_prompt_override():
    """Verify the default prompt uses the pragmatic SaaS Head of Growth persona and supports custom overrides."""
    assert "Head of Growth" in DEFAULT_SYSTEM_PROMPT_ZH
    assert "ByokModal.tsx" in DEFAULT_SYSTEM_PROMPT_ZH
    assert "McKinsey" not in DEFAULT_SYSTEM_PROMPT_ZH

    assert "Head of Growth" in DEFAULT_SYSTEM_PROMPT_EN
    assert "ByokModal.tsx" in DEFAULT_SYSTEM_PROMPT_EN
    assert "McKinsey" not in DEFAULT_SYSTEM_PROMPT_EN

    # Verify that without API key, generation is strictly locked and prompts to bind key
    diag_zh = generate_tab_diagnosis(
        tab_key="byok",
        tab_title="BYOK 漏斗與推薦裂變",
        tab_payload={"byok_conversion_rate": 0.42, "verify_failure_rate": 0.09},
        user_query="如何提升 BYOK 金鑰綁定率？",
        api_key="",
        language="zh",
        custom_system_prompt="自訂提示詞測試",
    )
    assert "Gemini API Key" in diag_zh
    assert "FastMCP" in diag_zh

    chart_diag = generate_chart_diagnosis(
        chart_title="BYOK Funnel",
        df_summary={"step_3_trial_limit_hit": 100, "step_6_byok_key_saved": 42},
        api_key="",
        language="en",
    )
    assert "Gemini API Key" in chart_diag
