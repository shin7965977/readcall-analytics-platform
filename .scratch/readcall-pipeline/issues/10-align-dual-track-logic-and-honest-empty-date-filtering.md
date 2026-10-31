# 10: Align Dual-Track Logic & Implement Honest Date Filtering

**What to build:** Synchronize Python fallback formulas in `mcp_server/server.py` with `transform_dbt/models/marts/gold_daily_growth_kpi.sql` (Aha user capping and offloaded AI compute cost formula). Refactor `DashboardScope._filter_date` to remove silent fallback to full 90-day range on empty slices, displaying clean empty-state UI feedback instead.

**Blocked by:** None

**Status:** closed

- [x] Update `aha_users` in `server.py` to mirror `gold_daily_growth_kpi.sql` logic instead of flat 0.71 multiplier.
- [x] Update `offloaded_ai_compute_usd` in `server.py` to compute `ai_inference_events * 0.0025 + byok_keys_saved * 0.45`.
- [x] Remove `return filtered if not filtered.empty else df` in `DashboardScope._filter_date`.
- [x] Add empty-state UI guards in `dashboard.py` showing "No activity recorded in selected date range".
