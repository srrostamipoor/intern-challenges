#!/bin/bash
set -e

docker network create app-net 2>/dev/null || true

docker run -d --name redis --network app-net redis:7-alpine > /dev/null
until docker exec redis redis-cli ping 2>/dev/null | grep -q PONG; do sleep 1; done

docker build -t api:1.0 ./api -q
docker run -d --name api --network app-net api:1.0 > /dev/null
sleep 3

docker run -d --name nginx --network app-net -p 8080:80 \
  -v "$(pwd)/nginx/nginx.conf:/etc/nginx/nginx.conf:ro" nginx:alpine > /dev/null

echo "Up. Try: curl http://localhost:8080/"