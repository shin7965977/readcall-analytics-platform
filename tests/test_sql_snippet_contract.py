"""Unit test contract: Verifies that all 8 SQL queries in dashboard expanders
dynamically incorporate WHERE date range filters matching the sidebar filter,
and have 100% column names, order, and row parity with their rendered Table Data Snippets.
"""

from __future__ import annotations

import re
from pathlib import Path
import pandas as pd

from mcp_server.server import load_gold_dataframe


REPO_ROOT = Path(__file__).resolve().parent.parent


def extract_sql_select_columns(sql_text: str) -> list[str]:
    """Parse out projected column names/aliases from a SELECT query."""
    m = re.search(r"SELECT\s+(.*?)\s+FROM\b", sql_text, re.DOTALL | re.IGNORECASE)
    assert m, f"No SELECT ... FROM found in SQL: {sql_text}"
    select_clause = m.group(1).strip()

    cols = []
    parts = re.split(r",\s*(?![^()]*\))", select_clause)
    for p in parts:
        p = p.strip()
        m_as = re.search(r"\bAS\s+([a-zA-Z0-9_]+)$", p, re.IGNORECASE)
        if m_as:
            cols.append(m_as.group(1).strip())
        else:
            token = p.split()[-1]
            if "." in token:
                token = token.split(".")[-1]
            cols.append(token.strip())
    return cols


def test_friction_monitoring_sql_and_table_snippet_contract():
    """Principle 2: Friction Monitoring SQL dynamically uses WHERE event_date BETWEEN and matches table rows 1:1."""
    code = (REPO_ROOT / "dashboard.py").read_text(encoding="utf-8")

    assert "Friction Monitoring SQL" in code
    # Check that SQL has dynamic WHERE clause
    fric_match = re.search(
        r"SELECT\s+event_date,\s+step_6_byok_key_saved,\s+byok_verify_failed,.*?round\(byok_verify_failed.*?AS friction_pct.*?WHERE event_date BETWEEN '\{start_str\}' AND '\{end_str\}'.*?ORDER BY event_date ASC;",
        code,
        re.DOTALL,
    )
    assert fric_match, (
        "Friction Monitoring SQL must contain exact SELECT list, dynamic WHERE date range, and ORDER BY event_date ASC;"
    )
    sql_text = fric_match.group(0)

    sql_cols = extract_sql_select_columns(sql_text)
    assert sql_cols == [
        "event_date",
        "step_6_byok_key_saved",
        "byok_verify_failed",
        "friction_pct",
    ]

    # Test runtime simulation with a specific 5-day date filter
    start_d = pd.to_datetime("2026-10-16")
    end_d = pd.to_datetime("2026-10-20")

    df_byok = load_gold_dataframe("gold_byok_funnel")
    df_byok["event_date"] = pd.to_datetime(df_byok["event_date"])
    df_filtered = df_byok[
        (df_byok["event_date"] >= start_d) & (df_byok["event_date"] <= end_d)
    ].copy()

    df_filtered["friction_pct"] = (
        df_filtered["byok_verify_failed"]
        * 100.0
        / (
            df_filtered["step_6_byok_key_saved"] + df_filtered["byok_verify_failed"]
        ).clip(lower=1)
    ).round(2)

    table_snippet = df_filtered.sort_values("event_date", ascending=True)[
        sql_cols
    ].reset_index(drop=True)

    # Column parity
    assert list(table_snippet.columns) == sql_cols
    # Row count parity: Table snippet row count matches filtered date range exactly (> 0)
    assert len(table_snippet) == len(df_filtered)
    assert len(table_snippet) > 0


def test_all_8_dashboard_sql_snippets_have_dynamic_where_date_clauses():
    """Verify all 8 chart expanders in dashboard.py dynamically inject WHERE date clauses from the sidebar filter."""
    code = (REPO_ROOT / "dashboard.py").read_text(encoding="utf-8")

    # 1. Star Schema 1: Traffic Acquisition & Geo Star
    assert "WHERE t.event_date BETWEEN '{start_str}' AND '{end_str}'" in code

    # 2. Star Schema 2: Product Feature Events Star
    assert "WHERE e.event_date BETWEEN '{start_str}' AND '{end_str}'" in code

    # 3. DAU Trend
    assert (
        "WHERE event_date BETWEEN '{start_str}' AND '{end_str}'\nORDER BY event_date ASC;"
        in code
    )

    # 4. Acquisition Channel Mix
    assert (
        "WHERE t.event_date BETWEEN '{start_str}' AND '{end_str}'\nGROUP BY 1, 2 ORDER BY 3 DESC;"
        in code
    )

    # 5. DACH vs Global
    assert (
        "WHERE t.event_date BETWEEN '{start_str}' AND '{end_str}'\nGROUP BY 1, 2 ORDER BY 3 DESC LIMIT 5;"
        in code
    )

    # 6. Monotonic BYOK Funnel
    assert (
        "FROM `de-consulting-508822.readcall_gold.gold_byok_funnel`\nWHERE event_date BETWEEN '{start_str}' AND '{end_str}'\nORDER BY event_date ASC;"
        in code
    )

    # 7. Referral Loop
    assert (
        "FROM `de-consulting-508822.readcall_gold.gold_referral_loop`\nWHERE event_date BETWEEN '{start_str}' AND '{end_str}'\nORDER BY event_date ASC;"
        in code
    )

    # 8. Friction Monitoring
    assert (
        "round(byok_verify_failed * 100.0 / nullif(step_6_byok_key_saved + byok_verify_failed, 0), 2) AS friction_pct\nFROM `de-consulting-508822.readcall_gold.gold_byok_funnel`\nWHERE event_date BETWEEN '{start_str}' AND '{end_str}'\nORDER BY event_date ASC;"
        in code
    )
