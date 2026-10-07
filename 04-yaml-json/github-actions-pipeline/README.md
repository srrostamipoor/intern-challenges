# Challenge 18 — Real GitHub Actions Pipeline

## Scenario

> *"The team wants a proper CI pipeline for the todo-api we described in Challenge 16.
> Write the full GitHub Actions workflow: lint → test → build Docker image → push to Docker Hub
> → trigger a deploy. This must work on a real repo."*

This is the capstone of Phase 2. You'll write YAML that actually runs — combining your Python
knowledge (the app being tested) with your YAML skills (the pipeline itself).

---

## What you will build

A `.github/workflows/ci.yaml` file that:

1. **Triggers** on push to `main` and on every pull request
2. **Lints** Python code with `flake8`
3. **Tests** with `pytest`
4. **Builds** a Docker image tagged with the Git SHA
5. **Pushes** to Docker Hub (only on `main` branch)
6. **Announces** the result to a Discord/Slack webhook

---

## Prerequisites

- A GitHub account and a public repo (create a new one: `todo-api-demo`)
- A Docker Hub account (free)
- The uptime monitor or log parser script from Challenge 11/12 as the "app" to test

---

## Deliverables

```
github-actions-pipeline/
├── .github/
│   └── workflows/
│       └── ci.yaml         # the main pipeline
├── app/
│   ├── monitor.py          # copy your script from Challenge 11 or 12
│   ├── requirements.txt
│   └── tests/
│       └── test_monitor.py # at least 3 unit tests
├── Dockerfile
├── screenshots/
│   ├── green_run.png       # screenshot of a successful pipeline run
│   └── failed_run.png      # screenshot of a deliberately broken run
└── README.md               # this file + your write-up
```

---

## The pipeline — step by step

### Step 1 — Triggers

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

### Step 2 — Lint job

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"              # cache pip dependencies between runs

      - run: pip install flake8
      - run: flake8 app/ --max-line-length=120
```

### Step 3 — Test job

```yaml
  test:
    runs-on: ubuntu-latest
    needs: lint                   # only run if lint passed
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
      - run: pip install -r app/requirements.txt
      - run: pytest app/tests/ -v --tb=short
```

### Step 4 — Build & Push Docker image

```yaml
  docker:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'   # push to Docker Hub only from main
    steps:
      - uses: actions/checkout@v4

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/todo-api:latest
            ${{ secrets.DOCKERHUB_USERNAME }}/todo-api:${{ github.sha }}
```

### Step 5 — Notify

```yaml
  notify:
    runs-on: ubuntu-latest
    needs: [lint, test, docker]
    if: always()                  # run even if previous jobs failed
    steps:
      - name: Send Discord notification
        env:
          WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK }}
        run: |
          STATUS="${{ needs.docker.result }}"
          COLOR=5763719   # green
          [ "$STATUS" != "success" ] && COLOR=15548997  # red

          curl -s -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{
              \"embeds\": [{
                \"title\": \"Pipeline: $STATUS\",
                \"description\": \"Repo: ${{ github.repository }}\nBranch: ${{ github.ref_name }}\nCommit: \`${{ github.sha }}\`\",
                \"color\": $COLOR
              }]
            }"
```

---

## The Dockerfile

Write a minimal, multi-stage Dockerfile for the app:

```dockerfile
# Stage 1: dependencies
FROM python:3.11-slim AS deps
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: final image
FROM python:3.11-slim
WORKDIR /app
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY app/ .

# Run as non-root
RUN useradd -m appuser
USER appuser

CMD ["python", "monitor.py", "--help"]
```

---

## Secrets you need to configure

In your GitHub repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret name | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token (not your password!) |
| `DISCORD_WEBHOOK` | Discord webhook URL |

**Never hardcode these in the YAML file.**

---

## Write at least 3 unit tests

In `app/tests/test_monitor.py`:

```python
import pytest
from unittest.mock import patch, MagicMock

# Import from your monitor.py
from monitor import check_url

def test_check_url_returns_true_on_200():
    with patch("monitor.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        is_up, reason = check_url("http://example.com")
    assert is_up is True

def test_check_url_returns_false_on_500():
    with patch("monitor.requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        is_up, reason = check_url("http://example.com")
    assert is_up is False

def test_check_url_handles_connection_error():
    import requests as req
    with patch("monitor.requests.get", side_effect=req.exceptions.ConnectionError):
        is_up, reason = check_url("http://doesnotexist.internal")
    assert is_up is False
    assert "connection" in reason.lower()
```

---

## Things to observe and document

1. Run the pipeline and **screenshot** the successful run showing all 4 jobs green
2. Introduce a bug (e.g. a syntax error in `monitor.py`) and **screenshot** the lint job failing
3. Check the Docker Hub page and verify the image was pushed with two tags
4. Open a pull request from a branch — verify the pipeline runs but the Docker push is **skipped**

---

## Guided questions

1. What is `needs:` in GitHub Actions? What happens if you remove it from the `test` job?
2. Why use `${{ github.sha }}` as an image tag instead of `latest`?
3. What is the difference between `if: github.ref == 'refs/heads/main'` and `if: github.event_name == 'push'`?
4. Why is `if: always()` important for the notify job? What happens without it?
5. What is a multi-stage Docker build and why does it produce a smaller final image?
6. What is `cache: "pip"` in `actions/setup-python` doing under the hood?

---

## Write-up

**What I built:**

**What was harder than I expected:**

**Pipeline run times (before and after pip caching):**

**What I'd add to make this production-grade:**
