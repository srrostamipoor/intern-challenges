# Challenge 17 — YAML Debugger

## Scenario

> *"A new engineer pushed a GitHub Actions workflow. The pipeline won't even start — it just says
> 'invalid workflow file'. Find all the bugs."*

This challenge is a pure diagnosis exercise. You are given intentionally broken YAML files.
Your job is to find every bug, explain why it's wrong, and fix it.
No running code — just you, a text editor, and `yamllint`.

---

## Setup

```bash
pip install yamllint
```

---

## Deliverables

```
yaml-validator/
├── broken/
│   ├── pipeline.yaml        # 8 bugs — GitHub Actions workflow
│   ├── compose.yaml         # 5 bugs — Docker Compose file
│   └── k8s-job.yaml         # 4 bugs — Kubernetes Job manifest
├── fixed/
│   ├── pipeline.yaml        # your corrected versions
│   ├── compose.yaml
│   └── k8s-job.yaml
├── bug-report.md            # document every bug found
└── README.md                # this file + your write-up
```

---

## The broken files

Create these files yourself in `broken/`. Each one has intentional bugs embedded.

### `broken/pipeline.yaml` — 8 bugs

Copy this file exactly as written, bugs and all:

```yaml
name: CI Pipeline
on:
  push:
     branches: [main]    # BUG 1: extra space before branches (inconsistent indent)
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
        python-version: "3.11"       # BUG 2: python-version not indented under "with"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
           pip install pytest          # BUG 3: inconsistent indentation inside run block

      - name: Run tests
        run: pytest tests/ -v

      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Push to registry
        if: github.ref == 'refs/heads/main'
        env:
          DOCKER_USER: ${{ secrets.DOCKER_USER }}
          DOCKER_PASS: ${{ secrets.DOCKER_PASS }}   # BUG 4: tab character before DOCKER_PASS (invisible!)
        run: |
          echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
          docker push myapp:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy
        run: |
         echo "Deploying..."    # BUG 5: only 1 space indent inside run block (should be 2 or consistent)
         ./scripts/deploy.sh

      - name: Notify Slack
        uses: slackapi/slack-github-action@v1.24.0
        with:
          payload: |
            {
              "text": "Deploy to production complete",
              "channel: "#devops"    # BUG 6: missing closing quote after "channel
            }

      - name: Cleanup
        run: docker system prune -f
        if github.always()           # BUG 7: missing colon after "if"

# BUG 8: This file uses both spaces and a tab (find the tab on line with DOCKER_PASS)
# Run: cat -A broken/pipeline.yaml | grep '\^I' to find tabs
```

### `broken/compose.yaml` — 5 bugs

```yaml
version: "3.9"

services:
  web:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./html:/usr/share/nginx/html
    networks:
      - frontend
    depends_on:
      - api

  api:
    build: ./api
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/mydb
      - DEBUG=false
    ports:
      - "8080:8080"
    networks:
      - frontend
      - backend
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "user"]
        interval: 10s      # BUG 1: interval indented one level too deep (under test)
      timeout: 5s
      retries: 5
    networks:
      - backend

networks:
  frontend:
  backend

volumes:           # BUG 2: missing colon after "backend" network definition above
  db_data:

# BUG 3: "api" service has no healthcheck but "db" depends on service_healthy — this will work
#         at the compose level but is a logical mistake. Document WHY this is a problem.

# BUG 4: The "web" service depends on "api" but api has no healthcheck condition.
#         This means "web" starts as soon as "api" container starts, not when it's ready.
#         Add a healthcheck and condition: service_healthy to fix this properly.

# BUG 5: environment in "api" uses list format (- KEY=VAL) but "db" uses map format (KEY: VAL).
#         Both are valid YAML, but mixing styles in the same file is inconsistent.
#         Standardize to one format and document your choice.
```

### `broken/k8s-job.yaml` — 4 bugs

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  namespace: production
spec:
  ttlSecondsAfterFinished: 100
  template:
    spec:
      restartPolicy: Never    # correct for a Job
      containers:
        - name: migrator
          image: myapp:1.0.0
          command: ["python", "manage.py", "migrate"]
          env:
            - name: DATABASE_URL
              value: "postgres://user:pass@db:5432/mydb"
          resources:
            requests:
              memory: 128Mi   # BUG 1: missing quotes — memory values should be "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: 500m       # BUG 2: cpu limit missing quotes — inconsistent with requests
      imagePullSecrets:
        name: registry-secret  # BUG 3: should be "- name:" (list item), not "name:"
  backoffLimit: 3
  activeDeadlineSeconds: 300

# BUG 4: A Job's pod template must have spec.restartPolicy set to Never or OnFailure.
#         This file has it correct but it's nested under spec.template.spec — verify
#         that it is NOT accidentally placed under spec directly (a common mistake).
#         Write a note explaining where restartPolicy belongs and why.
```

---

## The bug report format

For each bug, fill in `bug-report.md`:

```markdown
## Bug N — [short title]

**File:** broken/pipeline.yaml
**Line:** 14
**Type:** [Indentation | Syntax | Logic | Style]
**Symptom:** What error or behavior would this cause?
**Root cause:** Why is this wrong?
**Fix:** Exact change made in fixed/pipeline.yaml
```

---

## Tools to use

```bash
# yamllint with strict mode
yamllint -d "{extends: default, rules: {line-length: disable}}" broken/pipeline.yaml

# Find invisible tabs
cat -A broken/pipeline.yaml | grep -n $'\t'

# Python can also validate
python3 -c "import yaml; yaml.safe_load(open('broken/compose.yaml'))"
```

---

## Guided questions

1. Why does YAML forbid mixing tabs and spaces? What does the spec say about tabs?
2. `yamllint` found 3 errors. But there are 8 bugs. Why might a linter miss some bugs?
3. What is the difference between a YAML **syntax** error and a YAML **semantic** error? Give an example from this challenge.
4. GitHub Actions, Kubernetes, and Docker Compose all use YAML — but they all have different schema rules. What tool would you use to validate each one against its specific schema?

---

## Write-up

**How many bugs did I find before using yamllint?**

**Which bug was hardest to spot and why?**

**What would I add to a pre-commit hook to catch these automatically?**
