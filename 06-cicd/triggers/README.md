# Challenge 28 — Triggers: When Does the Pipeline Run?

## Scenario

> *"The pipeline runs on every single push — including a typo fix in the README.
> It also never runs for hotfix branches. And nobody set up the nightly smoke test.
> We need to control exactly what triggers what."*

Triggers are the front door of a CI/CD pipeline. Understanding them precisely means
your pipeline runs when it should, doesn't run when it shouldn't, and can always be
kicked off manually when you need it.

---

## What you will build

A single workflow file that demonstrates every major GitHub Actions trigger type,
with comments explaining why each one exists:

---

## Deliverables

```
triggers/
├── .github/
│   └── workflows/
│       ├── on-push.yaml          # push triggers with branch/path filters
│       ├── on-pr.yaml            # PR triggers with types
│       ├── on-schedule.yaml      # cron-based scheduled runs
│       └── on-manual.yaml        # workflow_dispatch with inputs
└── README.md
```

---

## Functional requirements

### 1. on-push.yaml — push triggers with filters

```yaml
---
name: On Push

on:
  push:
    branches:
      - main
      - "release/**"      # any branch starting with release/
    paths-ignore:
      - "**.md"           # don't trigger on documentation-only changes
      - ".gitignore"

jobs:
  info:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Triggered by push to: ${{ github.ref }}"
          echo "Commit: ${{ github.sha }}"
          echo "Author: ${{ github.actor }}"
```

Test this by:
- Pushing a `.md` file change — workflow should **not** trigger
- Pushing a `.py` file change — workflow **should** trigger
- Pushing to a `feature/` branch — workflow should **not** trigger

### 2. on-pr.yaml — pull request triggers with types

```yaml
---
name: On Pull Request

on:
  pull_request:
    branches: [main]
    types:
      - opened        # when the PR is first created
      - synchronize   # when new commits are pushed to the PR branch
      - reopened      # when a closed PR is reopened

jobs:
  pr-check:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "PR #${{ github.event.pull_request.number }}"
          echo "Title: ${{ github.event.pull_request.title }}"
          echo "From: ${{ github.head_ref }} → ${{ github.base_ref }}"
          echo "Trigger type: ${{ github.event.action }}"
```

**Important:** `pull_request` workflows run in the context of the *target* branch,
not the source branch — this is a security boundary. Document what this means for secrets access.

### 3. on-schedule.yaml — cron-based nightly runs

```yaml
---
name: Nightly Smoke Test

on:
  schedule:
    - cron: "0 2 * * *"    # 2am UTC every day
  # Also allow manual trigger (useful for testing the schedule itself)
  workflow_dispatch:

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          echo "Running nightly smoke test at $(date)"
          # In a real pipeline: run integration tests against staging
          curl -f https://httpbin.org/get | jq '.url'
```

Write a cron expression reference table in your write-up:

| Expression | Meaning |
|---|---|
| `0 2 * * *` | Daily at 2:00 AM UTC |
| `*/15 * * * *` | Every 15 minutes |
| `0 9 * * 1` | Every Monday at 9:00 AM UTC |
| `0 0 1 * *` | First day of every month at midnight |

### 4. on-manual.yaml — workflow_dispatch with inputs

```yaml
---
name: Manual Deploy

on:
  workflow_dispatch:
    inputs:
      environment:
        description: "Target environment"
        required: true
        type: choice
        options:
          - staging
          - production
        default: staging
      image_tag:
        description: "Docker image tag to deploy"
        required: true
        type: string
      dry_run:
        description: "Print what would happen without actually deploying"
        type: boolean
        default: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Environment: ${{ inputs.environment }}"
          echo "Image tag:   ${{ inputs.image_tag }}"
          echo "Dry run:     ${{ inputs.dry_run }}"

          if [ "${{ inputs.dry_run }}" = "true" ]; then
            echo "DRY RUN — would deploy ${{ inputs.image_tag }} to ${{ inputs.environment }}"
          else
            echo "Deploying ${{ inputs.image_tag }} to ${{ inputs.environment }}..."
          fi
```

Trigger this manually from the GitHub Actions UI under **Actions → Manual Deploy → Run workflow**.

### 5. Context variables to understand

| Variable | What it contains |
|---|---|
| `github.ref` | Full ref (e.g. `refs/heads/main`) |
| `github.ref_name` | Short name (e.g. `main`) |
| `github.sha` | The commit SHA that triggered the run |
| `github.actor` | Username who triggered the run |
| `github.event_name` | `push`, `pull_request`, `schedule`, `workflow_dispatch` |
| `github.event.action` | For PRs: `opened`, `synchronize`, `closed`, etc. |

Print all of these in a job step and observe the values for each trigger type.

---

## Guided questions

1. The `paths-ignore: ["**.md"]` filter means a push that only changes `README.md` won't trigger the pipeline. What is the *opposite* filter (`paths:`) and when would you use it?
2. Why does GitHub run `pull_request` workflows with the permissions of the *base* branch rather than the head branch? What attack does this prevent?
3. The schedule trigger uses UTC. Your team is in London (UTC+1 in summer). If the cron is `0 9 * * 1` (9am UTC), what time does the pipeline run locally in summer?
4. `workflow_dispatch` requires a manual trigger. What is `repository_dispatch` and when would you use it instead?
5. You set `paths-ignore: ["**.md"]`. A PR changes both `app.py` and `README.md`. Does the pipeline run?

---

## Stretch goals

- Add a `concurrency:` group so that only one workflow run at a time is allowed per branch, and new pushes cancel the previous run
- Use `on: push: tags:` to trigger a release pipeline when a `v*.*.*` tag is pushed
- Set up a `workflow_call` trigger so another workflow can call this one as a reusable component

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — paths: vs paths-ignore::**

**Q2 — PR security boundary:**

**Q3 — UTC timezone math:**

**Q4 — workflow_dispatch vs repository_dispatch:**

**Q5 — mixed paths change:**
