# Challenge 26 — Docker Cleanup and Resource Management

## Scenario

> *"The CI server's disk is full. Docker has been running for 6 months accumulating
> dangling images, stopped containers, unused volumes, and unnamed networks.
> Figure out what's consuming space and clean it up safely — without deleting anything that's still in use."*

This is an operational challenge. It's less about writing code and more about understanding
what Docker accumulates over time, how to inspect it, and how to clean it up deliberately.

---

## What you will build

A `cleanup.sh` script that:
1. Reports current disk usage (before)
2. Prunes only what is safe to remove
3. Reports disk usage again (after)
4. Logs what was removed and when

You'll also deliberately create a "mess" to clean up so you can observe the whole cycle.

---

## Deliverables

```
docker-cleanup/
├── make_mess.sh    # creates junk for you to clean up
├── cleanup.sh      # the safe, documented cleanup script
├── README.md
```

---

## Functional requirements

### 1. Understand what Docker accumulates

| Type | What it is | Safe to remove if... |
|---|---|---|
| Dangling image | An image with no name (replaced by a newer build) | Always safe |
| Unused image | A named image not used by any container | If you don't need to run it again |
| Stopped container | A container that has exited | If you don't need its logs or data |
| Unused volume | A named volume not mounted by any container | ⚠ Only if you don't need the data |
| Unused network | A custom network with no containers on it | Always safe |
| Build cache | Intermediate layers from past builds | Safe (will slow next build) |

### 2. make_mess.sh — create something to clean up

```bash
#!/bin/bash
# Creates intentional Docker junk so you have something to clean

echo "=== Creating mess... ==="

# Pull some images we won't keep containers for
docker pull alpine:3.18
docker pull alpine:3.19
docker pull hello-world

# Run containers and stop them (don't remove)
docker run --name mess-1 alpine:3.18 echo "junk container 1"
docker run --name mess-2 alpine:3.19 echo "junk container 2"
docker run --name mess-3 hello-world

# Create an orphaned volume
docker volume create orphan-vol-1
docker volume create orphan-vol-2

# Create orphaned networks
docker network create orphan-net-1
docker network create orphan-net-2

# Build the same image twice to create a dangling layer
mkdir -p /tmp/dangling-test
echo -e "FROM alpine\nRUN echo v1" > /tmp/dangling-test/Dockerfile
docker build -t dangling-test:latest /tmp/dangling-test
echo -e "FROM alpine\nRUN echo v2" > /tmp/dangling-test/Dockerfile
docker build -t dangling-test:latest /tmp/dangling-test
# The first build is now dangling

echo ""
echo "=== Current usage ==="
docker system df
```

### 3. cleanup.sh — safe, targeted pruning

```bash
#!/bin/bash
# Docker cleanup script — removes unused resources safely
# Logs every action with a timestamp

set -euo pipefail

LOG_FILE="cleanup_$(date +%Y%m%d_%H%M%S).log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

log "=== Docker Cleanup Starting ==="
log "Disk usage BEFORE:"
docker system df | tee -a "$LOG_FILE"

echo ""
log "--- Step 1: Remove stopped containers ---"
docker container prune --force | tee -a "$LOG_FILE"

log "--- Step 2: Remove dangling images (unnamed only) ---"
docker image prune --force | tee -a "$LOG_FILE"

log "--- Step 3: Remove unused networks ---"
docker network prune --force | tee -a "$LOG_FILE"

# WARNING: volumes contain data — always prompt, never force in scripts
log "--- Step 4: Remove unused volumes (PROMPT) ---"
echo ""
echo "⚠  Unused volumes:"
docker volume ls --filter dangling=true
echo ""
read -rp "Remove all unused volumes? (yes/NO): " confirm
if [ "$confirm" = "yes" ]; then
    docker volume prune --force | tee -a "$LOG_FILE"
else
    log "Skipped volume pruning."
fi

log "--- Step 5: Remove build cache ---"
docker builder prune --force | tee -a "$LOG_FILE"

echo ""
log "Disk usage AFTER:"
docker system df | tee -a "$LOG_FILE"

log "=== Cleanup complete. Log: $LOG_FILE ==="
```

### 4. The nuclear option — and why to avoid it

```bash
# This removes EVERYTHING not currently running — use only on dev machines
docker system prune -a --volumes
```

**Never run this on a production host or a CI server with cached layers you want to keep.**

Document in your write-up: what exactly does `docker system prune -a --volumes` delete?

### 5. Useful inspection commands

Learn and document what each of these shows:

```bash
# Disk usage summary
docker system df
docker system df -v    # verbose: lists each image/volume

# What images exist
docker image ls -a     # -a shows intermediate layers too
docker image ls --filter dangling=true   # only dangling

# What containers exist (including stopped)
docker ps -a
docker ps -a --filter status=exited

# What volumes exist
docker volume ls
docker volume ls --filter dangling=true

# What networks exist
docker network ls
```

### 6. Run the full cycle

```bash
chmod +x make_mess.sh cleanup.sh
./make_mess.sh
./cleanup.sh
```

Record the before/after disk usage numbers in your write-up.

---

## Guided questions

1. What is a "dangling" image? How is it different from an "unused" image? Which `docker image prune` flag removes both?
2. `docker system df` shows "Build Cache: 450 MB". What created this cache and is it safe to delete?
3. You have a stopped container with logs you need (`docker logs my-container`). If you run `docker container prune`, do you lose the logs?
4. Why does `cleanup.sh` prompt before pruning volumes, but not before pruning containers and networks?
5. On a CI/CD server, builds are slow because the Docker layer cache is always empty. What is the right solution — and what is the wrong solution?

