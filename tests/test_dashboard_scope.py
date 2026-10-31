"""Automated Regression Test Suite for DashboardScope and Filter Consistency.

Ensures all charts, cards, and funnel metrics strictly honor the active date range filter,
preventing Data Binding Disconnect and Architectural Antipatterns permanently across the cockpit.
"""

from __future__ import annotations

import ast
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from chart_generator import generate_chart_config, render_dynamic_chart
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
    assert scope_sub.byok_funnel["step_5_byok_key_saved"] == int(scope_sub.byok["step_6_byok_key_saved"].sum())

    # 4. Referral Loop Sensitivity
    assert len(scope_sub.referral) <= len(scope_full.referral)
    assert scope_sub.referral_loop["step_1_referral_modal_opened"] == int(scope_sub.referral["step_1_referral_modal_opened"].sum())

    # 5. Features Pareto Binding Sensitivity
    assert len(scope_sub.features) <= len(scope_full.features), "Filtered features rows must be <= full range"
    if "total_event_count" in scope_sub.features.columns and "total_event_count" in scope_full.features.columns:
        assert scope_sub.features["total_event_count"].sum() < scope_full.features["total_event_count"].sum(), (
            "Filtered feature events total must scale with date range"
        )


def test_funnel_monotonicity_and_positive_stages(cockpit_data: tuple[dict[str, pd.DataFrame], pd.DataFrame]) -> None:
    """Issue 07 Verification:

    Asserts that the 5-stage BYOK Funnel and Referral Loop are strictly monotonic (S1 >= S2 >= S3 >= S4 >= S5)
    and contain non-zero, genuine values without bulging or Infinity% artifacts.
    """
    data_dict, df_traffic = cockpit_data
    scope = DashboardScope(raw_dict=data_dict, traffic_raw=df_traffic)

    # 1. BYOK Funnel Monotonicity
    bf = scope.byok_funnel
    s1 = bf["step_1_first_visit"]
    s2 = bf["step_2_aha_interaction"]
    s3 = bf["step_3_byok_modal_opened"]
    s4 = bf["step_4_byok_get_key_clicked"]
    s5 = bf["step_5_byok_key_saved"]

    assert s1 > 0 and s2 > 0 and s3 > 0 and s4 > 0 and s5 > 0, "All BYOK funnel stages must be strictly positive"
    assert s1 >= s2, f"First visit ({s1}) must be >= Aha interaction ({s2})"
    assert s2 >= s3, f"Aha interaction ({s2}) must be >= ByokModal opened ({s3})"
    assert s3 >= s4, f"ByokModal opened ({s3}) must be >= key acquisition attempt ({s4})"
    assert s4 >= s5, f"Key acquisition attempt ({s4}) must be >= key saved ({s5})"

    # 2. Referral Loop Monotonicity
    rf = scope.referral_loop
    r1 = rf["step_1_referral_modal_opened"]
    r2 = rf["step_2_referral_link_copied"]
    r3 = rf["step_4_referral_unlock_success"]
    r4 = rf["step_5_custom_prompt_saved"]

    assert r1 > 0 and r2 > 0 and r3 > 0 and r4 > 0, "All referral stages must be positive"
    assert r1 >= r2, f"Referral modal opens ({r1}) must be >= link copies ({r2})"
    assert r2 >= r3, f"Link copies ({r2}) must be >= unlock successes ({r3})"
    assert r3 >= r4, f"Unlock successes ({r3}) must be >= custom prompt saves ({r4})"


def test_nl2chart_all_presets_and_registry_coverage(cockpit_data: tuple[dict[str, pd.DataFrame], pd.DataFrame]) -> None:
    """Issue 08 Verification:

    Verifies that all 3 preset queries and standard DAU queries map to valid datasets
    and successfully render Plotly Figure instances without silent failures.
    """
    data_dict, df_traffic = cockpit_data
    scope = DashboardScope(raw_dict=data_dict, traffic_raw=df_traffic)

    DATASET_REGISTRY = {
        "kpi": lambda s: s.kpi,
        "traffic": lambda s: s.traffic,
        "features": lambda s: s.features,
        "byok": lambda s: s.byok,
        "referral": lambda s: s.referral,
    }

    test_queries = [
        "Show top 12 product features by event count",
        "Daily BYOK key saves vs verification failures",
        "Referral link copies and unlock success trend",
        "Show daily active users trend",
    ]

    for q in test_queries:
        cfg = generate_chart_config(q)
        ds_key = cfg.get("dataset", "kpi")
        assert ds_key in DATASET_REGISTRY, f"Dataset {ds_key} must exist in registry"
        df_target = DATASET_REGISTRY[ds_key](scope)
        assert not df_target.empty, f"Target DataFrame for {ds_key} should not be empty"
        fig = render_dynamic_chart(cfg, df_target)
        assert fig is not None, f"Query '{q}' failed to generate a valid Plotly Figure"


def test_empty_date_range_honest_handling(cockpit_data: tuple[dict[str, pd.DataFrame], pd.DataFrame]) -> None:
    """Issue 10 Verification:

    Ensures that when an out-of-bounds date range is requested, DashboardScope honestly
    returns an empty DataFrame rather than silently falling back to the 90-day dataset.
    """
    data_dict, df_traffic = cockpit_data
    scope_future = DashboardScope(
        raw_dict=data_dict,
        traffic_raw=df_traffic,
        start_date=date(2035, 1, 1),
        end_date=date(2035, 1, 10),
    )

    assert scope_future.kpi.empty, "Out of bounds date range must return empty kpi DataFrame"
    assert scope_future.traffic.empty, "Out of bounds date range must return empty traffic DataFrame"
    assert scope_future.byok.empty, "Out of bounds date range must return empty byok DataFrame"


def test_ast_guard_no_unscoped_or_unweighted_ratios() -> None:
    """Issue 11 CI/CD Architectural Guard:

    Scans dashboard.py AST to enforce:
    1. No UI visualization code inside main() calls cached_byok_conversion_funnel or cached_referral_viral_loop.
    2. No metric card calculation performs unweighted .mean() on engagement_rate or aha_activation_rate.
    """
    dashboard_path = Path(__file__).resolve().parent.parent / "dashboard.py"
    assert dashboard_path.exists(), "dashboard.py must exist"

    tree = ast.parse(dashboard_path.read_text(encoding="utf-8"))

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
            # Check for direct calls bypassing DashboardScope
            if isinstance(subnode.func, ast.Name) and subnode.func.id in forbidden_calls:
                violations.append(f"Line {subnode.lineno}: Direct call to {subnode.func.id}() bypassing DashboardScope")

            # Check for unweighted ratio mean
            if isinstance(subnode.func, ast.Attribute) and subnode.func.attr == "mean":
                if isinstance(subnode.func.value, ast.Subscript):
                    slice_node = subnode.func.value.slice
                    if isinstance(slice_node, ast.Constant) and slice_node.value in ("engagement_rate", "aha_activation_rate"):
                        violations.append(f"Line {subnode.lineno}: Unweighted .mean() on ratio column '{slice_node.value}' (Simpson's Paradox)")

    assert not violations, f"Architectural Guard Violations: {violations}"
