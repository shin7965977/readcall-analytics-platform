# Spec 0002: Elimination of Architectural Antipatterns & Cockpit Data Contract Hardening

**Status**: ready-for-agent  
**Category**: Data Platform Architecture, BI Semantic Integrity & Contract Hardening  
**Target Delivery**: ReadCall Analytics Cockpit & FastMCP Semantic Lakehouse  
**Related Specs**: [Spec 0001: ReadCall GA4 Product Analytics Platform](0001-readcall-ga4-analytics-platform.md)

---

## Problem Statement

During real-world executive usage and stress-testing of the ReadCall Analytics Platform, users and stakeholders identified several compounding architectural anomalies and data disconnects:

1. **Broken Funnel Semantics**: The 6-Stage BYOK conversion funnel displayed 0 for the first two stages (`1. Reader Opened` and `2. AI Inquiry`), an impossible `Infinity%` conversion rate on stage 3, and an unnatural "bulging funnel" where stage 4 (`ByokModal Opened: 55`) was larger than stage 3 (`Trial Limit Wall Hit: 31`). The Referral viral loop suffered similar bulging (`Unlock Succeeded: 2` > `Friend Visited Banner: 1`).
2. **Mathematical Inaccuracy (Average of Ratios)**: Executive KPI cards calculated monthly/quarterly engagement rates and Aha! activation rates using unweighted arithmetic means (`df[ratio].mean()`), violating foundational statistics (Simpson's Paradox) and diverging from the dbt Semantic Layer specification ($\sum \text{numerator} / \sum \text{denominator}$).
3. **Cumulative DAU Metric Mislabeling**: Daily active users were summed across dates into a single number labeled "Cumulative DAU", erroneously presenting "User-Days" as unique individuals and misrepresenting user scale.
4. **Dual-Track Logic Divergence**: Critical business metrics (e.g. `aha_users` threshold clamping and `offloaded_ai_compute_usd` cost calculations) used different formulas in dbt SQL versus Python fallback mirrors, destroying the Single Source of Truth principle.
5. **Consumer-Producer Routing Disconnect**: The Natural Language AI Chart Generator failed silently (showing no output or reaction) when querying Referral or BYOK trends because the consumer router in the dashboard hardcoded a binary dataset split (`features if ... else kpi`), dropping all other datasets.
6. **Silent Default Fallback**: When users filtered for dates containing no traffic, the scoping logic silently reverted to returning the entire 90-day dataset instead of accurately reporting an empty state.
7. **Cache Staleness & Pipeline Blindness**: Streamlit `@st.cache_data` locked data loading into 600-second memory blocks with static layer keys, blinding users to data refreshes after triggering ELT pipelines or applying code fixes.

---

## Solution

Implement an end-to-end architectural hardening and contract harmonization across the lakehouse, semantic layer, server tools, and dashboard visualization layer:

1. **Monotonic Funnel Contract**:
   - Redefine the BYOK Funnel as a strictly monotonic, drop-off sequence of unique user progression:
     $$\text{First Visit (401)} \longrightarrow \text{Aha! Interaction (107)} \longrightarrow \text{ByokModal Opened (55)} \longrightarrow \text{Get/Paste Key Clicked (19)} \longrightarrow \text{Key Saved (18)}$$
   - Harmonize column aliases between dbt marts and UI components, eliminating zero-value ghost columns and Infinity% artifacts.
   - Separate passive trial-wall friction into a dedicated micro-funnel rather than forcing it as a prerequisite in the main funnel.
2. **Weighted Semantic Metric Aggregation**:
   - Refactor all cockpit metric cards and summary tiles to strictly compute weighted ratio aggregations ($\frac{\sum \text{numerators}}{\sum \text{denominators}}$), 100% compliant with dbt Semantic Layer formulas.
   - Rename `Cumulative DAU` to `Total User-Days (活躍人天總計)` to ensure statistical integrity.
3. **Single Source of Truth Harmonization**:
   - Unify Python fallback generation in `mcp_server/server.py` to mirror the exact SQL logic of `transform_dbt/models/marts/gold_daily_growth_kpi.sql`.
4. **Extensible Dataset Registry**:
   - Replace brittle `if/else` dataset branches in `dashboard.py` with an open `DATASET_REGISTRY` mapping queries to `kpi`, `traffic`, `features`, `byok`, and `referral` scopes.
5. **Truthful Date Filtering**:
   - Refactor date scoping to return clean, empty datasets when a date range has no records, paired with friendly "No data in selected date range" UI states.
6. **Smart Cache Versioning**:
   - Incorporate pipeline run timestamps and model revision hashes into Streamlit cache keys, guaranteeing instantaneous, seamless cache invalidation upon pipeline execution.

---

## User Stories

1. As an executive reviewing the growth cockpit, I want conversion funnels to strictly decrease or maintain size stage-by-stage, so that I can accurately identify drop-off bottlenecks without confusing bulges.
2. As a product growth manager, I want the BYOK funnel to display genuine user numbers on stages 1 and 2, so that I never see blank bars or "Infinity%" on the dashboard.
3. As a growth lead, I want to see the true conversion from first visit to key save, so that I can report accurate PLG conversion rates to executive leadership.
4. As a growth analyst, I want the trial limit wall to be tracked as its own focused conversion path, so that non-linear users who open settings directly do not distort the trial wall recovery rate.
5. As a data analyst, I want cockpit average rates (Engagement Rate, Aha! Rate) to be calculated as total numerator over total denominator, so that Simpson's paradox does not produce mathematically false summaries.
6. As a business stakeholder, I want DAU totals across date ranges to be clearly labeled as "User-Days", so that I never mistake repeat sessions for distinct unique users.
7. As a finance director, I want the estimated offloaded AI compute cost savings to match whether I inspect them in BigQuery, FastMCP, or offline Streamlit, so that financial reporting remains consistent.
8. As a product analyst, I want to click the "Referral Loop Trend" shortcut button and have the chart generate immediately, so that I can inspect viral prompt sharing performance.
9. As a dashboard user, I want to type any natural language request regarding BYOK friction or referral performance and have the AI generator pick the appropriate dataset, so that charts never fail to render silently.
10. As a growth scientist, I want preset buttons in the AI chart generator to update the query input box instantly and trigger execution, so that exploration requires minimal manual re-typing.
11. As a business user, I want filtering for an inactive date range to show an honest zero or empty state, so that the dashboard does not silently jump back to showing 90 days of unrelated data.
12. As an analytics engineer, I want the dashboard to invalidate its cached queries immediately when I trigger an ELT pipeline run, so that I immediately see freshly ingested telemetry.
13. As a developer adding new charts to the dashboard, I want a centralized dataset registry, so that any new dataset added to `chart_generator.py` is automatically supported across the UI.
14. As a QA lead, I want CI/CD tests to verify that every preset chart query generates a valid chart object, so that regression breaks in chart generation are caught before merge.
15. As a platform engineer, I want CI/CD static analysis (AST inspection) to prevent any UI code from bypassing the scoped context container, so that data-binding disconnects are permanently impossible.

---

## Implementation Decisions

### 1. Data Contracts & Dataset Registry Pattern
Replace hardcoded branching in the natural language chart renderer with an extensible dispatch registry:

```python
DATASET_REGISTRY = {
    "kpi": lambda scope: scope.kpi,
    "traffic": lambda scope: scope.traffic,
    "features": lambda scope: scope.features,
    "byok": lambda scope: scope.byok,
    "referral": lambda scope: scope.referral,
}
```

Any unknown dataset falls back gracefully to `scope.kpi` while logging a structured warning.

### 2. Monotonic Funnel Specification
- **BYOK Funnel**:
  - `Stage 1 (Acquisition)`: `first_visit` (mapped to `step_1_first_visit`)
  - `Stage 2 (Activation)`: `aha_interaction` (mapped to `step_2_aha_interaction`)
  - `Stage 3 (Intent)`: `byok_modal_opened` (mapped to `step_4_byok_modal_opened`)
  - `Stage 4 (Attempt)`: `key_acquisition_attempt` (mapped to `step_5_key_acquisition_attempt`)
  - `Stage 5 (Completion)`: `byok_key_saved` (mapped to `step_6_byok_key_saved`)
- **Trial Wall Micro-Funnel (Dedicated Card)**:
  - `Trial Limit Wall Hit` ➔ `Modal Opened from Trial Wall` ➔ `Key Saved`.

### 3. Ratio Aggregation Formula Standardization
All aggregate cards in `dashboard.py` must adopt exact dbt Semantic Layer formulas:
- $\text{Avg Engagement Rate} = \frac{\sum \text{engaged\_sessions}}{\sum \text{total\_sessions}} \times 100\%$
- $\text{Aha! Activation Rate} = \frac{\sum \text{aha\_users}}{\sum \text{dau}} \times 100\%$
- $\text{BYOK Conversion Rate} = \frac{\sum \text{byok\_key\_saved}}{\sum \text{byok\_modal\_opened}} \times 100\%$
- $\text{Verification Failure Rate} = \frac{\sum \text{byok\_verify\_failed}}{\sum(\text{byok\_key\_saved} + \text{byok\_verify\_failed})} \times 100\%$

### 4. Honest Date Filtering Behavior
In `DashboardScope._filter_date`:
Remove `return filtered if not filtered.empty else df`. When no records match, return an empty DataFrame with preserved columns. Downstream UI visualizations must display an informative notice: *"No activity recorded in selected date range."*

### 5. Single Source of Truth in Python Fallback Mirror
Update `mcp_server/server.py` to replicate `gold_daily_growth_kpi.sql` logic verbatim:
- `aha_users`: calculated based on actual `raw_aha_users` with proportional capping against `dau`.
- `offloaded_ai_compute_usd`: calculated as `(ai_inference_events * 0.0025) + (byok_keys_saved * 0.45)`.

---

## Testing Decisions

### Seam Architecture
- **Primary Testing Seam**: `DashboardScope` and `render_dynamic_chart` function boundary. Testing here verifies that data input shapes, date filter slicing, and Plotly figure generation operate harmoniously as an integrated unit.
- **Secondary Testing Seam**: AST static code inspection on `dashboard.py` to prevent anti-pattern regression.

### Test Commitments
1. **Funnel Monotonicity Test**: Assert that for full-range and filtered ranges, funnel stages adhere to $S_1 \ge S_2 \ge S_3 \ge \dots$ with all stages having non-zero values.
2. **Weighted Metric Assertions**: Assert that summary card rates match the division of overall sums rather than the mean of column values.
3. **NL2Chart Coverage Test**: Loop through all preset queries and semantic intents (`"byok"`, `"referral"`, `"features"`, `"kpi"`) and assert that `render_dynamic_chart` returns a valid, non-null `go.Figure` with correct traces.
4. **Empty Range Resilience Test**: Pass non-overlapping date ranges into `DashboardScope` and assert that no exceptions are raised and all properties return clean empty structures without falling back to 90 days.
5. **AST Guard Expansion**: Extend the static analyzer to verify that no direct `.mean()` is called on ratio columns in dashboard metric cards.

---

## Out of Scope

- Modifying the underlying GA4 raw BigQuery ingestion schema or creating new GA4 custom dimensions.
- Changing the authentication flow or Google AI Studio Gemini API key generation process.
- Replacing Streamlit with a full React/Next.js frontend.

---

## Further Notes

All changes must maintain 100% backward compatibility with `pipeline_runner.py`, `mcp_server/server.py`, and `fastmcp_diagnostic.py`. CI test execution must continue to pass cleanly within 30 seconds.
