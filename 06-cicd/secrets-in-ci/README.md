# Challenge 29 — Secrets Management in CI

## Scenario

> *"A developer committed an API key to the repo. It was in the pipeline YAML.
> It was rotated within the hour — but it had already been scraped by bots.
> We need to make sure credentials never touch the codebase again, ever."*

Secrets in CI/CD are one of the most common sources of security incidents.
This challenge is about handling them correctly — using the platform's secrets store,
avoiding the most common leakage patterns, and auditing what's there.

---

## What you will build

A workflow that:
1. Uses GitHub Secrets correctly for all credentials
2. Masks sensitive values so they never appear in logs
3. Scopes secrets to specific environments (staging vs production)
4. Includes a `secrets_check.py` script that scans for hardcoded credentials before CI runs

---

## Deliverables

```
secrets-in-ci/
├── app/
│   └── config.py          # reads secrets safely from environment
├── .github/
│   └── workflows/
│       ├── ci.yaml
│       └── deploy.yaml    # uses environment-scoped secrets
├── secrets_check.py       # pre-flight scan for hardcoded creds
└── README.md
```

---

## Functional requirements

### 1. The wrong way (understand it to avoid it)

```yaml
# NEVER DO THIS — the key is visible in the YAML file,
# in git history, and in the Actions run log
- run: |
    export DB_PASSWORD=mysecretpassword123
    python deploy.py
```

```yaml
# ALSO WRONG — hardcoding in env:
env:
  API_KEY: "sk-abc123real-key-here"
```

### 2. The right way — GitHub Secrets

Set secrets in the GitHub UI: **Settings → Secrets and variables → Actions → New repository secret**

Then reference them in the workflow:

```yaml
env:
  DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
  API_KEY: ${{ secrets.API_KEY }}
  DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}
```

GitHub automatically **masks** any secret value in log output, replacing it with `***`.

### 3. ci.yaml — using secrets safely

```yaml
---
name: CI with Secrets

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Pre-flight secrets scan
        run: python secrets_check.py

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Run tests
        env:
          # Secrets are injected as environment variables — never echoed
          DB_HOST: ${{ secrets.TEST_DB_HOST }}
          DB_PASSWORD: ${{ secrets.TEST_DB_PASSWORD }}
        run: |
          pip install -r app/requirements.txt
          pytest app/

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
          # login-action handles the token — you never echo it yourself
```

### 4. Environment-scoped secrets (staging vs production)

Create two GitHub Environments: **Settings → Environments → New environment**

- `staging` — has its own set of secrets, no approval required
- `production` — has its own secrets, requires manual approval before deploy

```yaml
---
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging     # ← uses staging-scoped secrets
    steps:
      - name: Deploy to staging
        env:
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}   # staging DB password
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}     # staging server key
        run: echo "Deploying to staging with env-scoped secrets"

  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production  # ← uses production-scoped secrets + approval gate
    steps:
      - name: Deploy to production
        env:
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}   # different value than staging!
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
        run: echo "Deploying to production after approval"
```

### 5. app/config.py — reading secrets safely in code

```python
import os

def get_required(key: str) -> str:
    """Get an environment variable or raise a clear error — never return empty string."""
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Set it in your .env file (local) or GitHub Secrets (CI)."
        )
    return value

DB_HOST     = get_required("DB_HOST")
DB_PASSWORD = get_required("DB_PASSWORD")
API_KEY     = get_required("API_KEY")
```

### 6. secrets_check.py — scan before you push

```python
#!/usr/bin/env python3
"""
Pre-flight check — run before CI steps to catch hardcoded secrets.
Exit 1 if anything suspicious is found.
"""
import os, re, sys

PATTERNS = [
    (r'password\s*=\s*["\'][^${\s][^"\']{4,}["\']', "plain-text password"),
    (r'token\s*=\s*["\'][^${\s][^"\']{4,}["\']',    "plain-text token"),
    (r'secret\s*=\s*["\'][^${\s][^"\']{4,}["\']',   "plain-text secret"),
    (r'ghp_[A-Za-z0-9]{36}',                         "GitHub PAT"),
    (r'AKIA[0-9A-Z]{16}',                             "AWS Access Key ID"),
    (r'sk-[A-Za-z0-9]{32,}',                          "OpenAI API key"),
]

SKIP = {".git", ".venv", "__pycache__", "node_modules", "secrets_check.py"}

def scan(root="."):
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for fname in filenames:
            path = os.path.join(dirpath, fname)
            try:
                with open(path, errors="ignore") as f:
                    for n, line in enumerate(f, 1):
                        for pattern, label in PATTERNS:
                            if re.search(pattern, line, re.IGNORECASE):
                                found.append((path, n, label, line.rstrip()))
            except (OSError, IsADirectoryError):
                pass
    return found

if __name__ == "__main__":
    issues = scan()
    if not issues:
        print("✓ No hardcoded secrets detected.")
        sys.exit(0)
    print(f"✗ {len(issues)} potential secret(s) found:\n")
    for path, lineno, label, content in issues:
        print(f"  {path}:{lineno}  [{label}]")
        print(f"  → {content[:120]}\n")
    sys.exit(1)
```

### 7. Prove masking works

Add this step temporarily and observe the Actions log:

```yaml
- name: Prove masking
  env:
    MY_SECRET: ${{ secrets.DB_PASSWORD }}
  run: |
    echo "The secret is: $MY_SECRET"
    # GitHub will print: The secret is: ***
```

---

## Key rules — never break these

| Rule | Why |
|---|---|
| Never `echo $SECRET` in a script | Even masked, it's a bad habit |
| Never store secrets in env vars in `Dockerfile` | They end up in image layers |
| Never log the full secret for debugging | Use `echo ${#MY_SECRET} chars` to confirm it's set |
| Never use secrets in job names or step names | Names are not masked |
| Rotate immediately if a secret is ever exposed | Assume it's already been scraped |

---

## Guided questions

1. A secret is set in GitHub, but when the job runs, `${{ secrets.MY_SECRET }}` is empty. What are the three most likely causes?
2. Why can't `pull_request` workflows from **forks** access repository secrets? What alternative does GitHub provide?
3. What is the difference between a **repository secret** and an **environment secret**? When does the environment secret win?
4. You need to pass a secret to a Docker build (e.g., a private pip registry token). Why is `--build-arg` dangerous, and what is the right way?
5. A secret was committed to the repo 6 months ago, then deleted in a later commit. Is it still exposed? What must you do?

---

## Stretch goals

- Add `secrets_check.py` as a Git pre-commit hook so it runs locally before any push
- Use `git-secrets` or `truffleHog` in the CI pipeline to scan the entire git history for leaked secrets
- Set up a production environment with a required reviewer — observe the approval gate in the GitHub UI

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — secret is empty, why?:**

**Q2 — fork PR no secrets access:**

**Q3 — repo secret vs environment secret:**

**Q4 — Docker --build-arg danger:**

**Q5 — secret in git history:**
