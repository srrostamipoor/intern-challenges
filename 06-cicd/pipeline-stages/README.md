# Challenge 27 — Pipeline Stages: lint → test → build → deploy

## Scenario

> *"Our developer pushed broken code straight to main. Tests existed but nobody ran them.
> We need a pipeline that enforces the right order: lint first, then test, then build,
> then deploy — and stops the moment any stage fails."*

This challenge is about understanding *why* CI/CD stages exist in that specific order,
not just how to configure them. You'll build a GitHub Actions workflow that enforces
a real quality gate before anything gets deployed.

---

## What you will build

A GitHub Actions pipeline for a small Python app with four jobs, each gating the next:

```
push/PR
   │
   ▼
[lint]   ← flake8 — catches style and syntax errors fast (30s)
   │
   ▼
[test]   ← pytest — proves the code is correct (2–5 min)
   │
   ▼
[build]  ← docker build + push to registry (1–3 min)
   │
   ▼
[deploy] ← only on main branch — rolls out the new image
```

---

## Deliverables

```
pipeline-stages/
├── app/
│   ├── main.py
│   ├── test_main.py
│   └── requirements.txt
├── Dockerfile
├── .github/
│   └── workflows/
│       └── pipeline.yaml
└── README.md
```

---

## Functional requirements

### 1. The app

`app/main.py`:

```python
from flask import Flask, jsonify

app = Flask(__name__)

def add(a, b):
    return a + b

def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]

@app.route("/")
def index():
    return jsonify({"status": "ok"})

@app.route("/add/<int:a>/<int:b>")
def add_route(a, b):
    return jsonify({"result": add(a, b)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

`app/test_main.py`:

```python
from main import add, is_palindrome

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_palindrome():
    assert is_palindrome("racecar") is True
    assert is_palindrome("Race Car") is True
    assert is_palindrome("hello") is False
```

`app/requirements.txt`:
```
flask
pytest
flake8
```

### 2. pipeline.yaml — the four-stage workflow

```yaml
---
name: Pipeline

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
      - run: pip install flake8
      - run: flake8 app/ --max-line-length=120

  test:
    runs-on: ubuntu-latest
    needs: lint        # ← only runs if lint passes
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r app/requirements.txt
      - run: pytest app/ -v

  build:
    runs-on: ubuntu-latest
    needs: test        # ← only runs if tests pass
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/pipeline-app:${{ github.sha }}

  deploy:
    runs-on: ubuntu-latest
    needs: build       # ← only runs if build passes
    if: github.ref == 'refs/heads/main'   # ← only on main, not PRs
    steps:
      - name: Deploy
        run: echo "Deploying ${{ github.sha }} to production"
        # In a real pipeline: SSH to server, pull image, restart container
```

### 3. Trigger a failure at each stage

Do each of these in a branch, open a PR, and observe which stage fails and which ones are skipped:

```bash
# Make lint fail — add a line that's too long
echo "x = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'" >> app/main.py

# Make tests fail — break a function
# In main.py, change: return a + b   to: return a - b

# Make build fail — add a syntax error to the Dockerfile
echo "INVALID_INSTRUCTION" >> Dockerfile
```

Observe: when lint fails, test, build, and deploy are all skipped. That's the value of `needs:`.

### 4. Why this order?

| Stage | Why here? | If it fails, you save... |
|---|---|---|
| `lint` | Catches trivial errors in seconds | Waiting 5 min for tests to run |
| `test` | Proves correctness before building an artifact | Storing/pushing a broken image |
| `build` | Creates the deployable artifact | Rolling out an image that can't be built |
| `deploy` | Last — only runs on known-good artifacts | Deploying broken code to production |

---

## Guided questions

1. `needs: lint` means the test job waits for lint. Can you make lint and test run **in parallel** and only have build wait for both? What would that look like?
2. What is the difference between a job failing and a job being **skipped**? How does GitHub Actions display each?
3. The deploy job has `if: github.ref == 'refs/heads/main'`. What happens to the deploy job when you open a Pull Request from a feature branch?
4. Why do we build the Docker image *after* tests pass, not before? What would go wrong if we pushed to the registry first?
5. A senior engineer says "just run all four stages in one job with `&&`". What do you lose compared to separate jobs with `needs:`?

---

## Stretch goals

- Add a fifth job `notify` that always runs (`if: always()`) and posts a Discord/Slack message with the pipeline result
- Split the pipeline into two files: `ci.yaml` (lint + test, runs on PRs) and `cd.yaml` (build + deploy, runs on merge to main)
- Add a manual `workflow_dispatch` trigger with an input for the target environment

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — parallel jobs:**

**Q2 — failed vs skipped:**

**Q3 — deploy on PR:**

**Q4 — build after tests:**

**Q5 — one job with &&:**
