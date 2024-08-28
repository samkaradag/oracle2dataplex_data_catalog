# Configure Terraform Provider
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.80" # Or latest stable version
    }
  }
}

# Google Cloud Provider Configuration
provider "google" {
  project     = var.project_id
  region      = var.region
  user_project_override = true # Explicitly charge usage to your project
}

# Enable Data Catalog API if it's not already enabled
resource "google_project_service" "data_catalog" {
  service             = "datacatalog.googleapis.com"
  disable_on_destroy = false

  # Wait for the service to be enabled before creating the tag template
  timeouts {
    create = "30m" # Adjust timeout as needed
  }
}

# Enable Dataplex API
resource "google_project_service" "dataplex" {
  service = "dataplex.googleapis.com"
  disable_on_destroy = false
  timeouts {
    create = "30m"
  }
}

# Enable Data Lineage API
resource "google_project_service" "data_lineage" {
  service = "datalineage.googleapis.com"
  disable_on_destroy = false
  timeouts {
    create = "30m"
  }
}

# Data Catalog Tag Template Resource
resource "google_data_catalog_tag_template" "bigquery_column_descriptions" {
  # Use a resource dependency to ensure the Data Catalog API is enabled
  depends_on = [google_project_service.data_catalog]

  tag_template_id = "column_description_template"
  display_name    = "Column Description Template"

  fields {
    field_id     = "description"
    display_name = "Description"
    type {
      primitive_type = "STRING"
    }
    is_required = true
  }
  force_delete = true
}


# Create Service Account
resource "google_service_account" "dataplex_aspect_account" {
  account_id   = "dataplex-sa"
  display_name = "Dataplex  Service Account"
  disabled     = false
}


# Bind Role to Service Account
resource "google_project_iam_member" "dataplex_aspect_binding" {
  project = var.project_id
  role    = "roles/datacatalog.tagTemplateUser"
  member  = "serviceAccount:${google_service_account.dataplex_aspect_account.email}"
}

# Grant service account access to Dataplex API
resource "google_project_iam_member" "dataplex_aspect_access" {
  project = var.project_id
  role    = "roles/dataplex.viewer"
  member  = "serviceAccount:${google_service_account.dataplex_aspect_account.email}"
}

# Grant service account access to Data Lineage API
resource "google_project_iam_member" "data_lineage_aspect_access" {
  project = var.project_id
  role    = "roles/datalineage.viewer"
  member  = "serviceAccount:${google_service_account.dataplex_aspect_account.email}"
}

# Output Service Account Credentials
output "service_account_email" {
  value = google_service_account.dataplex_aspect_account.email
}
