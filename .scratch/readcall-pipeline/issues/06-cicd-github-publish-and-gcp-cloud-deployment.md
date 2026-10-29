# 06: CI/CD Quality Gates, GitHub Repo Creation & Isolated GCP / Cloud Run Live Deployment

**What to build:** Execute full local verification (`ruff`, `pytest`, `dbt build`), create and push to the standalone GitHub repository `shin7965977/readcall-analytics-platform`, provision the isolated BigQuery datasets (`readcall_bronze`, `readcall_silver`, `readcall_gold`) in GCP project `de-consulting-508822`, run the production ELT pipeline to populate BigQuery, and deploy the standalone live Cloud Run service (`readcall-analytics-dashboard`) and Cloud Run Job (`readcall-pipeline-job`) without modifying any legacy `platzi_*` deployments.

**Blocked by:** 05: Bilingual Streamlit PLG Cockpit, Interactive System Prompt Editor & Stealth Recruiter Telemetry

**Status:** closed

- [x] `ruff check .` and `pytest tests/` pass with 0 errors.
- [x] Standalone GitHub repository `https://github.com/shin7965977/readcall-analytics-platform` is created and pushed with full bilingual documentation (`README.md`, `README_zh.md`).
- [x] BigQuery datasets `readcall_bronze`, `readcall_silver`, and `readcall_gold` are created and populated with transformed Gold tables in GCP (`de-consulting-508822`).
- [x] Cloud Run Job `readcall-pipeline-job` and live Streamlit Cloud Run Service `readcall-analytics-dashboard` are deployed and verified accessible via public URL while legacy `platzi_*` and `data-pipeline-consulting-demo-v01.streamlit.app` remain 100% untouched.
