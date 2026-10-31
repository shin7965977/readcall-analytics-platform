# 08: Implement Extensible Dataset Registry & Fix NL2Chart Routing

**What to build:** Refactor natural language chart routing in `dashboard.py`. Replace hardcoded binary conditional dispatch (`scope.features if ... else scope.kpi`) with an open `DATASET_REGISTRY` mapping queries to `kpi`, `traffic`, `features`, `byok`, and `referral` scopes. Ensure preset button clicks for `Referral Loop Trend` and `BYOK Daily Friction` immediately route to appropriate scoped tables and render valid Plotly charts with zero silent failures.

**Blocked by:** Issue 07

**Status:** ready-for-agent

- [ ] Implement `DATASET_REGISTRY` dictionary in `dashboard.py`.
- [ ] Connect `"referral"` dataset intent to `scope.referral` with `event_date`, `step_2_referral_link_copied`, and `step_4_referral_unlock_success`.
- [ ] Connect `"byok"` dataset intent to `scope.byok` with `event_date`, `step_6_byok_key_saved`, and `byok_verify_failed`.
- [ ] Add graceful fallback with informative warning if an unrecognized dataset is encountered.
- [ ] Verify that clicking `🌱 Referral Loop Trend` immediately draws the dual-line trend chart.
