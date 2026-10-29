# Challenge 25 — Container Health Checks

## Scenario

> *"Kubernetes says the pod is Running but users get 502 errors. The container started,
> but the app inside it crashed 30 seconds later — and nothing noticed.
> We need proper health checks so the platform knows when to restart a container
> and when to stop sending it traffic."*

Health checks are what separate a container that is *running* from one that is *healthy*.
This challenge covers Docker's `HEALTHCHECK` instruction, Compose health checks,
and integrating them into a `depends_on` wait condition.

---

## What you will build

A Flask app with three states — healthy, degraded, and down — and a full health check setup:

1. A `HEALTHCHECK` in the Dockerfile
2. A `healthcheck:` block in `compose.yaml`
3. An API that can simulate failure so you can watch the health check respond
4. A `depends_on` condition that waits for `service_healthy` before starting a dependent service

---

## Deliverables

```
container-healthchecks/
├── api/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── compose.yaml
└── README.md
```

---

## Functional requirements

### 1. The app with a controllable health state

`api/app.py`:

```python
from flask import Flask, jsonify
import time, threading

app = Flask(__name__)
_healthy = True
_start_time = time.monotonic()

@app.route("/health")
def health():
    if not _healthy:
        return jsonify({"status": "down", "reason": "simulated failure"}), 503
    uptime = time.monotonic() - _start_time
    return jsonify({"status": "ok", "uptime_seconds": round(uptime, 1)}), 200

@app.route("/break")
def break_health():
    global _healthy
    _healthy = False
    return jsonify({"status": "health check will now fail"})

@app.route("/fix")
def fix_health():
    global _healthy
    _healthy = True
    return jsonify({"status": "health check restored"})

@app.route("/")
def index():
    return jsonify({"message": "api is running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### 2. HEALTHCHECK in the Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8080

HEALTHCHECK \
  --interval=15s \
  --timeout=3s \
  --start-period=10s \
  --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "app.py"]
```

Install `curl` in the image (add before HEALTHCHECK):
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
```

### 3. compose.yaml with healthcheck and depends_on

```yaml
services:
  api:
    build: ./api
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 15s
      timeout: 3s
      start_period: 10s
      retries: 3

  worker:
    image: alpine
    # This service only starts after api is confirmed healthy
    depends_on:
      api:
        condition: service_healthy
    command: >
      sh -c "echo 'API is healthy — worker starting' && sleep infinity"
```

### 4. Observe the health check lifecycle

```bash
docker compose up --build -d

# Watch status in real time
watch -n2 docker compose ps

# Or one-shot
docker inspect compose-healthchecks-api-1 \
  --format '{{.State.Health.Status}}: {{(index .State.Health.Log 0).Output}}'
```

States you should observe:
- `starting` — within `start_period` (10s), health check failures don't count yet
- `healthy` — all checks passing
- `unhealthy` — after 3 consecutive failures

### 5. Trigger and recover from unhealthy state

```bash
# Simulate failure
curl http://localhost:8080/break

# Watch it go unhealthy (takes ~45s: 3 failures × 15s interval)
watch -n5 docker compose ps

# Recover
curl http://localhost:8080/fix

# Watch it return to healthy
watch -n5 docker compose ps
```

### 6. What the worker does

```bash
docker compose logs worker
```

You should see the worker only started *after* the API reported healthy.
Try bringing the stack up without the `condition: service_healthy` — the worker starts immediately,
before the API is ready. That's the problem `depends_on` with health conditions solves.

---

## HEALTHCHECK parameters explained

| Parameter | Default | What it controls |
|---|---|---|
| `--interval` | 30s | How often to run the check |
| `--timeout` | 30s | How long the check has to respond before it's considered failed |
| `--start-period` | 0s | Grace period after container start — failures here don't count |
| `--retries` | 3 | How many consecutive failures = unhealthy |

---

## Guided questions

1. What is the difference between a container with status `running` and one with health status `healthy`? Why does Kubernetes (or Compose `depends_on`) care about the distinction?
2. What happens in Kubernetes when a liveness probe fails three times? What about when a readiness probe fails?
3. Why is there a `--start-period` option? What problem does it solve for slow-starting apps (like ones that run database migrations on startup)?
4. The health check uses `curl -f http://localhost:8080/health`. What does the `-f` flag do, and why is it necessary?
5. Your health endpoint hits the database on every check. Is that a good idea? What is a better pattern?

---

## Stretch goals

- Add a Postgres service and make the `/health` endpoint return unhealthy if the DB connection fails
- Write a Python health check script (`healthcheck.py`) instead of using `curl` — use it as the `HEALTHCHECK CMD`
- Set `restart: on-failure` and watch Docker automatically restart an unhealthy container

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — running vs healthy:**

**Q2 — K8s liveness vs readiness probe failures:**

**Q3 — start-period for slow apps:**

**Q4 — curl -f flag:**

**Q5 — health check hitting DB:**
