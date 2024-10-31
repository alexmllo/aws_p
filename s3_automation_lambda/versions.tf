terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "region"
}

# backend
terraform {
  backend "s3" {
    bucket  = var.s3_bucket
    key     = var.s3_key
    region  = var.aws_region
    encrypt = true
  }
}
