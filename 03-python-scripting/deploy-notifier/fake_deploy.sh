#!/bin/bash
set -e

ENV=${1:-staging}
echo "[$(date)] Starting deploy to $ENV..."
sleep 2
echo "[$(date)] Pulling latest Docker image..."
sleep 1
echo "[$(date)] Running migrations..."

# Simulate a 30% chance of failure
if [ $((RANDOM % 10)) -lt 3 ]; then
    echo "ERROR: Migration failed - connection refused" >&2
    exit 1
fi

echo "[$(date)] Restarting service..."
sleep 1
echo "[$(date)] Deploy complete."
