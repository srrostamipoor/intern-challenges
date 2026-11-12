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

**Times I measured:**

All times are the `build` job duration from the Actions UI (GitHub-hosted
`ubuntu-latest`, Python 3.11, same `requirements.txt`).

| Workflow | First run | Second run (cache warm) | Savings |
|---|---|---|---|
| no-cache | 18s | 22s (4 runs ranged 14-22s) | 0% (baseline) |
| pip-cache | 18s (miss, +2s to save cache) | 19s (hit; 17s in a later run) | ~0%, within noise |
| docker-cache | 44s (cold, incl. 9s cache export) | 27s | 39% of the job, 62% of the build step (29s -> 11s) |

Cache invalidation (added `httpx` to `requirements.txt`):

| Workflow | Result |
|---|---|
| pip-cache | key changed, but `setup-python` fell back to the previous cache by prefix; only 5 new packages were downloaded, then a new cache was saved. Job 22s. |
| docker-cache | cache manifest imported, but `COPY requirements.txt` and `RUN pip install` ran again (12.5s). Job 45s, back to the cold time. |

**What I struggled with:**
- The README promised pip install would take 60-90s and drop to ~5s. On GitHub's
  runners it took only 9-16s without cache, because downloads run at 150-700 MB/s
  (`0:00:00` per wheel in the log). With the pip cache hit the install step was
  still 10-12s, so the pip cache gave no measurable gain; run-to-run noise
  (14-22s for the identical baseline) was larger than any difference.
- The reason is what `cache: "pip"` stores: the pip download cache (~54 MB of
  wheels), not the installed packages. Unpacking and installing pandas/numpy still
  happens on every run, and restoring/saving the cache costs 2-3s extra.
- The Docker layer cache did pay off, because a cache hit skips the whole
  `RUN pip install` layer (download + install), not just the download.
- On the very first docker run the log shows `importing cache manifest ... ERROR:
  not found`. That is expected: the `buildcache` tag does not exist yet, and the
  build continues and creates it.
- I first predicted that adding a package would force a full re-download in
  pip-cache. It does not: `setup-python` automatically uses a prefix restore key and
  restores the nearest older cache.
- With four workflows triggered by every push, it took care to match each log to
  the right workflow.

**What I'd do differently:**
- Measure on a workload where caching matters (slow downloads, or packages that must
  be compiled from source) before adding cache steps; here the pip cache is
  complexity without a benefit.
- Pin dependency versions (or use a lock file), so a cache hit cannot hide newer
  versions and the hash of `requirements.txt` reflects the real environment.
- Keep Dockerfile order cache-friendly (copy `requirements.txt`, install, then copy
  code), and consider caching the virtualenv itself if install time dominates.
- Delete the Docker Hub token created for this demo when finished.

---

## Guided questions — answers

**Q1 — hash the file, not the name:**
The file name never changes, but its content does. A key built from the name alone
would keep matching after a dependency changed, so the job would restore stale
packages that no longer match `requirements.txt`. A hash of the content makes the
key change exactly when the content changes (content-addressed). In the logs the key
ends with a different hash after I added `httpx`.

**Q2 — comment in requirements.txt:**
Yes, the key changes, because any byte change changes the hash. It arguably should
not, since the installed packages are the same, but the hash cannot know that. I
reasoned this from how the hash works; I did not run this exact test. The cost
differs by cache type: with pip-cache the prefix fallback restores the older cache,
so the extra cost is small; with the Docker layer cache, `COPY requirements.txt`
changes, so the expensive `RUN pip install` layer (~12s here) is rebuilt for a
comment-only change.

**Q3 — what pip cache stores:**
The downloaded wheel files (pip's download cache at `~/.cache/pip`, ~54 MB), not the
installed packages. Evidence: with a cache hit the log shows `Using cached X.whl`
instead of `Downloading`, but `Installing collected packages` still runs and the
install step took 10-12s, about the same as without cache.

**Q4 — Docker layer rebuild on app.py change:**
Only `COPY app/ .` (the last layer) and the image export are rebuilt. `FROM`,
`WORKDIR`, `COPY requirements.txt` and `RUN pip install` come from cache, because
their inputs did not change. Observed: the build step dropped from 29s to 11s. If
`requirements.txt` changes instead, everything after `COPY requirements.txt` is
rebuilt (observed: `pip install` ran again, 12.5s).

**Q5 — bug that caching masks:**
A cached environment can hide a problem that a clean install would show. For
example, a dependency version that was yanked or whose newer release breaks the app
keeps "working" in CI because the old wheel or old layer is reused, and it fails
later on a fresh machine or a production image build. With unpinned requirements, the
Docker layer cache can also keep serving old, possibly vulnerable package versions
until `requirements.txt` happens to change, and then many versions jump at once.
Mitigation: pin versions and periodically run a build without cache.
