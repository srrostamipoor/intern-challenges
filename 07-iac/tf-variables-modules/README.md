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

**What I built:**
A reusable Terraform module, `modules/web-service`, that creates an S3 bucket,
the bucket versioning setting, and a security group whose open ports come from a
list variable (using a `dynamic "ingress"` block). Two environments, `dev` and
`staging`, call the same module with different values (versioning off/on, ports
80+22 vs 80+443, different cost-center tag) and each has its own state file.
Everything ran against Floci, a free local AWS emulator on `localhost:4566`
(no real AWS account); no EC2 instance is created, only the security group.

**What I observed:**
- `dev`: `Plan: 3 to add`; resource addresses are prefixed with `module.web.`.
  The bucket got four tags: `CostCenter` (from the environment), and `Project`,
  `Environment`, `ManagedBy` (from the module) merged by `merge()`. The security
  group had two `ingress` blocks (22 and 80) generated from `allowed_ports`.
  The versioning status was `Suspended`, and `apply` accepted it.
- `staging`: same module, versioning `Enabled`, ingress 443 and 80, different
  names (`myapp-staging-assets`, `myapp-staging-sg`). The two states are separate
  files (about 6.7 KB each), and the two security groups have different ids.
- Missing required input: removing `project_name` from the `module "web"` block
  made `terraform validate` fail with
  `Missing required argument ... The argument "project_name" is required`.
- Changing the module (adding an `Owner` tag): `plan` in both environments
  showed `0 to add, 2 to change, 0 to destroy`. After `apply` in `dev` only,
  `dev` said `No changes` and `staging` still showed `2 to change`, until I ran
  `apply` there too.
- Adding 443 to `allowed_ports` in `dev`: `plan` showed `1 to change` (the
  security group, in place). The `ingress` list was printed as old entries
  removed and new entries added; I did not find out why it prints 22 and 80 that
  way (I did not apply this change and reverted it).

**What I struggled with:**
(edit to match your own experience; these happened during my run)
- I first saved `variables.tf` in `modules/` instead of `modules/web-service/`,
  so it was not part of the module. A directory listing showed it.
- `terraform init` failed three times with
  `releases.hashicorp.com: unexpected EOF` while downloading the AWS provider
  (a large file over an unstable connection). I copied the provider I already had
  from the previous challenge into a plugin cache directory
  (`TF_PLUGIN_CACHE_DIR`) and copied its `.terraform.lock.hcl`; then `init` used
  the cache without downloading.
- I pressed Enter instead of typing `yes` at the `apply` prompt, which printed
  `Apply cancelled` and created nothing.

**What I'd do differently:**
(suggestions, edit freely)
- Set up a provider plugin cache before the first `init`, so each environment
  does not download the provider again.
- Check the folder layout (`dir`) after creating each file.
- Save the plan with `-out` and apply that exact plan.

---

## Guided questions - answers

**Q1 - optional vs required variables:**
A variable with a `default` is optional: if the caller does not set it, the
default is used. A variable without a `default` is required. If the module call
does not provide it, Terraform stops at validation with
`Missing required argument` (I saw this for `project_name`).

**Q2 - locals vs variables:**
A variable is an input from outside the module (the caller, a tfvars file or
`-var`). A local is a value computed inside the module and cannot be set from
outside. I use locals for things I would otherwise repeat, like the merged tag
map (used by both the bucket and the security group) or a computed name.

**Q3 - dynamic block:**
The `dynamic` block uses `for_each` to loop over a collection (here
`var.allowed_ports`); `content {}` is the body generated for each item. Inside
it, `ingress.value` is the current element (for example 80 or 22). The loop
variable is named after the dynamic block's label and can be renamed with
`iterator`. Adding 443 to the list produced one more `ingress` entry in the plan
without any new code.

**Q4 - module update propagation:**
No. All environments share the module code, but each one has its own state, so
a change in the module only takes effect where I run `terraform apply`.
I saw this: after the `Owner` tag change, `plan` showed pending changes in both
environments, and applying in `dev` left `staging` still pending.

**Q5 - module source types:**
A relative path keeps the project portable: it works on any machine and any
clone, while an absolute path exists on one computer only. Terraform also
supports the Terraform Registry, GitHub and generic Git URLs, Bitbucket, HTTP
URLs, S3 and GCS buckets, and local paths.
