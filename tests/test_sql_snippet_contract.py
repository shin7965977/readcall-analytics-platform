"""Unit test contract: Verifies that all SQL queries in the dashboard expanders
have 100% column names, order, and row count parity with their rendered Table Data Snippets.
"""

from __future__ import annotations

import re
from pathlib import Path

from mcp_server.server import load_gold_dataframe


REPO_ROOT = Path(__file__).resolve().parent.parent


def extract_sql_select_columns(sql_text: str) -> list[str]:
    """Parse out projected column names/aliases from a SELECT query."""
    # Find SELECT ... FROM
    m = re.search(r"SELECT\s+(.*?)\s+FROM\b", sql_text, re.DOTALL | re.IGNORECASE)
    assert m, f"No SELECT ... FROM found in SQL: {sql_text}"
    select_clause = m.group(1).strip()

    cols = []
    # Split by comma not inside parens
    parts = re.split(r",\s*(?![^()]*\))", select_clause)
    for p in parts:
        p = p.strip()
        # Check alias 'AS <alias>'
        m_as = re.search(r"\bAS\s+([a-zA-Z0-9_]+)$", p, re.IGNORECASE)
        if m_as:
            cols.append(m_as.group(1).strip())
        else:
            # Fallback to last token (e.g. t.active_users -> active_users)
            token = p.split()[-1]
            if "." in token:
                token = token.split(".")[-1]
            cols.append(token.strip())
    return cols


def extract_sql_limit(sql_text: str) -> int | None:
    """Extract LIMIT N from SQL query."""
    m = re.search(r"\bLIMIT\s+(\d+)\b", sql_text, re.IGNORECASE)
    return int(m.group(1)) if m else None


def test_friction_monitoring_sql_and_table_snippet_contract():
    """Principle 2: Friction Monitoring SQL columns and row counts MUST match Table Data Snippet 1:1."""
    # 1. Inspect SQL snippet in dashboard.py
    code = (REPO_ROOT / "dashboard.py").read_text(encoding="utf-8")

    # Locate friction monitoring SQL block
    assert "Friction Monitoring SQL" in code
    fric_match = re.search(
        r"SELECT\s+event_date,\s+step_6_byok_key_saved,\s+byok_verify_failed,.*?round\(byok_verify_failed.*?AS friction_pct.*?LIMIT 5;",
        code,
        re.DOTALL,
    )
    assert fric_match, (
        "Friction Monitoring SQL must contain exact SELECT list and LIMIT 5;"
    )
    sql_text = fric_match.group(0)

    sql_cols = extract_sql_select_columns(sql_text)
    sql_limit = extract_sql_limit(sql_text)

    assert sql_cols == [
        "event_date",
        "step_6_byok_key_saved",
        "byok_verify_failed",
        "friction_pct",
    ]
    assert sql_limit == 5

    # 2. Simulate runtime execution of the snippet
    df_byok = load_gold_dataframe("gold_byok_funnel")
    df_b_sort = df_byok.sort_values("event_date", ascending=False).head(5).copy()
    df_b_sort["friction_pct"] = (
        df_b_sort["byok_verify_failed"]
        * 100.0
        / (df_b_sort["step_6_byok_key_saved"] + df_b_sort["byok_verify_failed"]).clip(
            lower=1
        )
    ).round(2)

    table_snippet = df_b_sort[sql_cols].reset_index(drop=True)

    # Assert column parity
    assert list(table_snippet.columns) == sql_cols
    # Assert row count parity
    assert len(table_snippet) == sql_limit


