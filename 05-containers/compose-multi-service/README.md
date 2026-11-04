# Challenge 23 — Docker Compose: Multi-Service App

## Scenario

> *"Running five `docker run` commands by hand every time is error-prone and hard to hand off.
> Put it all in a Compose file so the entire stack comes up with one command."*

Docker Compose is the standard tool for defining and running multi-container applications
on a single host. This is the challenge where everything from challenges 19–22 comes together.

---

## What you will build

A full three-tier web application defined in a single `compose.yaml`:

```
               ┌─────────────────────────────────────────────┐
 Host :8080 ──►│ nginx (proxy) ──► api ──► postgres (db)     │
               │                    └──► redis (cache)       │
               └─────────────────────────────────────────────┘
```

| Service | Image | Role |
|---|---|---|
| `nginx` | `nginx:alpine` | Reverse proxy — only public-facing service |
| `api` | Built from `./api` | Python Flask app |
| `postgres` | `postgres:16-alpine` | Primary datastore |
| `redis` | `redis:7-alpine` | In-memory cache / session store |

---

## Deliverables

```
compose-multi-service/
├── api/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
├── compose.yaml
├── .env.example
└── README.md
```

---

## Functional requirements

### 1. The API

`api/app.py` — stores a message in Postgres and caches it in Redis:

```python
from flask import Flask, request, jsonify
import os, psycopg2, redis

app = Flask(__name__)

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        dbname=os.getenv("DB_NAME", "appdb"),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD", "secret"),
    )

r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), decode_responses=True)

@app.before_request
def init_db():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, text TEXT)")
    conn.commit()
    conn.close()

@app.route("/messages", methods=["GET"])
def get_messages():
    cached = r.get("messages")
    if cached:
        return jsonify({"source": "cache", "messages": cached.split("|")})
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT text FROM messages ORDER BY id")
        rows = [row[0] for row in cur.fetchall()]
    conn.close()
    r.setex("messages", 30, "|".join(rows))
    return jsonify({"source": "db", "messages": rows})

@app.route("/messages", methods=["POST"])
def add_message():
    text = request.json.get("text", "")
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO messages (text) VALUES (%s)", (text,))
    conn.commit()
    conn.close()
    r.delete("messages")   # invalidate cache
    return jsonify({"added": text}), 201

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

`requirements.txt`:
```
flask
psycopg2-binary
redis
```

### 2. compose.yaml — what you must write

You must write this file yourself. The skeleton below shows the structure — fill in all values:

```yaml
services:

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - backend
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    networks:
      - backend
    restart: unless-stopped

  api:
    build: ./api
    environment:
      DB_HOST: postgres
      DB_NAME: ${DB_NAME}
      DB_USER: ${DB_USER}
      DB_PASSWORD: ${DB_PASSWORD}
      REDIS_HOST: redis
    networks:
      - backend
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    networks:
      - backend
    depends_on:
      - api
    restart: unless-stopped

networks:
  backend:

volumes:
  postgres-data:
```

### 3. .env file

```bash
DB_NAME=appdb
DB_USER=appuser
DB_PASSWORD=secret
```

Compose automatically reads `.env` from the same directory.

### 4. Bring it up

```bash
docker compose up --build -d
docker compose ps
docker compose logs api
```

### 5. Test it

```bash
# Add a message
curl -s -X POST http://localhost:8080/messages \
  -H "Content-Type: application/json" \
  -d '{"text": "hello from compose"}'

# First GET — hits the DB
curl -s http://localhost:8080/messages

# Second GET — hits the cache
curl -s http://localhost:8080/messages

