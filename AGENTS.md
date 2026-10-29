# Project Agent Guidelines — ReadCall Analytics Platform

## Agent skills

### Issue tracker

Issues and specifications are tracked as local markdown files under `.scratch/`. See [`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md).

### Domain docs

This repository uses a single-context domain layout centered on [`CONTEXT.md`](CONTEXT.md) and [`docs/adr/`](docs/adr/). See [`docs/agents/domain.md`](docs/agents/domain.md).

### PLG Product Analytics, Founding Marketing & FastMCP Intelligence

When answering questions about ReadCall product diagnostics, GA4 telemetry, BYOK funnel friction, referral viral loops, or using FastMCP tools, enforce:
- **Conclusion-First Product Analytics**: Pinpoint the primary AARRR binding constraint first without corporate fluff.
- **Semantic Layer & Show the Numbers**: Quantify `aha_activation_rate`, `byok_conversion_rate`, `byok_verify_failure_rate`, and `viral_k_factor`, tracing drop-offs directly to ReadCall React components (`ByokModal.tsx`, `LinguisticInspectorContent.tsx`, `TutorCustomPromptModal.tsx`, `QuizModal.tsx`).
- **Actionable PLG & CRO Interventions**: Concrete 30-60-90 day product UX, onboarding, and programmatic SEO recommendations.
