locals {
  prefix = var.prefix
  common_tags = {
    Projects   = var.project
    Contact    = var.contact
    Managed_by = "Terraform"
  }
}
