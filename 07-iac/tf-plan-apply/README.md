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

**What I built:**
A small Terraform project (`main.tf`, `variables.tf`, `outputs.tf`) with an S3 bucket
(`myapp-dev-assets`) and a security group, running against Floci (a local AWS emulator).
With it I read three kinds of plans (create, in-place update, replacement), simulated drift in two
directions (a tag added by hand, a bucket deleted by hand), used `state list/show`, `refresh-only`,
`state rm` and `import`, simulated a state lock conflict with two terminals, and tested the safe
`plan -out` / `apply plan.tfplan` pattern, including a stale plan. Details are in
`scenarios/01-read-plan-output.md`, `02-drift-demo.md` and `03-lock-demo.md`.

**Drift scenario I found most interesting:**
Deleting the bucket by hand. `terraform plan` started with `Refreshing state...`, found nothing at that
id, dropped the bucket from its picture and planned `+ create`. The state said "exists", reality said
"gone", and the code is the source of truth, so the bucket was rebuilt from the code. It also showed that
Terraform rebuilds the *resource*, not the *data* inside it.

**What I struggled with:**
Telling the three things apart: code, state (what Terraform remembers) and reality (what really exists).
Also reading replacement plans: `-/+` is the label of the whole resource, while `~`, `+`, `-` are labels of
single attributes. Some practical problems too: the AWS CLI and the Docker Hub image were not reachable, so
I sent the S3 calls over plain HTTP with `curl.exe`; on Windows PowerShell `terraform plan -out=plan.tfplan`
failed with "Too many command line arguments" until I quoted the argument (`"-out=plan.tfplan"`); and a
Terraform prompt needs an English `yes` (a Persian keyboard layout cancelled the apply once).

**What I would do differently:**
Run the lock demo against a remote backend (S3 + DynamoDB on the emulator) to see the real `Lock Info` and
try `force-unlock` with a lock ID, which the local Windows file lock does not give.

---

## Guided questions — answers

**Q1 — replace on production DB:**
First, do not apply. Read the plan to see which attribute forces the replacement; often the same goal
can be reached with a change that is applied in place, and then the replacement disappears.
If a real replacement is unavoidable, the options are:
(1) take a snapshot/backup, replace, and restore the data (downtime, risk of losing writes made after the snapshot);
(2) build the new database next to the old one under a new resource name, migrate the data, switch the
application over, and only then remove the old one (least downtime, old data stays safe until the end);
(3) leave the plan unapplied and protect the resource with `lifecycle { prevent_destroy = true }` so a
destroy fails instead of happening.
The least risky is (2) combined with a backup first, because the old database is never destroyed until
the new one is proven. In every case the `destroy` count in the plan must be reviewed by a human.
(I saw the `-/+` replacement pattern on a bucket and a security group with `-var "environment=prod"`;
I did not test a database.)

**Q2 — refresh vs plan:**
`refresh` reads the real infrastructure and updates the *state* with what it finds. `plan` does that
refresh first (the `Refreshing state...` lines), then compares the result with the *configuration* and
lists the actions needed. Neither changes real infrastructure. I checked this: after adding a tag by hand,
`terraform plan -refresh-only` showed it but `terraform state show` still listed the old tags (plan does not
write the state file); after `terraform apply -refresh-only` the state showed the new tag, and a normal
`plan` still wanted to remove it, so the real bucket was never touched. `refresh` does rewrite the state
file, so it is not completely harmless: if resources look missing (wrong account or credentials), they can be
dropped from the state. The standalone `terraform refresh` is deprecated; `terraform apply -refresh-only`
does the same but shows the changes first and asks for approval.

**Q3 — state rm use case:**
Use it to stop managing a resource without destroying it: for example handing it over to another
Terraform project/team, splitting a state, or removing something that must keep running but should not
be managed here. The next `terraform plan` still finds the resource block in the code but nothing in
the state, so it plans to **create** it again, while the real resource still exists. I saw exactly this:
after `state rm aws_s3_bucket.assets`, the plan said `will be created` and only the security group was
refreshed. Applying that would fail with "already exists" or create a duplicate (I deliberately did not
apply). So after `state rm` the block must also be removed from the code (to stop managing it) or the
resource must be imported back; `terraform import aws_s3_bucket.assets myapp-dev-assets` worked and the
next plan showed no changes.

**Q4 — force-unlock safety:**
Not automatically. `force-unlock` removes the lock without checking that the owner is really gone; if the
apply is still running, two writers can corrupt the state. Check first: the lock info in the error message
(ID, who, when, which operation); whether the process or CI job is really dead (ask the engineer, look at
the CI logs, check the machine); and whether the apply may have stopped halfway, leaving real resources
changed but the state not updated. Only when you are sure nothing is running, unlock, then run
`terraform plan` to see the real state of things. With a versioned S3 backend an older state version can
be recovered if something goes wrong. (In my local test the lock was a Windows file lock without a lock ID,
so I could show the lock error but not run `force-unlock` itself.)

**Q5 — plan → apply gap:**
Mostly yes, but not in every case. `terraform apply plan.tfplan` applies exactly the saved actions and does
not plan again (and it does not ask for `yes`). I tested two things that can change in between:
- *The state changed* (someone else applied): I saved `old.tfplan`, ran a normal `apply`, then
  `terraform apply old.tfplan` failed with `Error: Saved plan is stale ... the state was changed by another
  operation after the plan was created.`
- *Reality changed by hand* (a tag added directly): the saved plan was accepted, because the state had not
  changed, and it applied exactly its own actions. It did not notice or touch the manual tag; the tag showed
  up as drift in the next `plan`.
So the apply does what the plan said, but it does not re-check reality: if someone changed or deleted a
resource by hand during those 5 minutes, the saved actions run against different infrastructure and may fail
or give a different result. Values marked `(known after apply)` are also only decided at apply time. For this
reason the plan file should be applied soon after approval and treated as sensitive, because it can contain
secret values.
