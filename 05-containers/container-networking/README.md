# Challenge 22 — Container Networking

## Scenario

> *"We have two containers — an API and a Redis cache. They need to talk to each other
> but neither should be reachable from the internet. A third container (Nginx) sits in front
> and handles all external traffic."*

This challenge is about understanding how Docker networks work: isolation, DNS by container name,
bridge vs host vs none, and controlling which containers can reach which.

---

## What you will build

Three containers on a custom bridge network:

```
           ┌─────────────────────────────────────────────┐
 Host      │ Docker bridge network: "app-net"            │
 :8080 ────│──► nginx ──► api:8080 ──► redis:6379        │
           │                                             │
           └─────────────────────────────────────────────┘
```

- `redis` — official Redis image, no ports exposed to the host
- `api` — Python Flask app that increments a Redis counter
- `nginx` — reverse proxy, only container with a host-facing port

---

## Deliverables

```
container-networking/
├── api/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
├── up.sh        # starts everything in the right order
├── down.sh      # stops and removes everything
└── README.md
```

---

## Functional requirements

### 1. Create the network

```bash
docker network create app-net
```

### 2. Start Redis (no host port — internal only)

```bash
docker run -d \
  --name redis \
  --network app-net \
  redis:7-alpine
```

Notice: no `-p` flag — Redis is unreachable from your host machine. Only containers on `app-net` can reach it.

### 3. The API

`api/app.py`:

```python
from flask import Flask, jsonify
import redis

app = Flask(__name__)
# Docker's built-in DNS resolves "redis" to the redis container's IP
r = redis.Redis(host="redis", port=6379, decode_responses=True)

@app.route("/")
def index():
    count = r.incr("visits")
    return jsonify({"visits": count, "from": "api"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

`requirements.txt`:
```
flask
redis
```

Build and run:
```bash
docker build -t api:1.0 ./api

docker run -d \
  --name api \
  --network app-net \
  api:1.0
```

Again: no `-p` — the API is also internal only.

Verify API can reach Redis:
```bash
docker exec api curl -s http://localhost:8080/
```

### 4. Nginx as the reverse proxy

`nginx/nginx.conf`:

```nginx
events {}

http {
    server {
        listen 80;

        location / {
            proxy_pass http://api:8080;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

```bash
docker run -d \
  --name nginx \
  --network app-net \
  -p 8080:80 \
  -v "$(pwd)/nginx/nginx.conf:/etc/nginx/nginx.conf:ro" \
  nginx:alpine
```

### 5. Test from the host

```bash
curl http://localhost:8080/        # hits nginx → api → redis
curl http://localhost:8080/        # visits count increases
curl http://localhost:8080/health  # health check via nginx
```

### 6. Prove isolation

Try to reach Redis directly from the host — it should fail:
```bash
redis-cli -h localhost -p 6379 ping   # should fail (port not exposed)
```

Try to reach the API directly — also fails:
```bash
curl http://localhost:8080/  # only works through nginx
# Direct api port not exposed either
```

### 7. Inspect the network

```bash
docker network inspect app-net
```

Note the containers, their IPs, and the network subnet.

---

## Key concepts

| Concept | How Docker implements it |
|---|---|
| Container DNS | Each container's name is a hostname within the network |
| Isolation | Containers not on the same network cannot talk to each other |
| Port mapping | `-p host:container` — only exposed ports are reachable from outside |
| Bridge network | Default for multi-container setups on a single host |

---

## Guided questions

1. You connected three containers with `--network app-net`. What would happen if you forgot `--network` on the Redis container? Could the API still reach it?
2. In `app.py`, the Redis host is the string `"redis"`. How does this get resolved to an IP address? What is the Docker feature that enables this?
3. What is the difference between a **bridge** network, a **host** network, and a **none** network?
4. If you `docker rm` the Redis container and recreate it, does the API need to be restarted? Why or why not?
5. The `nginx.conf` uses `proxy_pass http://api:8080`. The API is not exposed on port 8080 to the *host* — so how does Nginx reach it?

---

## Stretch goals

- Create a *second* bridge network `db-net`, put only Redis and the API on it, and only the API and Nginx on `app-net` — prove that Nginx cannot reach Redis directly
- Add a `curl` health-check `HEALTHCHECK` instruction to the API Dockerfile
- Replace the raw `docker run` commands with a shell script that waits for Redis to be ready before starting the API (hint: `docker exec redis redis-cli ping`)

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — forgot --network on Redis:**

**Q2 — how "redis" hostname resolves:**

**Q3 — bridge vs host vs none:**

**Q4 — Redis recreated, API restart?:**

**Q5 — Nginx reaches internal API:**
