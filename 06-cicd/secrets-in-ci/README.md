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

**What I built:**
A CI setup that keeps credentials out of the codebase, in a separate repo
because workflows only run from the repository root:
https://github.com/srrostamipoor/secrets-ci-demo. The files here are a copy.

- `ci.yaml`: scans the code with `secrets_check.py` first, runs tests, logs in
  to Docker Hub with repository secrets, and has a temporary "Prove masking"
  step.
- `deploy.yaml`: `deploy-staging` and `deploy-production` use environment
  secrets. Production has a required reviewer, so the job waited until I
  approved it.
- `app/config.py` reads secrets only from environment variables and raises a
  clear error when one is missing. `app/test_config.py` tests both cases with
  `monkeypatch`.
- `secrets_check.py` exits 1 if it finds a hardcoded password, token or key.

What I observed:
- The masking step printed `The secret is: ***` and `Length: 18 chars`.
- A repo secret `DB_PASSWORD` and environment secrets with the same name
  coexisted. Staging printed length 16 and production 20 (the repo secret
  was 18), so each job used its own environment's value.
  `DEPLOY_KEY` showed 12 (staging) and 13 (production).
- The production job waited about two minutes for my approval before running.
- `secrets_check.py` returned 0 on the clean project and 1 with a test file
  containing `password = "hunter2hunter2"`, which I then removed.

**What I struggled with:**
- My first run failed at the Docker Hub login with "Username and password
  required" because I had not created the repository secrets yet.
- The README's `pytest app/` fails with exit code 5 when there are no tests, so
  I added `test_config.py`.
- Trailing whitespace and a missing final newline made flake8 complain
  (W293, W292).

**What I'd do differently:**
- Never print secrets, even masked: masking can be bypassed by changing the
  value (for example base64). I would use only the length check.
- Add `secrets_check.py` as a pre-commit hook so it runs before every commit.
- Scan the full git history (git-secrets or trufflehog) in CI, not only the
  working tree.

---

## Guided questions — answers

**Q1 — secret is empty, why?:**
(1) The name is wrong or the secret was never created in this repository (I saw
this: "Username and password required"). (2) The run comes from a fork or
Dependabot pull request, which gets no secrets. (3) It is an environment secret
but the job has no `environment:` key.

**Q2 — fork PR no secrets access:**
Anyone can fork and change the workflow to send `${{ secrets.X }}` to their own
server, so GitHub withholds secrets and makes the token read-only for fork PRs.
`pull_request_target` runs in the base context with secrets, but it is risky and
must not run untrusted PR code. A safer gate is an environment with a required
reviewer.

**Q3 — repo secret vs environment secret:**
A repo secret is available to every job. An environment secret is only available
to jobs that declare that `environment:`, and the environment can add rules such
as required reviewers. If both have the same name, the environment secret wins:
staging and production printed lengths 16 and 20 instead of the repo value's 18.

**Q4 — Docker --build-arg danger:**
The value is stored in the image metadata. `docker history --no-trunc` showed
`ARG MY_TOKEN=fake-token-123` and the `RUN` line with the value, and Docker warned
`SecretsUsedInArgOrEnv`. The right way is a BuildKit secret mount:
`RUN --mount=type=secret,id=token ...` with `docker build --secret`, so the value
is only available during that RUN and is not stored in a layer.

**Q5 — secret in git history:**
Yes, it is still exposed. `git log -p -S` found the value in the commit that added
it even though a later commit deleted the file. I must revoke and rotate the secret
first. Rewriting history (git filter-repo or BFG, then force push) is optional,
because existing clones and forks keep the old data.