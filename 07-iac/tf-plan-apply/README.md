# Challenge 35 — Terraform: plan vs apply, State Locking, and Drift

## Scenario

> *"Someone ran `terraform apply` while I was also running it and they overwrote my changes.
> Also, someone added a firewall rule manually in the console and now terraform says
> it will delete it. How do we prevent both of these from happening?"*

`plan` vs `apply`, state locking, and drift detection are the operational discipline layer
of Terraform. This challenge focuses on understanding what happens at each step and
what can go wrong in a team environment.

---

## What you will build

A set of Terraform experiments that demonstrate:

1. Reading and understanding a `terraform plan` output in detail
2. Simulating and detecting **drift** (out-of-band manual changes)
3. Resolving drift with `terraform apply` or `terraform import`
4. Simulating a state lock conflict

---

## Deliverables

```
tf-plan-apply/
├── main.tf
├── variables.tf
├── outputs.tf
├── scenarios/
│   ├── 01-read-plan-output.md    # annotated plan output with explanation
│   ├── 02-drift-demo.md          # steps to simulate and detect drift
│   └── 03-lock-demo.md           # state lock demonstration
└── README.md
```

---

## Functional requirements

### 1. Understand plan output in detail

Run `terraform plan` and save the output. Then annotate what each symbol means:

```
Terraform will perform the following actions:

  # aws_s3_bucket.assets will be created           ← + means CREATE
  + resource "aws_s3_bucket" "assets" {
      + bucket = "myapp-dev-assets"
      + id     = (known after apply)               ← only known once resource is created
    }

  # aws_security_group.web will be updated in-place ← ~ means UPDATE (no destroy)
  ~ resource "aws_security_group" "web" {
      ~ description = "old description" -> "new description"
        id          = "sg-abc123"        ← = means unchanged
    }

  # aws_s3_bucket.old will be destroyed             ← - means DESTROY
  - resource "aws_s3_bucket" "old" {
      - bucket = "myapp-old" -> null
    }

  # aws_db_instance.db must be replaced             ← -/+ means DESTROY then CREATE
  -/+ resource "aws_db_instance" "db" {
      ~ allocated_storage = 20 -> 50   # forces replacement
    }

Plan: 1 to add, 1 to change, 1 to destroy, 1 to replace.
```

In `scenarios/01-read-plan-output.md`, write your own annotated version of a real plan from your config.

### 2. Simulate and detect drift

```bash
# Step 1: Apply your config — creates an S3 bucket and security group
terraform apply -auto-approve

# Step 2: Simulate a manual change (drift)
# Manually add a tag to the S3 bucket via AWS CLI (or LocalStack)
aws s3api put-bucket-tagging \
  --bucket myapp-dev-assets \
  --tagging 'TagSet=[{Key=ManualTag,Value=AddedByHand}]'

# Step 3: Run plan — Terraform detects the drift
terraform plan
# Output: ~ will update resource "aws_s3_bucket" — remove ManualTag

# Step 4: Apply — Terraform brings reality back to what the code says
terraform apply
```

This is **drift**: real infrastructure has diverged from the Terraform config.
`terraform plan` always detects it. `terraform apply` fixes it.

**Also demonstrate drift in the other direction** — deleting a resource Terraform doesn't know about:

```bash
# Add a tag to the Terraform config that doesn't exist in real infra
# (simulate an unapplied config change)
# In main.tf, add: NewTag = "not yet applied"
terraform plan
# Shows: ~ will add NewTag to the bucket
```

Document both drift scenarios in `scenarios/02-drift-demo.md`.

### 3. terraform refresh and terraform state

```bash
# Sync Terraform's state with real infrastructure (read actual state)
terraform refresh

# List all resources in state
terraform state list

# Show the current state of one resource
terraform state show aws_s3_bucket.assets

# Remove a resource from state WITHOUT destroying it
# (use case: you want to manage it outside Terraform)
terraform state rm aws_s3_bucket.assets
# After this: `terraform plan` will want to recreate the bucket
# but the bucket still exists in AWS

# Re-import it back
terraform import aws_s3_bucket.assets myapp-dev-assets
```

### 4. State locking — understand the concept

With a DynamoDB backend, state locking works like this:

```
Team member A runs: terraform apply
  → Terraform writes a lock to DynamoDB: { "ID": "uuid", "Who": "sara@laptop" }
  → Applies changes
  → Releases the lock

Team member B tries to run: terraform apply at the same time
  → Terraform reads DynamoDB, finds an active lock
  → Error: "Error acquiring the state lock"
  → B must wait or force-unlock (risky)
```

To simulate this without a real DynamoDB table:

```bash
# In terminal 1: start a slow apply (add sleep to a null_resource)
terraform apply

# In terminal 2: immediately try another apply
terraform apply
# Should show: Error: state lock held by terminal 1
```

Document the error message and explain what `terraform force-unlock <lock-id>` does and
when it is (and isn't) safe in `scenarios/03-lock-demo.md`.

### 5. Plan safety rules to document

| Practice | Why |
|---|---|
| Always run `plan` before `apply` | See exactly what changes before they happen |
| Review `-/+ replace` carefully | Destroy + recreate means downtime |
| Never `apply -auto-approve` in production | No human review step |
| Require plan output approval in CI | Pipeline should run plan, human approves, then apply |
| Use `terraform plan -out=plan.tfplan` | Save the plan so apply runs exactly what was reviewed |

```bash
# The safe CI pattern:
terraform plan -out=plan.tfplan   # save plan to file
# (human or automated review of plan output)
terraform apply plan.tfplan        # apply exactly what was planned — nothing else
```

---

## Guided questions

1. `terraform plan` shows a `-/+ replace` for a database instance because you changed `allocated_storage`. The database has live production data. What are your options — and which is the least risky?
2. What is the difference between `terraform refresh` and `terraform plan`? Does `terraform refresh` change any infrastructure?
3. `terraform state rm` removes a resource from state without destroying it. When would you do this, and what happens the *next* time you run `terraform plan`?
4. A state lock is held but the engineer who started the apply went offline. Is it safe to run `terraform force-unlock`? What would you check first?
5. You run `terraform plan -out=plan.tfplan` and show the output to your manager for approval. They approve. 5 minutes later you run `terraform apply plan.tfplan`. Is the apply guaranteed to do exactly what the plan showed? What could have changed in those 5 minutes?

---

## Stretch goals

- Add `lifecycle { prevent_destroy = true }` to a critical resource and observe what happens when you try to destroy it
- Use `terraform taint` (or `terraform apply -replace`) to force a resource to be destroyed and recreated on the next apply
- Set up a GitHub Actions workflow that runs `terraform plan` on PRs and posts the output as a PR comment

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**Drift scenario I found most interesting:**

**What I struggled with:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — replace on production DB:**

**Q2 — refresh vs plan:**

**Q3 — state rm use case:**

**Q4 — force-unlock safety:**

**Q5 — plan → apply gap:**
