# Cloud Run Job for Serverless Pipeline Execution (Isolated readcall-pipeline-job)
resource "google_cloud_run_v2_job" "pipeline_job" {
  name     = "readcall-pipeline-job"
  location = var.region
  labels   = var.labels

  template {
    task_count = 1

    template {
      max_retries     = 1
      timeout         = "1800s"
      service_account = google_service_account.pipeline_sa.email

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.pipeline_repo.repository_id}/readcall-pipeline-runner:latest"

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }

        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "GCP_REGION"
          value = var.region
        }

        env {
          name  = "GA4_PROPERTY_ID"
          value = var.ga4_property_id
        }

        env {
          name  = "DBT_TARGET"
          value = "bigquery"
        }

        env {
          name  = "DBT_BQ_METHOD"
          value = "oauth"
        }

        env {
          name  = "DBT_BQ_DATASET"
          value = google_bigquery_dataset.silver.dataset_id
        }

        env {
          name  = "DLT_DESTINATION"
          value = "bigquery"
        }

        env {
          name  = "DLT_DATASET_NAME"
          value = google_bigquery_dataset.bronze.dataset_id
        }

        env {
          name  = "PIPELINE_TARGET"
          value = "all"
        }

        env {
          name  = "SIMULATION_DAYS"
          value = "90"
        }

        env {
          name  = "ELEMENTARY_REPORT_BUCKET"
          value = google_storage_bucket.observability_bucket.name
        }
      }
    }
  }

  depends_on = [
    google_project_service.enabled_apis,
    google_artifact_registry_repository.pipeline_repo
  ]
}

# Cloud Scheduler Job for Daily Automated Execution (Triggers Cloud Workflows)
resource "google_cloud_scheduler_job" "pipeline_schedule" {
  name             = "readcall-daily-pipeline-schedule"
  description      = "Daily trigger for ReadCall GA4 Product Analytics Pipeline via Cloud Workflows DAG (Runs at 02:30 UTC)"
  schedule         = "30 2 * * *"
  time_zone        = "Etc/UTC"
  attempt_deadline = "320s"
  region           = var.region

  http_target {
    http_method = "POST"
    uri         = "https://workflowexecutions.googleapis.com/v1/projects/${var.project_id}/locations/${var.region}/workflows/${google_workflows_workflow.pipeline_workflow.name}/executions"

    body = base64encode(jsonencode({
      argument = jsonencode({
        triggered_by = "cloud-scheduler"
      })
    }))

    oauth_token {
      service_account_email = google_service_account.pipeline_sa.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }

  depends_on = [
    google_project_service.enabled_apis,
    google_workflows_workflow.pipeline_workflow
  ]
}
