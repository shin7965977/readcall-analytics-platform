"""ReadCall Product Analytics Lakehouse - English Entry Point.

Features:
- 🛠️ View / Edit System Prompt
- 💾 Apply Custom Prompt
- 🔄 Reset to Default
"""

from __future__ import annotations

import streamlit as st

import dashboard

if __name__ == "__main__":
    st.session_state["lang"] = "en"
    dashboard.main() if hasattr(dashboard, "main") else None
