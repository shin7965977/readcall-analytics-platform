# 09: Standardize Weighted Semantic Metric Cards & Metric Naming

**What to build:** Refactor executive metric cards in `dashboard.py`. Eliminate arithmetic averages of daily ratios (`df["rate"].mean()`) to avoid Simpson's Paradox. Enforce dbt Semantic Layer definitions using weighted totals ($\sum \text{numerator} / \sum \text{denominator}$). Re-label `Cumulative DAU` to `Total User-Days (活躍人天總計)` with clear tooltip documentation.

**Blocked by:** None

**Status:** ready-for-agent

- [ ] Compute `Avg Engagement Rate` as `sum(engaged_sessions) / sum(total_sessions) * 100.0`.
- [ ] Compute `Aha! Activation Rate` as `sum(aha_users) / sum(dau) * 100.0`.
- [ ] Compute `BYOK Conversion Rate` as `sum(byok_key_saved) / sum(byok_modal_opened) * 100.0`.
- [ ] Rename `Cumulative DAU` to `Total User-Days (活躍人天總計)` across English and Chinese localizations.
- [ ] Update tooltips with precise mathematical and operational definitions.
