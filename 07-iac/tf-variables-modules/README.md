# Challenge 34 — Terraform: Variables, Outputs, and Modules

## Scenario

> *"We copy-paste the same Terraform blocks for every environment — dev, staging, production.
> When we update a security group rule, we have to update it in three places.
> We need reusable modules so the infrastructure is DRY."*

Variables, outputs, and modules are what make Terraform scalable beyond a single engineer's
laptop. This challenge is about building reusable infrastructure blocks.

---

## What you will build

A module-based Terraform project:

```
tf-variables-modules/
├── modules/
│   └── web-service/        # reusable module: S3 + security group + config
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── dev/
│   │   ├── main.tf         # uses the module with dev values
│   │   └── terraform.tfvars
│   └── staging/
│       ├── main.tf         # uses the same module with staging values
│       └── terraform.tfvars
└── README.md
```

---

## Deliverables

```
tf-variables-modules/
├── modules/
│   └── web-service/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   └── staging/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── terraform.tfvars
└── README.md
```

---

## Functional requirements

### 1. The module — modules/web-service/

`modules/web-service/variables.tf`:

```hcl
variable "project_name" {
  type        = string
  description = "Name prefix for all resources"
}

variable "environment" {
  type        = string
  description = "dev, staging, or production"
}

variable "bucket_versioning" {
  type        = bool
  description = "Enable S3 versioning"
  default     = false
}

variable "allowed_ports" {
  type        = list(number)
  description = "List of ingress ports to open"
  default     = [80, 443]
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to all resources"
  default     = {}
}
```

`modules/web-service/main.tf`:

```hcl
locals {
  # Merge caller-provided tags with module-standard tags
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )
  bucket_name = "${var.project_name}-${var.environment}-assets"
}

resource "aws_s3_bucket" "assets" {
  bucket = local.bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id
  versioning_configuration {
    status = var.bucket_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_security_group" "web" {
  name        = "${var.project_name}-${var.environment}-sg"
  description = "Managed by Terraform web-service module"
  tags        = local.common_tags

  dynamic "ingress" {
    for_each = var.allowed_ports
    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

`modules/web-service/outputs.tf`:

```hcl
output "bucket_name" {
  value       = aws_s3_bucket.assets.bucket
  description = "The S3 bucket name"
}

output "bucket_arn" {
  value       = aws_s3_bucket.assets.arn
  description = "The S3 bucket ARN"
}

output "security_group_id" {
  value       = aws_security_group.web.id
  description = "The security group ID"
}
```

### 2. environments/dev/main.tf — calling the module

```hcl
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.aws_region
}

module "web" {
  source = "../../modules/web-service"    # relative path to the module

  project_name      = var.project_name
  environment       = "dev"
  bucket_versioning = false               # dev doesn't need versioning
  allowed_ports     = [80, 22]            # dev also allows SSH
  tags = {
    CostCenter = "engineering-dev"
  }
}
```

`environments/dev/outputs.tf`:

```hcl
output "bucket_name" {
  value = module.web.bucket_name    # referencing module outputs
}

output "security_group_id" {
  value = module.web.security_group_id
}
```

### 3. environments/staging/main.tf — same module, different values

```hcl
module "web" {
  source = "../../modules/web-service"

  project_name      = var.project_name
  environment       = "staging"
  bucket_versioning = true       # staging has versioning enabled
  allowed_ports     = [80, 443]  # staging: no SSH, HTTPS only
  tags = {
    CostCenter = "engineering-staging"
  }
}
```

### 4. Apply both environments

```bash
# Apply dev
cd environments/dev
terraform init
terraform apply -var-file="terraform.tfvars"

# Apply staging (completely separate state)
cd ../staging
terraform init
terraform apply -var-file="terraform.tfvars"
```

Both environments use the same module code. If you update the module,
both environments pick up the change on the next `terraform apply`.

### 5. Variable types to understand and use

| Type | Example | Use case |
|---|---|---|
| `string` | `"us-east-1"` | Region, names |
| `number` | `3` | Replica count |
| `bool` | `true` | Feature flags |
| `list(string)` | `["a","b"]` | Multiple values |
| `map(string)` | `{key="val"}` | Tag maps |
| `object({...})` | Complex config | Structured input |

### 6. locals — computed values

```hcl
locals {
  bucket_name = "${var.project_name}-${var.environment}-${random_id.suffix.hex}"
  is_prod     = var.environment == "production"
}

resource "aws_s3_bucket" "assets" {
  bucket = local.bucket_name
  # Conditional: enable versioning only in production
  dynamic "versioning" { ... }
}
```

---

## Guided questions

1. A module has a `variables.tf` with `default` values. Does the caller *have to* provide those variables? What happens if a required variable (no default) is not provided?
2. `locals` vs `variables` — what is the difference? When would you use `locals` over a `variable`?
3. The `dynamic "ingress"` block iterates over `var.allowed_ports`. What HCL keyword replaces `for_each` in a dynamic block, and what does `ingress.value` refer to?
4. You update `modules/web-service/main.tf` to add a new tag. You have 3 environments (dev, staging, production). Do all three automatically pick up the change, or do you need to run `terraform apply` in each?
5. Why is the module `source` a relative path (`../../modules/web-service`) rather than an absolute path? What other module sources does Terraform support?

---

## Stretch goals

- Publish your module to the [Terraform Registry](https://registry.terraform.io/) (requires a public GitHub repo)
- Add a `count` or `for_each` to create multiple S3 buckets from a single resource block
- Use `terraform-docs` to auto-generate documentation from your module's `variables.tf` and `outputs.tf`

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — optional vs required variables:**

**Q2 — locals vs variables:**

**Q3 — dynamic block for_each:**

**Q4 — module update propagation:**

**Q5 — module source types:**
