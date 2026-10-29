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

*(Fill this in after completing the challenge.)*

**Before/after disk usage I measured:**

| Resource | Before | After |
|---|---|---|
| Images | | |
| Containers | | |
| Volumes | | |
| Build cache | | |

**What `docker system prune -a --volumes` deletes:**

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — dangling vs unused image:**

**Q2 — build cache 450 MB:**

**Q3 — stopped container logs survive prune?:**

**Q4 — why volumes need a prompt:**

**Q5 — slow CI builds, right vs wrong solution:**
