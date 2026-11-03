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
docker image ls app --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}"