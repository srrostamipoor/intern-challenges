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

**What I built:**
A small Flask API whose health I can control (`/health`, `/break`, `/fix`) and
a Compose stack with two services. The `api` image has a `HEALTHCHECK` in the
Dockerfile (`curl -f http://localhost:8080/health`, every 15s, 3s timeout, 10s
start period, 3 retries), and the same check is repeated in `compose.yaml`.
A `worker` service uses `depends_on: api: condition: service_healthy`, so it
only starts after the API is healthy.

**What I observed:**
- `docker compose up --build -d` printed `api Healthy` and then
  `worker Started`, both at about 6.2s. That is earlier than the 15s interval,
  which I believe is because Docker checks more often during the start period
  (the start interval).
- After `/break`, `FailingStreak` grew 1, 2, 3 and the status stayed `healthy`
  until the third failure; then it became `unhealthy` (about 30-45s after
  `/break`, matching 3 failures x 15s). The container stayed `Up` the whole
  time and the worker was not touched; Docker only changes the label.
- The health log showed `exit=22` and `curl: (22) The requested URL returned
  error: 503`.
- After `/fix`, the status returned to `healthy` (streak 0) in about 20s, one
  successful check was enough.
- Without `condition: service_healthy` (tested on a temporary copy of the
  file), `worker` started in 0.7s, before the API (1.1s), and `docker compose
  ps` showed the API still as `health: starting`. The worker's log said "API is
  healthy" even though that was not true yet.
- Inside the API container: `curl -s` on `/health` while broken printed the 503
  JSON body and returned `exit=0`; `curl -sf` printed nothing and returned
  `exit=22`.

**What I struggled with:**
- My `requirements.txt` was saved empty (0 bytes), which would have installed
  nothing in the image; I noticed it in the `dir` output before building.
- `watch` does not exist in PowerShell, so I used a loop with
  `Start-Sleep` and `docker inspect --format`.
- The container name in the challenge text (`compose-healthchecks-api-1`)
  does not match my folder name, so I used `docker inspect (docker compose ps
  -q api)` instead of guessing the name.
- `curl` is not in `python:3.11-slim`, so installing it with `apt-get` added
  22 packages (about 15 MB) just for the health check.

**What I'd do differently:**
- Use a small Python health check script instead of installing `curl`, to keep
  the image smaller.
- Split the endpoints into a cheap `/health` (liveness) and a `/ready` that
  checks dependencies (readiness).
- Add a real dependency (Postgres) with its own `pg_isready` healthcheck.

---

## Guided questions — answers

**Q1 — running vs healthy:**
`running` only means the main process of the container is alive. `healthy`
means the health check command succeeds, i.e. the application actually
answers. An app can hang or return errors while its process is still running;
I saw this when the container stayed `Up` but was `unhealthy` after `/break`.
Kubernetes and Compose `depends_on` care because routing traffic or starting a
dependent service when the app is only "running" causes errors like the 502s
in the scenario. In my test, without `service_healthy` the worker started
while the API was still `health: starting`.

**Q2 — K8s liveness vs readiness probe failures:**
When a liveness probe fails the configured number of times (three by
default), the kubelet kills the container and restarts it, which is meant for
applications that are stuck. When a readiness probe fails, the container is
not restarted; the pod is only removed from the Service's endpoints so it gets
no traffic, and it is added back when the probe succeeds again. (I did not run
Kubernetes here; in plain Docker, `unhealthy` is only a label and nothing
restarts the container, which I saw directly.)

**Q3 — start-period for slow apps:**
Slow-starting apps, for example ones that run database migrations, cannot
answer the check during their first seconds. During `--start-period`, failed
checks do not count towards `--retries`, so the container is not marked
`unhealthy` (or, in orchestrators, restarted) before it had a chance to start.
A successful check during that period marks it healthy immediately.

**Q4 — curl -f flag:**
`-f` (`--fail`) makes curl exit with a non-zero code (22) when the server
returns an HTTP error (400 or above). Without it, curl prints the error body
and exits with 0. I tested it while the API was broken: `curl -s` returned the
503 JSON body with `exit=0`, `curl -sf` returned nothing with `exit=22`. Since
Docker only looks at the exit code, a check without `-f` would report the
container as healthy while the app is returning errors.

**Q5 — health check hitting DB:**
Usually not a good idea for the main (liveness) check. If the database is slow
or down, every replica fails its check at the same time and gets restarted,
which does not fix the database and can make things worse; it also adds load
to the database on every check. A better pattern is to keep `/health` cheap
(only "the process responds") and add a separate `/ready` endpoint that checks
dependencies, used for readiness so a failure only stops traffic instead of
restarting the container. The result of a dependency check can also be cached
for a few seconds.