# 03: dbt Medallion Models (Staging ➔ Silver ➔ Gold) & Semantic Layer (`semantic_models.yml`)

**What to build:** Replace the legacy e-commerce dbt models in `transform_dbt/` with ReadCall's SaaS Product Analytics Kimball Star Schema, Gold PLG Marts, and dbt Semantic Layer (`semantic_models.yml`).

**Blocked by:** 02: ReadCall GA4 Ingestion Adapter, Strict Allowlist & 90-Day Privacy Calibrator

**Status:** closed

- [x] Staging views (`stg_ga4_daily_traffic.sql`, `stg_ga4_events.sql`) cast types, enforce non-negative bounds, and normalize dimensions.
- [x] Silver dimensions (`dim_channels.sql`, `dim_devices_geo.sql` with `is_dach_region`, and `dim_feature_catalog.sql` mapping 32 events to 5 product modules, AARRR stages, and React `.tsx` source components) and facts (`fct_daily_traffic.sql`, `fct_feature_events.sql`) build cleanly.
- [x] Gold marts (`gold_daily_growth_kpi.sql`, `gold_feature_adoption.sql`, `gold_byok_funnel.sql`, `gold_referral_loop.sql`) materialize pre-pivoted funnel steps and pre-calculated conversion ratios.
- [x] `transform_dbt/models/semantic_models.yml` defines entities, dimensions, measures, ratio metrics (`aha_activation_rate`, `byok_conversion_rate`, `byok_verify_failure_rate`, `viral_k_factor`), component mappings, and health thresholds.
- [x] All dbt schema and integrity tests in `transform_dbt/models/schema.yml` pass `dbt test` with 0 errors.
