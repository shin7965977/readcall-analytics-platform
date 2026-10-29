# Technical Specification — ReadCall Analytics Platform

See the canonical specification file under `.scratch/specs/`:
👉 [Spec 0001: ReadCall GA4 Product Analytics, PLG Lakehouse & AI Growth Platform](file:///c:/Users/shin7/Downloads/CV/readcall-analytics-platform/.scratch/specs/0001-readcall-ga4-analytics-platform.md)

### Key Summaries
- **Source Product**: **ReadCall** (`https://readcall.app` / [`shin7965977/readcall`](https://github.com/shin7965977/readcall)) — AI-powered German reading, morphological breakdown, 6-tense verb conjugation, and active recall platform.
- **Architecture**: Pluggable GA4 Ingestion (`dlt` + `ga4_adapter.py`) + Isolated Medallion Lakehouse (`BigQuery readcall_bronze / readcall_silver / readcall_gold`) + Transformations & Semantic Layer (`dbt-core` + `semantic_models.yml`) + Serverless Orchestration (`Cloud Scheduler` + `Cloud Workflows` + `Cloud Run Jobs`) + Declarative IaC (`Terraform`) + PLG AI Advisor (`FastMCP` + Interactive Prompt Playground).
- **Security & Privacy**:
  - **Zero-PII Boundary**: Only aggregated dimensions and strict allowlisted product events are ingested.
  - **Privacy-Preserving 90-Day Calibrated Scaling**: Protects raw early-stage commercial figures on public showcase while preserving exact real-world GA4 conversion distributions (`READCALL_RAW_MODE=true` switches to unscaled raw counts).
  - **Stealth Recruiter Telemetry**: Invisibly tracks `?utm_campaign=` / `?ref=` opens via `portfolio_opened`, `portfolio_tab_viewed`, and `portfolio_ai_tested` to a dedicated GA4 stream without ever exposing recruiter traffic on the dashboard UI or BigQuery tables.
- **Domain & Semantic Layer**: Strictly aligned with [`CONTEXT.md`](file:///c:/Users/shin7/Downloads/CV/readcall-analytics-platform/CONTEXT.md).
