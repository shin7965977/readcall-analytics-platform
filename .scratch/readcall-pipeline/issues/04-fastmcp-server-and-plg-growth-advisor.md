# 04: FastMCP Gold Governance Server & PLG Growth Lead Diagnostic Engine

**What to build:** Refactor `mcp_server/server.py`, `fastmcp_diagnostic.py`, and `chart_generator.py` for ReadCall's SaaS Product Analytics domain. Restrict AI query access strictly to `readcall_gold`, expose 5 specialized tools (including `get_semantic_definitions` reading `semantic_models.yml`), and adopt the pragmatic **SaaS Head of Growth & Staff Product Data Scientist** persona powered by the *Founding Marketing* (AARRR / CRO / Referral) skill framework.

**Blocked by:** 03: dbt Medallion Models (Staging ➔ Silver ➔ Gold) & Semantic Layer (`semantic_models.yml`)

**Status:** closed

- [x] `mcp_server/server.py` enforces `ALLOWED_DATASET = "readcall_gold"` and exposes `get_daily_growth_kpi`, `get_feature_adoption`, `get_byok_funnel`, `get_referral_loop`, and `get_semantic_definitions`.
- [x] `fastmcp_diagnostic.py` uses the pragmatic SaaS Head of Growth & Staff Product Data Scientist system prompt (dropping artificial MBB partner titles and synthetic subscription ARR in favor of real PLG funnel, UX component attribution, and CRO actions).
- [x] `chart_generator.py` supports natural language chart generation (NL2Chart) across ReadCall's 4 Gold marts in both Traditional Chinese and English.
- [x] Unit tests verify `sanitize_dataset_access` blocks `readcall_bronze` and `readcall_silver`.
