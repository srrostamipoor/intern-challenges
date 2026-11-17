terraform {
  backend "s3" {
    bucket         = "myapp-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "myapp-terraform-locks"
    encrypt        = true

    # Floci (local emulator) settings - remove for real AWS
    access_key                  = "test"
    secret_key                  = "test"
    use_path_style              = true
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_requesting_account_id  = true
    skip_region_validation      = true

    endpoints = {
      s3       = "http://localhost:4566"
      dynamodb = "http://localhost:4566"
    }
  }
}