# Restart the stack — data should survive (named volume)
docker compose down
docker compose up -d
curl -s http://localhost:8080/messages   # messages still there
```

### 6. Useful Compose commands to know

| Command | What it does |
|---|---|
| `docker compose up -d` | Start all services in the background |
| `docker compose down` | Stop and remove containers (volumes stay) |
| `docker compose down -v` | Also remove named volumes |
| `docker compose logs -f api` | Follow logs from the api service |
| `docker compose exec api bash` | Shell into the running api container |
| `docker compose ps` | Show status of all services |
| `docker compose build` | Rebuild images without starting |

---

## Guided questions

1. `depends_on` makes the API wait for Postgres to *start*. Does that mean Postgres is *ready* to accept connections? What is the difference, and how would you handle it properly?
2. What does `restart: unless-stopped` do? When would a container restart automatically?
3. The `.env` file is read by Compose, but it is not passed into the container automatically — you still need to declare each variable under `environment:`. Why is this, and is there a way to pass all of them at once?
4. `docker compose down` stops containers but keeps named volumes. Why is this the safe default? When would you add `-v` and what risk does that carry?
5. Two services are on the same `backend` network. What prevents the `nginx` container from directly connecting to `postgres` on port 5432?

---

## Stretch goals

- Add a `healthcheck` to the `postgres` service using `pg_isready` and make the API's `depends_on` wait for the `healthy` condition
- Add a `pgadmin` service so you can browse the database via a web UI
- Add a `--scale api=3` flag to run 3 API replicas behind Nginx and observe load balancing

---
## Write-up

**What I built:**
A four-service stack defined in one `compose.yaml`: nginx (the only public
service, port 8080), a Flask API, PostgreSQL 16 and Redis 7. The API stores
messages in Postgres and caches the list in Redis for 30 seconds; a POST
clears the cache. Database credentials come from a `.env` file that is
git-ignored, and a `.env.example` is committed instead. Postgres data lives
in a named volume.

I tested it end to end: the first GET returned `source: db`, the second
`source: cache`, and a new POST made the next GET read from the db again.
After `docker compose down` and `up -d` the messages were still there; after
`docker compose down -v` the list was empty.

**What I struggled with:**
- `curl -d '{"text": ...}'` breaks the JSON quotes in PowerShell, so I used
  `Invoke-RestMethod` instead.
- My phone hotspot had DNS problems and `pip install` retried a few times
  during the first build, but it finished.
- Understanding that `depends_on` only controls start order, not readiness.

**What I'd do differently:**
- Add a `pg_isready` healthcheck to Postgres and use
  `depends_on: condition: service_healthy`.
- Use two networks (frontend and backend) so nginx cannot reach the database.
- Add a `.gitignore` before the first commit (I did this one first).

---

## Guided questions — answers

**Q1 — depends_on vs actually ready:**
No. `depends_on` only waits until the container has *started*
(`condition: service_started`, which I saw in `docker compose config`).
Postgres needs some seconds after that (initdb on a fresh volume, recovery)
before it accepts connections, so the API could get connection errors during
that window. My app only connects on the first request, so I did not see an
error in my test, but the race exists. The proper fix is a healthcheck with
`pg_isready` plus `depends_on: postgres: condition: service_healthy`, and
retry logic in the app as a second layer.

**Q2 — restart: unless-stopped:**
It tells Docker to restart the container automatically if it crashes (exits
with an error) and also when the Docker daemon starts again, for example
after a reboot. It does not restart a container that I stopped manually
(`docker stop`, `docker compose stop` or `down`). Compared to `always`, the
manual stop is respected.

**Q3 — .env vs environment::**
Compose reads `.env` only to substitute `${VAR}` inside `compose.yaml`; it
does not copy the file into the containers. This is deliberate: each service
receives only the variables it needs (for example, nginx and redis get none),
which limits exposure of secrets. To pass everything at once, use
`env_file: - .env` on a service, but then it also gets variables it does not
need.

**Q4 — compose down keeps volumes:**
Containers are disposable and can be recreated at any time, but the data in
volumes is not, so `down` removes only the containers and network and keeps
the data. I confirmed this: after `down` and `up` my two messages were still
there. I would use `-v` when I want a clean start, for example resetting a
development database. The risk is permanent data loss with no undo: after
`down -v` my list went from two messages to empty. On a production database
it could destroy real data.

**Q5 — nginx can reach postgres?:**
Nothing prevents it in this setup. All four services are on the same
`backend` network, so any container can resolve and reach any other one. I
checked it: `docker compose exec nginx sh -c "nc -zv postgres 5432"` printed
`open`. Only the published port (`8080:80` on nginx) limits access from the
host, not from other containers. To really isolate the database I would
create two networks: `frontend` (nginx and api) and `backend` (api, postgres
and redis). Then nginx has no route to postgres.