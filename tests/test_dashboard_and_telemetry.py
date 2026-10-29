"""Unit & Integration Tests for Stealth Recruiter Telemetry, NL2Chart & Streamlit Cockpits."""

from __future__ import annotations

from pathlib import Path

import pytest

from chart_generator import generate_chart_config, render_dynamic_chart
from dashboard import load_cockpit_datasets
from recruiter_telemetry import build_stealth_ga4_snippet, extract_recruiter_context

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_stealth_recruiter_telemetry_context_and_opt_out():
    """Verify ?utm_campaign=, ?ref=, and ?developer=true opt-out behavior."""
    ctx_hr = extract_recruiter_context({"utm_campaign": "stripe_hr_team", "utm_source": "cv_pdf"})
    assert ctx_hr["recruiter_ref"] == "stripe_hr_team"
    assert ctx_hr["utm_campaign"] == "stripe_hr_team"
    assert ctx_hr["utm_source"] == "cv_pdf"
    assert ctx_hr["is_opted_out"] is False

    snippet = build_stealth_ga4_snippet(
        event_name="portfolio_opened",
        context=ctx_hr,
        extra_params={"cockpit_lang": "zh-TW"},
        ga_id="G-CR2LW8PH5M",
    )
    assert "G-CR2LW8PH5M" in snippet
    assert "portfolio_opened" in snippet
    assert "stripe_hr_team" in snippet
    assert "readcall_ga_opt_out" in snippet
    assert "display:none" in snippet

    # Developer opt-out must suppress snippet generation completely
    ctx_dev = extract_recruiter_context({"ref": "self_test", "developer": "true"})
    assert ctx_dev["is_opted_out"] is True
    assert build_stealth_ga4_snippet("portfolio_opened", context=ctx_dev) == ""


def test_stealth_telemetry_rejects_non_portfolio_event_names():
    """Ensure stealth telemetry only emits `portfolio_*` events so product analytics stay pure."""
    with pytest.raises(ValueError, match="portfolio_"):
        build_stealth_ga4_snippet("reader_opened")


def test_nl2chart_and_cockpit_datasets():
    """Verify cockpit dataset loading and NL2Chart generation across all 4 analytical domains."""
    datasets = load_cockpit_datasets()
    assert set(datasets.keys()) == {"kpi", "features", "byok", "referral", "traffic"}
    assert len(datasets["features"]) == 32
    assert not datasets["kpi"].empty
    assert not datasets["byok"].empty
    assert not datasets["referral"].empty

    for query in [
        "顯示前 12 大產品功能埋點排行",
        "分析每日 BYOK 金鑰儲存與驗證失敗趨勢",
        "查看每日推薦連結複製與解鎖趨勢",
        "Show daily active users trend",
    ]:
        cfg = generate_chart_config(query)
        assert cfg is not None
        ds_df = datasets[cfg["dataset"]]
        fig = render_dynamic_chart(cfg, ds_df)
        assert fig is not None


def test_dashboard_files_include_system_prompt_playground_and_have_no_visible_recruiter_ui():
    """Verify both dashboard.py and dashboard_en.py expose the System Prompt editor and keep recruiter tracking invisible."""
    zh_code = (REPO_ROOT / "dashboard.py").read_text(encoding="utf-8")
    en_code = (REPO_ROOT / "dashboard_en.py").read_text(encoding="utf-8")

    assert "🛠️ 檢視 / 修改系統 Prompt (Edit System Prompt)" in zh_code
    assert "💾 套用自訂 Prompt" in zh_code
    assert "🔄 還原預設值" in zh_code

    assert "🛠️ View / Edit System Prompt" in en_code
    assert "💾 Apply Custom Prompt" in en_code
    assert "🔄 Reset to Default" in en_code

    # Ensure no visible recruiter tracking tab or table is rendered on the UI
    assert "Recruiter Tracker" not in zh_code
    assert "Recruiter Tracker" not in en_code
