"""Automated Regression Test Suite for DashboardScope and Filter Consistency.

Ensures all charts, cards, and funnel metrics strictly honor the active date range filter,
preventing Data Binding Disconnect permanently across the cockpit.
"""

from __future__ import annotations

import ast
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from dashboard import DashboardScope, load_lakehouse_data
from mcp_server.server import load_gold_dataframe


@pytest.fixture(scope="module")
def cockpit_data() -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    data_dict = load_lakehouse_data("gold")
    df_traffic = load_gold_dataframe("fct_daily_traffic")
    return data_dict, df_traffic


def test_scope_full_range(cockpit_data: tuple[dict[str, pd.DataFrame], pd.DataFrame]) -> None:
    data_dict, df_traffic = cockpit_data
    scope = DashboardScope(raw_dict=data_dict, traffic_raw=df_traffic)

    assert not scope.kpi.empty, "KPI table should not be empty"
    assert not scope.traffic.empty, "Traffic table should not be empty"
    assert not scope.byok.empty, "BYOK table should not be empty"
    assert not scope.features.empty, "Features table should not be empty"


def test_scope_date_filter_sensitivity(cockpit_data: tuple[dict[str, pd.DataFrame], pd.DataFrame]) -> None:
    data_dict, df_traffic = cockpit_data
    df_kpi = data_dict["kpi"]
    assert "event_date" in df_kpi.columns

    min_date = df_kpi["event_date"].min().date()
    max_date = df_kpi["event_date"].max().date()
    mid_date = min_date + (max_date - min_date) // 2

    # Restrict to second half of date range
    scope_full = DashboardScope(raw_dict=data_dict, traffic_raw=df_traffic)
    scope_sub = DashboardScope(
        raw_dict=data_dict,
        traffic_raw=df_traffic,
        start_date=mid_date,
        end_date=max_date,
    )

    # 1. KPI & Trend Chart Binding Sensitivity
    assert len(scope_sub.kpi) < len(scope_full.kpi), "Filtered KPI rows must be smaller than full range"
    assert scope_sub.kpi["event_date"].dt.date.min() >= mid_date, "Min date in scope must be >= start_date"
    assert scope_sub.kpi["event_date"].dt.date.max() <= max_date, "Max date in scope must be <= end_date"
    assert scope_sub.kpi["dau"].sum() < scope_full.kpi["dau"].sum(), "Sum of DAU must scale with date filter"

    # 2. Traffic Acquisition & Geo Mix Binding Sensitivity
    assert len(scope_sub.traffic) < len(scope_full.traffic), "Filtered traffic rows must be smaller than full range"
    assert scope_sub.traffic["active_users"].sum() < scope_full.traffic["active_users"].sum(), "Active users in traffic must scale with filter"

    # 3. BYOK Funnel & Friction Bar Chart Sensitivity
    assert len(scope_sub.byok) < len(scope_full.byok), "BYOK rows must scale with date filter"
    assert scope_sub.byok_funnel["step_6_byok_key_saved"] == int(scope_sub.byok["step_6_byok_key_saved"].sum())
    assert scope_sub.byok_funnel["step_1_reader_opened"] <= scope_full.byok_funnel["step_1_reader_opened"]

    # 4. Referral Loop Sensitivity
    assert len(scope_sub.referral) <= len(scope_full.referral)
    assert scope_sub.referral_loop["step_1_referral_modal_opened"] == int(scope_sub.referral["step_1_referral_modal_opened"].sum())
    assert scope_sub.referral_loop["step_1_referral_modal_opened"] <= scope_full.referral_loop["step_1_referral_modal_opened"]

    # 5. Features Pareto Binding Sensitivity
    assert len(scope_sub.features) <= len(scope_full.features), "Filtered features rows must be <= full range"
    if "total_event_count" in scope_sub.features.columns and "total_event_count" in scope_full.features.columns:
        assert scope_sub.features["total_event_count"].sum() < scope_full.features["total_event_count"].sum(), (
            "Filtered feature events total must scale with date range"
        )


def test_ast_guard_no_unscoped_cached_funnels_in_rendering() -> None:
    """CI/CD Architectural Lint Guard:

    Scans dashboard.py AST to enforce that NO UI visualization code inside main()
    ever bypasses DashboardScope by directly calling cached_byok_conversion_funnel
    or cached_referral_viral_loop.
    """
    dashboard_path = Path(__file__).resolve().parent.parent / "dashboard.py"
    assert dashboard_path.exists(), "dashboard.py must exist"

    tree = ast.parse(dashboard_path.read_text(encoding="utf-8"))

    # Find the main() function node
    main_func: ast.FunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            main_func = node
            break

    assert main_func is not None, "main() function must exist in dashboard.py"

    forbidden_calls = {"cached_byok_conversion_funnel", "cached_referral_viral_loop"}
    violations: list[str] = []

    for subnode in ast.walk(main_func):
        if isinstance(subnode, ast.Call):
            if isinstance(subnode.func, ast.Name) and subnode.func.id in forbidden_calls:
                violations.append(f"Line {subnode.lineno}: Direct call to {subnode.func.id}() bypassing DashboardScope")

    assert not violations, f"Architectural Guard Violation: {violations}"
