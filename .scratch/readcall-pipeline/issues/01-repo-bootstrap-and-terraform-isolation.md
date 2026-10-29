# 01: Repository Bootstrap & Isolated Terraform GCP Infrastructure (`readcall_*`)

**What to build:** Bootstrap the standalone `readcall-analytics-platform` project directory (`c:\Users\shin7\Downloads\CV\readcall-analytics-platform`), remove the legacy `platzi_store.py` adapter, configure domain documentation (`CONTEXT.md`, `SPEC.md`, `AGENTS.md`, `docs/agents/issue-tracker.md`), and update all Terraform IaC definitions (`terraform/`) to provision isolated GCP resources (`readcall_bronze`, `readcall_silver`, `readcall_gold`, `readcall-pipeline-job`, `readcall-pipeline-orchestrator`) so that zero legacy `platzi_*` resources are modified or overwritten.

**Blocked by:** None (can start immediately)

**Status:** closed

- [x] Standalone directory `c:\Users\shin7\Downloads\CV\readcall-analytics-platform` is initialized with clean project structure and `.gitignore` protecting credentials (`gcp-key.json`, `.env`).
- [x] Legacy `ingestion/sources/platzi_store.py` is completely removed from the new project.
- [x] `terraform/main.tf`, `terraform/cloud_run.tf`, and `terraform/workflows.tf` define `readcall_bronze`, `readcall_silver`, `readcall_gold`, `readcall-pipeline-job`, and `readcall-pipeline-orchestrator`.
- [x] `CONTEXT.md` and `SPEC.md` document the ReadCall ubiquitous language, 32-event taxonomy, and security boundaries.
