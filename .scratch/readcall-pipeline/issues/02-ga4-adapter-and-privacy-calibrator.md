# 02: ReadCall GA4 Ingestion Adapter, Strict Allowlist & 90-Day Privacy Calibrator

**What to build:** Implement `ingestion/sources/ga4_adapter.py` and update `ingestion/run_ingest.py` and `pipeline_runner.py` to ingest ReadCall's GA4 telemetry into `readcall_bronze` (`raw_ga4_daily_traffic` and `raw_ga4_events`). Enforce a strict 32-event allowlist (`ALLOWED_READCALL_EVENTS`), strip all PII and recruiter-tracking traffic (`portfolio_*`, `utm_source=resume`), and provide deterministic 90-day privacy-preserving calibrated scaling by default (with `READCALL_RAW_MODE=true` supporting unscaled raw GA4 counts).

**Blocked by:** 01: Repository Bootstrap & Isolated Terraform GCP Infrastructure (`readcall_*`)

**Status:** closed

- [x] `ingestion/sources/ga4_adapter.py` implements `ReadCallGA4Adapter` yielding canonical `raw_ga4_daily_traffic` and `raw_ga4_events` records.
- [x] Strict event allowlist permits only the 32 ReadCall product telemetry events and drops any `portfolio_*` or `utm_source=resume` records at ingestion time.
- [x] `raw_ga4_daily_traffic` and `raw_ga4_events` are physically separated in Bronze to prevent session-vs-event scope fan-out duplication.
- [x] Default mode generates 90 days of calibrated data anchored to real ReadCall GA4 (`properties/559361789`) distributions; setting `READCALL_RAW_MODE=true` returns raw unscaled counts.
- [x] `dlt` pipeline loads both DuckDB (`local_warehouse.duckdb`) and BigQuery (`readcall_bronze`) cleanly with incremental watermark tracking on `updated_at`.
- [x] Unit tests in `tests/test_ga4_adapter.py` verify schema compliance, allowlist filtering, and zero-PII guarantees.
