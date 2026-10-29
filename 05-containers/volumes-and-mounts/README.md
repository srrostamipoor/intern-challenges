# Challenge 21 — Volumes and Bind Mounts

## Scenario

> *"The container works great until we restart it — then all the data is gone.
> We need persistent storage for the database. We also need the app source to update
> live in development without rebuilding the image every time."*

This challenge is about the two ways to get data in and out of a running container:
**bind mounts** (for development) and **named volumes** (for persistence).

---

## What you will build

A small app that writes data to a file — and three different ways to run it:

| Mode | How | When to use |
|---|---|---|
| No mount | Data lives inside the container only | Never (it disappears on restart) |
| Bind mount | Host directory ↔ container path | Development (live code reloading) |
| Named volume | Docker-managed volume | Production (persistent DB/data) |

---

## Deliverables

```
volumes-and-mounts/
├── app.py            # writes a visit counter to /data/visits.txt
├── requirements.txt
├── Dockerfile
├── run.sh            # three demo commands (no mount / bind / volume)
└── README.md
```

---

## Functional requirements

### 1. The app

`app.py` — a Flask app that tracks visits in a flat file:

```python
from flask import Flask, jsonify
import os

app = Flask(__name__)
DATA_FILE = "/data/visits.txt"

def read_count():
    os.makedirs("/data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        return 0
    with open(DATA_FILE) as f:
        return int(f.read().strip() or 0)

def write_count(n):
    with open(DATA_FILE, "w") as f:
        f.write(str(n))

@app.route("/")
def index():
    count = read_count() + 1
    write_count(count)
    return jsonify({"visits": count})

@app.route("/reset")
def reset():
    write_count(0)
    return jsonify({"visits": 0})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### 2. Build the image

```bash
docker build -t visit-counter:1.0 .
```

### 3. Demo 1 — no mount (data lost on restart)

```bash
docker run -d -p 8080:8080 --name demo1 visit-counter:1.0
curl http://localhost:8080/    # visits: 1
curl http://localhost:8080/    # visits: 2
docker rm -f demo1

docker run -d -p 8080:8080 --name demo1 visit-counter:1.0
curl http://localhost:8080/    # visits: 1 again — counter reset!
docker rm -f demo1
```

Observe: the `/data/visits.txt` inside the container is gone when the container is removed.

### 4. Demo 2 — bind mount (host directory)

```bash
mkdir -p ./local-data

docker run -d -p 8080:8080 \
  -v "$(pwd)/local-data:/data" \
  --name demo2 visit-counter:1.0

curl http://localhost:8080/    # visits: 1
curl http://localhost:8080/    # visits: 2
cat ./local-data/visits.txt    # you can read it from the host!

docker rm -f demo2

docker run -d -p 8080:8080 \
  -v "$(pwd)/local-data:/data" \
  --name demo2 visit-counter:1.0

curl http://localhost:8080/    # visits: 3 — persisted!
docker rm -f demo2
```

### 5. Demo 3 — named volume (Docker-managed)

```bash
docker volume create visit-data

docker run -d -p 8080:8080 \
  -v visit-data:/data \
  --name demo3 visit-counter:1.0

curl http://localhost:8080/    # visits: 1
docker rm -f demo3

docker run -d -p 8080:8080 \
  -v visit-data:/data \
  --name demo3 visit-counter:1.0

curl http://localhost:8080/    # visits: 2 — persisted!
docker rm -f demo3

# Inspect where Docker stores the volume on the host
docker volume inspect visit-data
```

### 6. Cleanup

```bash
docker volume rm visit-data
```

---

## Key concepts table

| | Bind mount | Named volume |
|---|---|---|
| Path on host | You choose (e.g. `./local-data`) | Docker manages (`/var/lib/docker/volumes/…`) |
| Good for | Dev — live code edits | Prod — DB files, persistent state |
| Portable | No (tied to host path) | Yes (works on any Docker host) |
| Backed up how | Copy the host directory | `docker volume inspect`, then copy |

---

## Guided questions

1. What happens to a named volume when you run `docker rm` the container? Does the data survive?
2. What is the difference between `-v ./local-data:/data` (bind mount) and `-v visit-data:/data` (named volume)? How does Docker know which is which?
3. In the bind mount demo, you can edit `./local-data/visits.txt` from the host and the container will see the change immediately. Why is this useful in development but dangerous in production?
4. Where does Docker physically store a named volume on a Linux host? What command shows you?
5. You run a database container with a named volume. You delete the container. Where is the data?

---

## Stretch goals

- Use `docker run --mount` syntax instead of `-v` and note the difference in readability
- Mount the `app.py` file itself as a bind mount and edit it live — see Flask auto-reload without rebuilding
- Write a `backup.sh` that uses `docker run --rm -v visit-data:/source -v $(pwd):/backup alpine tar czf /backup/visit-data.tar.gz -C /source .` to back up the volume

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — volume survives rm:**

**Q2 — bind vs named volume syntax:**

**Q3 — bind mounts in dev vs prod:**

**Q4 — where Docker stores volumes:**

**Q5 — db container deleted, data?:**
