# Terraform for AI SDLC Gemini Cloud (REQ-F-GCP-001)

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

variable "project_id" {
  type        = string
  description = "The GCP Project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "The GCP Region"
}

# 1. Firestore Database (Native Mode)
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = "nam5" # Multi-region for reliability
  type        = "FIRESTORE_NATIVE"
}

# 2. Cloud Storage for Artifacts and Snapshots
resource "google_storage_bucket" "artifacts" {
  name          = "aisdlc-${var.project_id}-artifacts"
  location      = var.region
  force_destroy = true
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
}

# 3. Vertex AI API Enablement
resource "google_project_service" "vertex_ai" {
  service = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

# 4. Pub/Sub for Sensory Service and Human Reviews
resource "google_pubsub_topic" "sdlc_events" {
  name = "sdlc-events-topic"
}

# 5. IAM Service Account for the Iterate Engine (Cloud Run)
resource "google_service_account" "iterate_engine_sa" {
  account_id   = "aisdlc-iterate-engine"
  display_name = "AI SDLC Iterate Engine Service Account"
}

# 6. IAM Roles for the Service Account
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.iterate_engine_sa.email}"
}

resource "google_project_iam_member" "storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.iterate_engine_sa.email}"
}

resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.iterate_engine_sa.email}"
}

# 7. Cloud Workflows for Orchestration (Optional)
resource "google_project_service" "workflows" {
  service = "workflows.googleapis.com"
  disable_on_destroy = false
}

output "artifact_bucket" {
  value = google_storage_bucket.artifacts.name
}

output "pubsub_topic" {
  value = google_pubsub_topic.sdlc_events.name
}
