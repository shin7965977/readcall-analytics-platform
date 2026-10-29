"""Stealth Recruiter Telemetry for ReadCall Portfolio Cockpit.

Silently tracks when HR / Hiring Managers open the portfolio link from a resume
or email (`?utm_campaign=company_name` or `?ref=company_name`) and forwards
`portfolio_opened`, `portfolio_tab_viewed`, and `portfolio_ai_tested` events to
`PORTFOLIO_TRACKER_GA_ID`.

Strict Isolation Rules:
1. Respects `?developer=true` opt-out (`readcall_ga_opt_out` in localStorage).
2. Zero visual footprint (`height=0, width=0`).
3. All events are prefixed with `portfolio_` so `ga4_adapter.py` and `stg_ga4_events.sql`
   strictly exclude them from the ReadCall product analytics lakehouse.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any

DEFAULT_PORTFOLIO_GA_ID = "G-CR2LW8PH5M"
ALLOWED_PORTFOLIO_EVENTS = {
    "portfolio_opened",
    "portfolio_tab_viewed",
    "portfolio_ai_tested",
}


def _first_val(val: Any, default: str = "") -> str:
    if val is None:
        return default
    if isinstance(val, list | tuple):
        return str(val[0]) if val else default
    return str(val)


def extract_recruiter_context(query_params: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Parse URL query parameters (`?utm_campaign=`, `?ref=`, `?developer=`) into telemetry context."""
    params = query_params or {}
    dev_raw = _first_val(params.get("developer"), "").strip().lower()
    is_opted_out = dev_raw in ("true", "1", "yes")

    utm_campaign = _first_val(params.get("utm_campaign"), "").strip()
    ref_param = _first_val(params.get("ref"), "").strip()
    company_param = _first_val(params.get("company"), "").strip()
    utm_source = _first_val(params.get("utm_source"), "").strip() or "resume_link"

    recruiter_ref = utm_campaign or ref_param or company_param or "direct"

    return {
        "recruiter_ref": recruiter_ref,
        "utm_campaign": utm_campaign or recruiter_ref,
        "utm_source": utm_source,
        "is_opted_out": is_opted_out,
    }


def build_stealth_ga4_snippet(
    event_name: str = "portfolio_opened",
    context: Mapping[str, Any] | None = None,
    extra_params: Mapping[str, Any] | None = None,
    ga_id: str | None = None,
) -> str:
    """Build a 0x0px hidden GA4 gtag.js HTML snippet for recruiter open tracking."""
    if not event_name.startswith("portfolio_"):
        raise ValueError(f"Stealth telemetry events must start with 'portfolio_': got {event_name}")

    ctx = dict(context or extract_recruiter_context({}))
    if ctx.get("is_opted_out"):
        return ""

    measurement_id = (ga_id or os.getenv("PORTFOLIO_TRACKER_GA_ID", DEFAULT_PORTFOLIO_GA_ID)).strip()
    if not measurement_id:
        return ""

    payload: dict[str, Any] = {
        "recruiter_ref": ctx.get("recruiter_ref", "direct"),
        "utm_campaign": ctx.get("utm_campaign", "direct"),
        "utm_source": ctx.get("utm_source", "resume_link"),
        "transport_type": "beacon",
    }
    if extra_params:
        for k, v in extra_params.items():
            if v is not None:
                payload[str(k)] = v

    payload_json = json.dumps(payload, ensure_ascii=False)
    event_json = json.dumps(event_name, ensure_ascii=False)
    ga_id_json = json.dumps(measurement_id, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
<script>
(function() {{
  try {{
    if (window.localStorage && window.localStorage.getItem('readcall_ga_opt_out') === 'true') {{
      return;
    }}
  }} catch (e) {{}}
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', {ga_id_json}, {{ 'send_page_view': false }});
  gtag('event', {event_json}, {payload_json});
}})();
</script>
</head>
<body style="margin:0;padding:0;overflow:hidden;width:0;height:0;display:none;"></body>
</html>"""


def inject_stealth_telemetry(
    event_name: str = "portfolio_opened",
    extra_params: Mapping[str, Any] | None = None,
) -> bool:
    """Inject the 0px stealth GA4 snippet into a live Streamlit page without visible UI elements."""
    try:
        import streamlit as st
        import streamlit.components.v1 as components

        qp = dict(st.query_params) if hasattr(st, "query_params") else {}
        ctx = extract_recruiter_context(qp)
        if ctx.get("is_opted_out"):
            return False

        # Deduplicate repeated identical fires within the same Streamlit session
        session_key = f"_stealth_fired_{event_name}_{json.dumps(extra_params or {}, sort_keys=True)}"
        if hasattr(st, "session_state") and st.session_state.get(session_key):
            return False

        snippet = build_stealth_ga4_snippet(
            event_name=event_name,
            context=ctx,
            extra_params=extra_params,
        )
        if not snippet:
            return False

        components.html(snippet, height=0, width=0)
        if hasattr(st, "session_state"):
            st.session_state[session_key] = True
        return True
    except Exception:
        return False