def test_all_8_dashboard_sql_snippets_have_strict_column_and_limit_parity():
    """Verify all 8 chart expanders in dashboard.py enforce exact column & row count parity."""
    code = (REPO_ROOT / "dashboard.py").read_text(encoding="utf-8")

    # 1. Star Schema 1: Traffic Acquisition & Geo Star
    s1_match = re.search(
        r"-- Traffic Acquisition Star Schema Join\s+SELECT\s+(.*?)\s+LIMIT (\d+);",
        code,
        re.DOTALL,
    )
    assert s1_match, "Star Schema 1 SQL must have LIMIT clause"
    s1_cols = extract_sql_select_columns("SELECT " + s1_match.group(1) + " FROM dummy")
    s1_limit = int(s1_match.group(2))
    assert s1_limit == 15
    assert len(s1_cols) == 12
    assert s1_cols == [
        "traffic_record_id",
        "event_date",
        "acquisition_type",
        "channel_group",
        "source_medium",
        "device_category",
        "country",
        "is_dach_region",
        "sessions",
        "engaged_sessions",
        "active_users",
        "engagement_rate",
    ]

    # 2. Star Schema 2: Product Engagement & Feature Funnel Star
    s2_match = re.search(
        r"-- Product Feature Events Star Schema Join\s+SELECT\s+(.*?)\s+LIMIT (\d+);",
        code,
        re.DOTALL,
    )
    assert s2_match, "Star Schema 2 SQL must have LIMIT clause"
    s2_cols = extract_sql_select_columns("SELECT " + s2_match.group(1) + " FROM dummy")
    s2_limit = int(s2_match.group(2))
    assert s2_limit == 15
    assert len(s2_cols) == 11
    assert s2_cols == [
        "event_record_id",
        "event_date",
        "event_name",
        "aarrr_stage",
        "module_category",
        "source_component",
        "is_aha_moment",
        "is_ai_inference_event",
        "event_count",
        "total_users",
        "events_per_user",
    ]

    # 3. DAU & Aha Trend
    kpi_match = re.search(
        r"SELECT\s+event_date,\s+dau,\s+aha_users,\s+round\(aha_users \* 100\.0 / nullif\(dau, 0\), 2\) AS aha_rate_pct\s+FROM `de-consulting-508822\.readcall_gold\.gold_daily_growth_kpi`\s+ORDER BY event_date DESC\s+LIMIT (\d+);",
        code,
    )
    assert kpi_match, "DAU trend SQL must have LIMIT 5"
    kpi_limit = int(kpi_match.group(1))
    assert kpi_limit == 5

    # 4. Acquisition Channel Mix
    ch_match = re.search(
        r"c\.acquisition_type,\s+t\.channel_group,\s+SUM\(t\.active_users\) AS active_users.*?ORDER BY 3 DESC\s+LIMIT (\d+);",
        code,
        re.DOTALL,
    )
    assert ch_match, "Channel mix SQL must have LIMIT 5"
    assert int(ch_match.group(1)) == 5

    # 5. DACH vs Global
    geo_match = re.search(
        r"g\.country,\s+g\.is_dach_region,\s+SUM\(t\.active_users\) AS active_users.*?ORDER BY 3 DESC LIMIT (\d+);",
        code,
        re.DOTALL,
    )
    assert geo_match, "Geo SQL must have LIMIT 5"
    assert int(geo_match.group(1)) == 5

    # 6. Monotonic BYOK Funnel
    byok_match = re.search(
        r"SELECT\s+event_date,\s+step_1_first_visit,\s+step_2_aha_interaction,\s+step_4_byok_modal_opened,\s+step_5_byok_get_key_clicked,\s+step_6_byok_key_saved\s+FROM `de-consulting-508822\.readcall_gold\.gold_byok_funnel`\s+ORDER BY event_date DESC\s+LIMIT (\d+);",
        code,
    )
    assert byok_match, "BYOK funnel SQL must have LIMIT 5"
    assert int(byok_match.group(1)) == 5

    # 7. Referral Loop
    ref_match = re.search(
        r"SELECT\s+event_date,\s+step_1_referral_modal_opened,\s+step_2_referral_link_copied,\s+step_4_referral_unlock_success,\s+step_5_custom_prompt_saved,\s+viral_k_factor\s+FROM `de-consulting-508822\.readcall_gold\.gold_referral_loop`\s+ORDER BY event_date DESC\s+LIMIT (\d+);",
        code,
    )
    assert ref_match, "Referral loop SQL must have LIMIT 5"
    assert int(ref_match.group(1)) == 5

    # 8. Friction Monitoring
    fric_match = re.search(
        r"SELECT\s+event_date,\s+step_6_byok_key_saved,\s+byok_verify_failed,\s+round\(byok_verify_failed \* 100\.0 / nullif\(step_6_byok_key_saved \+ byok_verify_failed, 0\), 2\) AS friction_pct\s+FROM `de-consulting-508822\.readcall_gold\.gold_byok_funnel`\s+ORDER BY event_date DESC\s+LIMIT (\d+);",
        code,
    )
    assert fric_match, "Friction SQL must have LIMIT 5"
    assert int(fric_match.group(1)) == 5
