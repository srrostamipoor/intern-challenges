# Challenge 31 — Pipeline Caching

## Scenario

> *"Every pipeline run takes 8 minutes. `pip install` takes 5 of those 8 minutes.
> The dependencies haven't changed in 3 weeks. We're wasting 5 minutes per run, dozens of times a day."*

Caching is one of the highest-leverage optimizations in any CI/CD pipeline.
Done correctly, it can cut build times by 60–80% with minimal complexity.

---

## What you will build

A workflow with three versions of the same job — without cache, with pip cache, and with Docker layer cache — measuring the time savings at each step.

---

## Deliverables

```
pipeline-caching/
├── app/
│   ├── main.py
│   └── requirements.txt    # include several heavy packages
├── Dockerfile
├── .github/
│   └── workflows/
│       ├── no-cache.yaml
│       ├── pip-cache.yaml
│       └── docker-cache.yaml
└── README.md
```

---

## Functional requirements

### 1. requirements.txt — make it heavy enough to measure

```
flask
requests
pandas
numpy
boto3
psycopg2-binary
pytest
pytest-cov
flake8
```

This takes 60–90 seconds to install without caching.

### 2. no-cache.yaml — baseline (the slow version)

```yaml
---
name: No Cache (baseline)

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install (no cache)
        run: pip install -r app/requirements.txt
      - run: pytest app/
```

Time this run. It becomes your baseline.

### 3. pip-cache.yaml — cache pip dependencies

```yaml
---
name: With pip Cache

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"                           # ← this one line enables pip caching
          cache-dependency-path: app/requirements.txt

      - name: Install (with cache)
        run: pip install -r app/requirements.txt
        # First run: downloads and caches packages (~90s)
        # Second run: restores from cache (~5s)

      - run: pytest app/
```

**How it works:** `actions/setup-python` with `cache: "pip"` automatically:
1. Computes a cache key from the hash of `requirements.txt`
2. Restores the pip download cache if the key matches
3. After the job, saves the cache for future runs

Cache key logic:
```
cache key = OS + python version + hash(requirements.txt)
```

If `requirements.txt` changes → cache miss → fresh install → new cache saved.
If `requirements.txt` is unchanged → cache hit → packages restored instantly.

### 4. docker-cache.yaml — cache Docker build layers

```yaml
---
name: With Docker Cache

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/cache-demo:latest
          cache-from: type=registry,ref=${{ secrets.DOCKERHUB_USERNAME }}/cache-demo:buildcache
          cache-to:   type=registry,ref=${{ secrets.DOCKERHUB_USERNAME }}/cache-demo:buildcache,mode=max
          # ↑ stores the build cache in the registry itself
          # First run: builds all layers (~3 min)
          # Subsequent runs: restores unchanged layers from cache (~30s)
```

This uses Docker BuildKit's inline cache. The cache is stored in the Docker registry
as a special manifest — no separate cache storage needed.

### 5. Measure and document

Run each workflow at least twice and record times:

| Workflow | First run | Second run (cache warm) | Savings |
|---|---|---|---|
| no-cache | ___s | ___s | 0% |
| pip-cache | ___s | ___s | ___% |
| docker-cache | ___s | ___s | ___% |

### 6. Cache invalidation — test it

After warming the pip cache:
```bash
# Add one new package to requirements.txt
echo "httpx" >> app/requirements.txt
git commit -am "add httpx"
git push
```

Observe: the cache key changes (different `requirements.txt` hash),
so pip installs everything fresh. The new cache is then stored for future runs.

---

## How GitHub Actions cache works (the mechanism)

```
1. Job starts
2. actions/cache (or setup-python/cache) computes a cache key
3. If key matches a stored cache → restore it → skip install
4. Job runs
5. If it was a cache miss → save the newly installed packages as a new cache entry

Cache storage limit: 10 GB per repository (older entries are evicted automatically)
Cache entries expire: after 7 days of not being accessed
```

---

## Guided questions

1. The pip cache key includes the hash of `requirements.txt`. Why hash the file rather than just use the filename as the key?
2. You add a comment to `requirements.txt` (no new packages). Does the cache invalidate? Should it?
3. What is `cache: "pip"` actually caching — the downloaded `.whl` files, the installed packages, or both?
4. Docker layer caching: if you change `app.py` but not `requirements.txt`, which layers are rebuilt and which are cached?
5. Caching makes the pipeline faster but can hide problems. Give an example of a bug that caching could mask.

---

## Stretch goals

- Add a `restore-keys:` fallback so that even a partial cache match (different Python version) restores something useful
- Cache Node.js `node_modules` in a project that uses both Python and JS
- Write a job that prints the cache hit/miss status and fails if it expected a hit but got a miss

---
## Write-up

*(Fill this in after completing the challenge.)*

**Times I measured:**

| Workflow | First run | Second run | Savings |
|---|---|---|---|
| no-cache | | | 0% |
| pip-cache | | | |
| docker-cache | | | |

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — hash the file, not the name:**

**Q2 — comment in requirements.txt:**

**Q3 — what pip cache stores:**

**Q4 — Docker layer rebuild on app.py change:**

**Q5 — bug that caching masks:**
