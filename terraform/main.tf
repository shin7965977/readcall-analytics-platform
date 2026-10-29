# 1. Enable Required GCP APIs
locals {
  services = [
    "bigquery.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "cloudscheduler.googleapis.com",
    "workflows.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com"
  ]
}

resource "google_project_service" "enabled_apis" {
  for_each           = toset(local.services)
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# 2. BigQuery Medallion Architecture Datasets (Isolated readcall_* Namespace)
resource "google_bigquery_dataset" "bronze" {
  dataset_id                 = "readcall_bronze"
  friendly_name              = "ReadCall Bronze (Raw GA4 Telemetry)"
  description                = "Bronze Layer: Raw allowlisted ReadCall GA4 daily traffic and 32 product events (Zero-PII) managed by dlt"
  location                   = var.region
  delete_contents_on_destroy = var.delete_contents_on_destroy
  labels                     = merge(var.labels, { layer = "bronze" })

  depends_on = [google_project_service.enabled_apis]
}

resource "google_bigquery_dataset" "silver" {
  dataset_id                 = "readcall_silver"
  friendly_name              = "ReadCall Silver (Star Schema)"
  description                = "Silver Layer: Cleaned and normalized SaaS Star Schema (dim_channels, dim_devices_geo, dim_feature_catalog, fct_*) managed by dbt"
  location                   = var.region
  delete_contents_on_destroy = var.delete_contents_on_destroy
  labels                     = merge(var.labels, { layer = "silver" })

  depends_on = [google_project_service.enabled_apis]
}

resource "google_bigquery_dataset" "gold" {
  dataset_id                 = "readcall_gold"
  friendly_name              = "ReadCall Gold (PLG & Funnel Marts)"
  description                = "Gold Layer: Product growth, feature adoption, BYOK funnel, and referral loop marts for Streamlit and FastMCP"
  location                   = var.region
  delete_contents_on_destroy = var.delete_contents_on_destroy
  labels                     = merge(var.labels, { layer = "gold" })

  depends_on = [google_project_service.enabled_apis]
}

# 3. Artifact Registry for Container Images
resource "google_artifact_registry_repository" "pipeline_repo" {
  location      = var.region
  repository_id = "readcall-pipeline-repo"
  description   = "Docker repository for ReadCall GA4 Data Pipeline runner and dashboard container images"
  format        = "DOCKER"
  labels        = var.labels

  depends_on = [google_project_service.enabled_apis]
}

# 4. Pipeline Service Account and IAM Roles
resource "google_service_account" "pipeline_sa" {
  account_id   = "readcall-pipeline-sa"
  display_name = "Service Account for ReadCall Analytics Pipeline Runner"
  description  = "Dedicated runner identity for ReadCall GA4 dlt ingestion, dbt transformation, and Cloud Run"

  depends_on = [google_project_service.enabled_apis]
}

locals {
  pipeline_roles = [
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/artifactregistry.writer",
    "roles/workflows.invoker",
    "roles/run.developer",
    "roles/iam.serviceAccountUser"
  ]
}

resource "google_project_iam_member" "pipeline_sa_roles" {
  for_each = toset(local.pipeline_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

# 5. Cloud Storage Bucket for Elementary Observability Reports
resource "google_storage_bucket" "observability_bucket" {
  name                        = "${var.project_id}-readcall-observability"
  location                    = var.region
  force_destroy               = var.delete_contents_on_destroy
  uniform_bucket_level_access = true
  labels                      = merge(var.labels, { service = "observability" })

  depends_on = [google_project_service.enabled_apis]
}
