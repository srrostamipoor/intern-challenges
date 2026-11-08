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

# Create orphaned volumes
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