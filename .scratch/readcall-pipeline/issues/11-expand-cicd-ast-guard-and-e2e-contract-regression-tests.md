# 11: Expand CI/CD AST Guards & E2E Contract Regression Tests

**What to build:** Extend `tests/test_dashboard_scope.py` with comprehensive contract regression assertions. Add tests verifying: (1) Funnel monotonicity ($S_1 \ge S_2 \ge \dots$), (2) Weighted metric ratio assertions vs arithmetic mean, (3) NL2Chart coverage across all datasets and presets returning valid `go.Figure` instances, and (4) AST static linter banning `.mean()` on ratio columns and ensuring all visualization calls consume `scope`.

**Blocked by:** Issues 07, 08, 09, 10

**Status:** closed

- [x] Add `test_funnel_monotonicity_and_positive_stages` asserting $S_1 \ge S_2 \ge \dots > 0$.
- [x] Add `test_weighted_metric_card_calculations` confirming no Simpson's Paradox.
- [x] Add `test_nl2chart_all_presets_and_registry_coverage` testing all queries against `render_dynamic_chart`.
- [x] Add `test_empty_date_range_graceful_handling` verifying clean empty responses on out-of-bounds dates.
- [x] Expand AST test `test_ast_guard_no_ratio_mean_in_metric_cards` in `test_dashboard_scope.py`.
