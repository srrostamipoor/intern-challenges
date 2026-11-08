#!/bin/bash
# Docker cleanup script - removes unused resources safely
# Usage: ./cleanup.sh [--dry-run]
# Logs every action with a timestamp

set -euo pipefail

DRY_RUN=false
case "${1:-}" in
    "") ;;
    --dry-run) DRY_RUN=true ;;
    *) echo "Usage: $0 [--dry-run]"; exit 2 ;;
esac

LOG_FILE="cleanup_$(date +%Y%m%d_%H%M%S).log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

log "=== Docker Cleanup Starting (dry-run: $DRY_RUN) ==="
log "Disk usage BEFORE:"
docker system df | tee -a "$LOG_FILE"

echo ""
log "--- Step 1: Remove stopped containers ---"
if $DRY_RUN; then
    docker ps -a --filter status=exited --format '{{.Names}} ({{.Image}})' | tee -a "$LOG_FILE"
else
    docker container prune --force | tee -a "$LOG_FILE"
fi

log "--- Step 2: Remove dangling images (unnamed only) ---"
if $DRY_RUN; then
    docker image ls --filter dangling=true | tee -a "$LOG_FILE"
else
    docker image prune --force | tee -a "$LOG_FILE"
fi

log "--- Step 3: Remove unused networks ---"
if $DRY_RUN; then
    docker network ls | tee -a "$LOG_FILE"
    log "(dry-run: prune would remove the custom networks that have no containers)"
else
    docker network prune --force | tee -a "$LOG_FILE"
fi

# WARNING: volumes contain data - always prompt, never force in scripts
log "--- Step 4: Remove unused volumes (PROMPT) ---"
echo ""
echo "Unused volumes:"
docker volume ls --filter dangling=true | tee -a "$LOG_FILE"
echo ""
if $DRY_RUN; then
    log "Dry run: no volumes removed."
else
    read -rp "Remove unused volumes? (yes/NO): " confirm
    if [ "$confirm" = "yes" ]; then
        docker volume prune --force | tee -a "$LOG_FILE"
    else
        log "Skipped volume pruning."
    fi
fi

log "--- Step 5: Remove build cache ---"
if $DRY_RUN; then
    log "Dry run: build cache not touched."
else
    docker builder prune --force | tee -a "$LOG_FILE"
fi

echo ""
if $DRY_RUN; then
    log "=== Dry run complete, nothing was deleted. Log: $LOG_FILE ==="
else
    log "Disk usage AFTER:"
    docker system df | tee -a "$LOG_FILE"
    log "=== Cleanup complete. Log: $LOG_FILE ==="
fi