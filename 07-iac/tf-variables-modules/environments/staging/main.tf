terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  # Floci (local AWS emulator) - remove these lines for real AWS
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true
  endpoints {
    s3  = "http://localhost:4566"
    ec2 = "http://localhost:4566"
  }
}

module "web" {
  source = "../../modules/web-service"

  project_name      = var.project_name
  environment       = "staging"
  bucket_versioning = true
  allowed_ports     = [80, 443]
  tags = {
    CostCenter = "engineering-staging"
  }
}
