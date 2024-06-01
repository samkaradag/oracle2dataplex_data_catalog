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