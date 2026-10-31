# 07: Fix BYOK and Referral Funnel Monotonicity & Schema Mismatch

**What to build:** Refactor `gold_byok_funnel` and `gold_referral_loop` consumption in `dashboard.py` and `DashboardScope`. Replace zero-value ghost aliases (`step_1_reader_opened`) with authentic progression steps (`step_1_first_visit: 401`, `step_2_aha_interaction: 107`). Restructure the BYOK Funnel as a strictly monotonic, 5-stage progression ($401 \to 107 \to 55 \to 19 \to 18$). Decouple the trial limit wall into a dedicated micro-funnel metric to eliminate the bulging funnel artifact and impossible `Infinity%` conversion rates.

**Blocked by:** None (can start immediately)

**Status:** closed

- [x] Eliminate zero-value lookup on `step_1_reader_opened` and `step_2_ai_trial_inquiry` in `DashboardScope.byok_funnel`.
- [x] Connect Stage 1 to `step_1_first_visit` (401) and Stage 2 to `step_2_aha_interaction` (107).
- [x] Standardize Funnel stages in `dashboard.py` to ensure $S_1 \ge S_2 \ge S_3 \ge S_4 \ge S_5$.
- [x] Establish dedicated Trial Wall recovery card ($\text{Wall Hit} \to \text{Modal Opened} \to \text{Key Saved}$).
- [x] Synchronize Referral loop stages to eliminate cross-device event inversion (visited < unlocks).