---

## Stretch goals

- Set up a `cron` job that runs `docker image prune -f` nightly (use `crontab -e`)
- Write a Python version of `cleanup.sh` using the `docker` Python SDK (`pip install docker`) instead of shell commands
- Add a `--dry-run` flag to `cleanup.sh` that shows what *would* be deleted without actually deleting anything

---
## Write-up

**Before/after disk usage I measured:**

Measured with `docker system df`: "before" is right after `make_mess.sh`,
"after" is right after `cleanup.sh` (answering `yes` to the volume prompt).

| Resource | Before | After |
|---|---|---|
| Images | 23 (12 active), 4.987 GB, 633.4 MB reclaimable | 22 (2 active), 4.987 GB, 2.887 GB reclaimable (57%) |
| Containers | 26 (2 active), 1.272 GB | 2 (2 active), 237.6 kB |
| Volumes | 14 (1 active), 96.59 MB | 5 (1 active), 96.59 MB |
| Build cache | 92 entries, 2.442 GB | 42 entries, 2.211 GB |

What each step actually freed: containers 1.272 GB (23 stopped containers),
dangling image 11 kB, volumes 356 B (9 anonymous volumes), build cache
230.7 MB. Networks `orphan-net-1`, `orphan-net-2` and `intern-net` were
removed. I only looked at `docker system df`, not at the free space on
Windows.

**What `docker system prune -a --volumes` deletes:**
Everything not in use, in one command: all stopped containers, all networks
not used by a container, all images not used by at least one container (not
just dangling ones, because of `-a`), unused build cache, and unused
volumes. In my Docker version `docker system prune --help` says
`--volumes  Prune anonymous volumes`, so named volumes are kept unless
`docker volume prune --all` is used. It is meant only for development
machines; on a production host or a CI server it would delete cached layers
and images that are needed.

**What I struggled with:**
- The challenge's `cleanup.sh` prunes everything on the machine, not only the
  junk from `make_mess.sh`. My laptop had about 20 other stopped containers
  from earlier challenges, so before running it I decided to accept that
  loss and copied the files of the one container I cared about
  (`devops-practice`) to a backup folder with `docker cp`. The copy gave a
  symlink error for a `.venv` folder (Windows cannot create symlinks without
  extra rights), but the other files were copied.
- The list shown before the volume prompt (`docker volume ls --filter
  dangling=true`) had 13 volumes, but `docker volume prune` removed only the
  9 anonymous ones and kept the 4 named ones, so the list and the action did
  not match.
- I expected the first `dangling-test` build to become a dangling image, but
  the only unnamed image was the old `hello-world` that I replaced with a new
  pull. I do not know exactly why; it may be how this Docker Desktop stores
  images.

**What I'd do differently:**
- Put a label on the junk resources and prune only those
  (`--filter "label=..."`), so the script is safe on a machine with other
  work on it.
- Use `docker image prune -a --filter "until=..."` on a schedule instead of
  removing everything, and keep the build cache that is useful.
- Make the dry-run listing match what prune will really do (for example,
  list only anonymous volumes).

I also added a `--dry-run` option to `cleanup.sh` (a stretch goal): it
prints what would be removed and deletes nothing.

---

## Guided questions — answers

**Q1 — dangling vs unused image:**
A dangling image has no name or tag (`<none>`), for example an old image
whose tag moved to a newer build; I saw the old `hello-world` become
`<untagged>` after pulling a newer one. An unused image has a name but no
container uses it; after the cleanup my laptop had 20 such images
(2.887 GB reclaimable, 57%). `docker image prune` removes only dangling ones,
and `docker image prune -a` removes both. I tested it with a labelled
`junk-demo` image: plain `prune` reclaimed 0B, `prune -a` deleted it.

**Q2 — build cache 450 MB:**
The cache is created by `docker build`: BuildKit stores the result of each
build step so unchanged steps are reused (the `CACHED` lines). It is safe to
delete; nothing needs it to run, only the next build gets slower because
steps like `pip install` or `apt-get` run again. On my machine the cache was
2.442 GB in 92 entries; `docker builder prune` freed 230.7 MB, and the
remaining 2.2 GB was shown as not reclaimable (probably still linked to
existing images, I did not verify it).

**Q3 — stopped container logs survive prune?:**
No. The logs belong to the container, so removing it removes them. I tested
it: `docker logs log-test` worked, then after `docker container prune` it
returned `No such container: log-test`. If I need the logs I must save them
first (`docker logs name > file.txt`).

**Q4 — why volumes need a prompt:**
Volumes hold persistent data, such as a database, which cannot be rebuilt
from an image and cannot be restored after deletion. Containers and networks
can be recreated from their definition, so deleting them is not harmful. I
also saw that Docker itself is careful with them: from 13 listed volumes
the prune removed only the 9 anonymous ones and kept the 4 named ones, and
removing those needs `--all`.

**Q5 — slow CI builds, right vs wrong solution:**
The right solution is to make the cache survive between builds: keep a
persistent cache on the runner, or export and import it (for example
`--cache-to` and `--cache-from` with a registry or the CI's cache), keep
rarely changing steps early in the Dockerfile, and prune only by age
(`--filter "until=..."`) on a schedule so the disk does not fill. The wrong
solutions are wiping everything before every build (`docker system prune -a`
or `--no-cache`), using runners that start empty with no cache storage, or
the opposite mistake of never cleaning until the disk is full.