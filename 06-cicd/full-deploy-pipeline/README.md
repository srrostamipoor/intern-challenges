# Challenge 32 — Full Deploy Pipeline: PR Tests + Auto-Deploy on Merge

## Scenario

> *"Every time someone merges to main, I want the code automatically tested, built,
> and deployed to Render (or Railway). If tests fail, the PR can't merge.
> If the deploy fails, I want to know immediately."*

This is the capstone of the CI/CD section. Everything from challenges 27–31 comes together
in one real, working pipeline for a project deployed to a free hosting service.

---

## What you will build

A production-grade pipeline for a Flask app deployed to **Render** (free tier):

```
Pull Request opened/updated
   │
   ├─► [lint]    — flake8
   └─► [test]    — pytest with coverage
          │
          └─► PR status check blocks merge if either fails

Merge to main
   │
   ├─► [lint] → [test] → [build] → [deploy to Render]
   │                                      │
   └─────────────────────────────────────►└─► [notify] (always runs)
```

---

## Deliverables

```
full-deploy-pipeline/
├── app/
│   ├── main.py
│   ├── test_main.py
│   └── requirements.txt
├── Dockerfile
├── render.yaml          # Render infrastructure-as-config
├── .github/
│   └── workflows/
│       └── pipeline.yaml
└── README.md
```

---

## Functional requirements

### 1. Set up Render

1. Create a free account at [render.com](https://render.com)
2. Connect your GitHub repository
3. Create a **Web Service** pointing to your repo
4. Note your **Deploy Hook URL** (under Settings → Deploy Hooks) — this is what the pipeline calls

### 2. render.yaml — Render infrastructure-as-config

```yaml
services:
  - type: web
    name: pipeline-app
    runtime: docker
    dockerfilePath: ./Dockerfile
    envVars:
      - key: APP_ENV
        value: production
    healthCheckPath: /health
    autoDeploy: false    # we control deploys from the pipeline, not Render's auto-deploy
```

### 3. pipeline.yaml — the full workflow

```yaml
---
name: Full Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
          cache-dependency-path: app/requirements.txt
      - run: pip install flake8
      - run: flake8 app/ --max-line-length=120

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
          cache-dependency-path: app/requirements.txt
      - run: pip install -r app/requirements.txt pytest pytest-cov
      - run: pytest app/ -v --cov=app --cov-report=xml
      - uses: actions/upload-artifact@v4
        if: always()    # upload even if tests fail, so you can inspect the report
        with:
          name: coverage-${{ github.sha }}
          path: coverage.xml
          retention-days: 14

  build:
    runs-on: ubuntu-latest
    needs: [lint, test]
    if: github.ref == 'refs/heads/main'    # build only on merge, not PRs
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/pipeline-app:${{ github.sha }}
            ${{ secrets.DOCKERHUB_USERNAME }}/pipeline-app:latest
          cache-from: type=registry,ref=${{ secrets.DOCKERHUB_USERNAME }}/pipeline-app:buildcache
          cache-to:   type=registry,ref=${{ secrets.DOCKERHUB_USERNAME }}/pipeline-app:buildcache,mode=max

  deploy:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Trigger Render deploy
        run: |
          RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}")
          echo "Render response: $RESPONSE"
          if [ "$RESPONSE" != "200" ]; then
            echo "Deploy hook failed with status $RESPONSE"
            exit 1
          fi

      - name: Wait for deploy to complete
        run: |
          echo "Waiting for Render to deploy..."
          sleep 60    # Render typically deploys in 1-2 minutes
          curl -f https://your-app.onrender.com/health || exit 1
          echo "Deploy confirmed healthy."

  notify:
    runs-on: ubuntu-latest
    needs: [lint, test, build, deploy]
    if: always()    # always run, even if previous jobs failed
    steps:
      - name: Send notification
        env:
          WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK }}
          LINT_STATUS:   ${{ needs.lint.result }}
          TEST_STATUS:   ${{ needs.test.result }}
          BUILD_STATUS:  ${{ needs.build.result }}
          DEPLOY_STATUS: ${{ needs.deploy.result }}
        run: |
          if [ -z "$WEBHOOK_URL" ]; then
            echo "No DISCORD_WEBHOOK set — skipping notification"
            exit 0
          fi

          OVERALL="success"
          for STATUS in $LINT_STATUS $TEST_STATUS $BUILD_STATUS $DEPLOY_STATUS; do
            [ "$STATUS" = "failure" ] && OVERALL="failure"
          done

          COLOR=5763719    # green
          [ "$OVERALL" = "failure" ] && COLOR=15548997    # red

          curl -s -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{
              \"embeds\": [{
                \"title\": \"Pipeline: $OVERALL\",
                \"description\": \"Commit: \`${{ github.sha }}\`\nBranch: ${{ github.ref_name }}\n\nlint: $LINT_STATUS | test: $TEST_STATUS | build: $BUILD_STATUS | deploy: $DEPLOY_STATUS\",
                \"color\": $COLOR
              }]
            }"
```

### 4. Required GitHub Secrets

Set these in **Settings → Secrets and variables → Actions**:

| Secret | Where to get it |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub → Account Settings → Security → Access Token |
| `RENDER_DEPLOY_HOOK_URL` | Render dashboard → Service → Settings → Deploy Hooks |
| `DISCORD_WEBHOOK` | Discord server → Channel Settings → Integrations → Webhooks |

### 5. Set up the branch protection rule

Go to **Settings → Branches → Add rule** for `main`:
- ✅ Require status checks to pass before merging
  - Add `lint` and `test` as required checks
- ✅ Require branches to be up to date before merging
- ✅ Do not allow bypassing the above settings

Now open a PR with a failing test — the merge button will be blocked.

### 6. End-to-end test

```bash
# Create a feature branch
git checkout -b feature/add-endpoint

# Add a new endpoint and a test for it
# Push and open a PR
git push -u origin feature/add-endpoint
# GitHub opens the PR, runs lint + test, shows green checks

# Merge the PR
# Pipeline runs: lint → test → build → deploy
# Check: curl https://your-app.onrender.com/
# Discord notification arrives
```

---

## Guided questions

1. Lint and test run in parallel (no `needs:` between them) but both are required for `build`. Draw the dependency graph. What is the total pipeline time if lint takes 30s, test takes 2min, and build takes 3min?
2. The `deploy` job calls a Render webhook URL. What is a deploy hook, and why is it better than SSH-ing into the server and running `docker pull` manually?
3. `if: always()` on the notify job ensures it runs even when deploy fails. But `needs: [lint, test, build, deploy]` means if deploy is *skipped* (e.g., on a PR), notify still runs. Is `needs.deploy.result` `"skipped"` or `"failure"` in that case?
4. Branch protection requires the `lint` and `test` checks to pass. These checks run on the PR branch. After merging, the pipeline runs again on `main`. Is this duplicate work? Why might it be necessary?
5. The `build` job only runs on `main` (`if: github.ref == 'refs/heads/main'`). What is the result of the `build` job when triggered by a PR — `"skipped"` or `"success"`? How does this affect `notify`?

---

## Stretch goals

- Add a `rollback` workflow that accepts a commit SHA input and re-triggers the Render deploy hook with that SHA's image
- Add `pytest-cov` minimum coverage enforcement: fail the test job if coverage drops below 80%
- Deploy to two environments: `render-staging` on every merge to `main`, `render-production` on a git tag push

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**Deploy URL:**

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — dependency graph and total time:**

**Q2 — deploy hook vs SSH:**

**Q3 — notify result when deploy is skipped:**

**Q4 — duplicate CI on merge:**

**Q5 — build result on PR:**
