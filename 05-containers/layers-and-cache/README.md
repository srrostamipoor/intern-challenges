# Challenge 20 — Layers, Cache, and Image Size

## Scenario

> *"Our Docker images are 1.2 GB. They take 8 minutes to build and 4 minutes to push.
> Find out why, fix the Dockerfile, and prove it with numbers."*

Understanding how Docker layers and the build cache work is what separates someone
who can write a Dockerfile from someone who can write a *good* one.

---

## What you will build

Three versions of the same Dockerfile, measuring and explaining the difference:

| File | What it demonstrates |
|---|---|
| `Dockerfile.bad` | Common mistakes — fat image, broken cache |
| `Dockerfile.good` | Fixed layer order, cache-friendly |
| `Dockerfile.multistage` | Multi-stage build — smallest possible image |

A `Makefile` (or `build.sh`) that builds all three and prints the size of each.

---

## Deliverables

```
layers-and-cache/
├── app.py               # same Flask app from Challenge 19
├── requirements.txt
├── Dockerfile.bad
├── Dockerfile.good
├── Dockerfile.multistage
├── build.sh             # builds all three, prints sizes
└── README.md
```

---

## Functional requirements

### 1. Dockerfile.bad — write these mistakes deliberately

```dockerfile
# BAD: starts from the full (fat) base image
FROM python:3.11

# BAD: copies everything in one go — any file change busts the pip install layer
COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python", "app.py"]
```

Build it, note the size:
```bash
docker build -f Dockerfile.bad -t app:bad .
docker image inspect app:bad --format '{{.Size}}' | numfmt --to=iec
```

### 2. Dockerfile.good — fix every mistake

Rules:
- Use `python:3.11-slim` as the base
- Copy `requirements.txt` **before** the rest of the source
- Use `--no-cache-dir` and `--upgrade pip`
- Add a `.dockerignore`

After fixing:
```bash
docker build -f Dockerfile.good -t app:good .
```

Verify the cache works:
```bash
# Change only app.py (not requirements.txt), rebuild
echo "# change" >> app.py
docker build -f Dockerfile.good -t app:good .
# The "pip install" layer should show "CACHED"
```

### 3. Dockerfile.multistage — builder + runtime stages

```dockerfile
# Stage 1: builder — installs dependencies
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: runtime — copies only installed packages + app
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app.py .
ENV APP_ENV=production
EXPOSE 8080
CMD ["python", "app.py"]
```

### 4. build.sh — compare all three

```bash
#!/bin/bash
set -e

echo "Building app:bad..."
docker build -f Dockerfile.bad -t app:bad . -q

echo "Building app:good..."
docker build -f Dockerfile.good -t app:good . -q

echo "Building app:multistage..."
docker build -f Dockerfile.multistage -t app:multistage . -q

echo ""
echo "=== Image sizes ==="
docker image ls app:bad app:good app:multistage --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}"
```

### 5. What to document

Record the sizes you measured in your write-up. Explain *why* each one is the size it is.

---

## Guided questions

1. Docker builds images in layers. What exactly is a layer? Where are layers stored on the host machine?
2. A layer is "busted" (invalidated). What happens to all the layers after it in the build?
3. Why does copying `requirements.txt` first (before the rest of the source) make pip installs faster on re-builds?
4. What does `COPY --from=builder` do in a multi-stage build? Why does it reduce the final image size?
5. A co-worker says "just use `--no-cache` flag at build time to be safe". What is wrong with this advice?

---

## Stretch goals

- Use `dive` (a free CLI tool) to inspect the layers of `app:bad` and `app:good` side by side
- Add a `RUN apt-get clean && rm -rf /var/lib/apt/lists/*` after any `apt-get` command and explain what it removes
- Time the re-build of `app:good` after changing only `app.py` — the pip install should be near-instant

---
## Write-up

*(Fill this in after completing the challenge.)*

**Image sizes I measured:**

| Image | Size |
|---|---|
| app:bad | |
| app:good | |
| app:multistage | |

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — What is a layer:**

**Q2 — Cache busting cascade:**

**Q3 — requirements.txt first:**

**Q4 — COPY --from=builder:**

**Q5 — --no-cache always:**
