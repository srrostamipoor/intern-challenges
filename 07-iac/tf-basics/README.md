# Challenge 33 — Terraform: Providers, Resources, and State

## Scenario

> *"We've been clicking around in the AWS console to create infrastructure.
> Nobody knows what's running or why. If we lost the console access tomorrow,
> we couldn't recreate it. We need everything defined in code."*

Terraform lets you describe infrastructure as code (HCL), apply it, and track what
was created in a state file. This is the foundation of every modern infrastructure team.

---

## What you will build

Using **LocalStack** (a free AWS simulator that runs locally — no real AWS account needed
for the core exercises) or a real AWS free-tier account:

1. A Terraform configuration that provisions an S3 bucket and an EC2-equivalent resource
2. A remote state backend (S3 bucket for state + DynamoDB for locking)
3. A clear demonstration of `plan` → `apply` → `destroy` cycle

---

## Deliverables

```
tf-basics/
├── main.tf          # provider + resources
├── variables.tf     # input variables
├── outputs.tf       # output values
├── backend.tf       # remote state configuration
├── terraform.tfvars # variable values (in .gitignore)
├── .gitignore
└── README.md
```

---

## Functional requirements

### 1. Install Terraform

```bash
# Ubuntu/Debian
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

terraform version
```

### 2. Option A: LocalStack (no AWS account required)

```bash
pip install localstack awscli-local
localstack start -d    # starts AWS services locally

# Configure aws CLI to point at LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
```

### 3. main.tf — provider + resources

```hcl
terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  # LocalStack endpoint — remove these lines for real AWS
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  endpoints {
    s3 = "http://localhost:4566"
    ec2 = "http://localhost:4566"
  }
}

# Resource 1: S3 bucket for app assets
resource "aws_s3_bucket" "assets" {
  bucket = "${var.project_name}-assets-${var.environment}"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Resource 2: Security group (EC2 equivalent)
resource "aws_security_group" "web" {
  name        = "${var.project_name}-web-sg"
  description = "Allow HTTP and SSH"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}
```

### 4. variables.tf

```hcl
variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be dev, staging, or production"
  }
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH"
  type        = string
  default     = "0.0.0.0/0"
}
```

### 5. outputs.tf

```hcl
output "bucket_name" {
  description = "The name of the S3 assets bucket"
  value       = aws_s3_bucket.assets.bucket
}

output "bucket_arn" {
  description = "The ARN of the S3 assets bucket"
  value       = aws_s3_bucket.assets.arn
}

output "security_group_id" {
  description = "The ID of the web security group"
  value       = aws_security_group.web.id
}
```

### 6. terraform.tfvars (in .gitignore)

```hcl
project_name     = "myapp"
environment      = "dev"
allowed_ssh_cidr = "203.0.113.0/24"
```

### 7. The plan → apply → destroy cycle

```bash
# Initialize — downloads the provider plugin
terraform init

# Preview — what would be created/changed/destroyed
terraform plan

# Apply — create the resources (prompts for confirmation)
terraform apply

# Inspect what was created
terraform show
terraform state list

# Look at the state file
cat terraform.tfstate   # this is why you don't edit it by hand

# Make a change — add a tag to the bucket
# Edit main.tf, add: Owner = "sara" to the tags
terraform plan          # see exactly what changes
terraform apply         # apply only the diff

# Clean up
terraform destroy
```

### 8. backend.tf — remote state (understand the concept, implement if you have real AWS)

```hcl
# This stores the state file in S3 and uses DynamoDB for locking
# so multiple team members can't apply at the same time

terraform {
  backend "s3" {
    bucket         = "myapp-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "myapp-terraform-locks"
    encrypt        = true
  }
}
```

**Why remote state matters:** If the state file lives on one person's laptop and they're
on holiday, no one else can run Terraform. With remote state, the team shares one source of truth.

### 9. .gitignore

```gitignore
# Terraform state — contains sensitive values (passwords, IDs)
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl

# Variables with real values
terraform.tfvars
*.auto.tfvars
```

---

## Key concepts table

| Concept | What it is |
|---|---|
| Provider | Plugin that knows how to talk to a cloud API (AWS, GCP, Azure, etc.) |
| Resource | A single piece of infrastructure (an S3 bucket, a VM, a DNS record) |
| State file | Terraform's record of what it created — maps config to real resources |
| Plan | A dry run that shows what `apply` would do |
| Apply | Actually creates/updates/deletes resources to match the config |
| Destroy | Deletes everything tracked in the state file |

---

## Guided questions

1. You run `terraform apply` and it creates 5 resources. You then delete one resource manually in the AWS console. What does `terraform plan` show next time you run it?
2. The state file contains the real IDs, ARNs, and sometimes secrets for everything Terraform created. Why is it dangerous to commit it to Git?
3. What is state locking (DynamoDB table) and what problem does it prevent?
4. You rename a resource block in `main.tf` from `aws_s3_bucket.assets` to `aws_s3_bucket.static`. What does `terraform plan` say? What is the safer way to rename without destroying and recreating?
5. What is the difference between `terraform destroy` and deleting everything manually in the console? Which leaves your state file in a clean state?

---

## Stretch goals

- Use `terraform import` to bring an existing manually-created resource under Terraform management
- Add a `locals {}` block to compute the bucket name once and reuse it across resources
- Create a second workspace (`terraform workspace new staging`) with different variable values

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**What I struggled with:**

**What the state file contained that surprised me:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — manual deletion, terraform plan:**

**Q2 — state file in Git:**

**Q3 — state locking:**

**Q4 — renaming a resource:**

**Q5 — terraform destroy vs manual delete:**
