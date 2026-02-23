# Gemini Cloud Genesis - Observability Module
# Implements: ADR-GC-006 (Multi-tenant Observability)

variable "region" {
  type        = string
  description = "GCP Region"
  default     = "us-central1"
}

# Firestore Database (Native Mode)
resource "google_firestore_database" "default" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# Indexes for Events (Time-series queries)
resource "google_firestore_index" "events_timestamp" {
  database = google_firestore_database.default.name
  collection = "events"

  fields {
    field_path = "timestamp"
    order      = "DESCENDING"
  }
  
  fields {
    field_path = "project"
    order      = "ASCENDING"
  }
}

# BigQuery for Aggregated Telemetry
resource "google_bigquery_dataset" "genesis_telemetry" {
  dataset_id                  = "genesis_telemetry"
  friendly_name               = "Genesis Methodology Telemetry"
  description                 = "Aggregated event logs from all Genesis projects"
  location                    = "US"
  default_table_expiration_ms = 31536000000 # 1 year
}

resource "google_bigquery_table" "events_log" {
  dataset_id = google_bigquery_dataset.genesis_telemetry.dataset_id
  table_id   = "events_log"

  time_partitioning {
    type = "DAY"
    field = "timestamp"
  }

  schema = <<EOF
[
  {
    "name": "event_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  },
  {
    "name": "tenant",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "project",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "event_type",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "data_json",
    "type": "JSON",
    "mode": "NULLABLE"
  }
]
EOF
}
