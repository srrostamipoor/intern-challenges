#!/bin/bash
set -e

# clean up leftovers from earlier runs
docker rm -f demo1 demo2 demo3 2>/dev/null || true
docker volume rm visit-data 2>/dev/null || true
rm -rf local-data

echo "=== Demo 1: no mount ==="
docker run -d -p 8080:8080 --name demo1 visit-counter:1.0 > /dev/null
sleep 3
curl -s http://localhost:8080/; echo
curl -s http://localhost:8080/; echo
docker rm -f demo1 > /dev/null
docker run -d -p 8080:8080 --name demo1 visit-counter:1.0 > /dev/null
sleep 3
curl -s http://localhost:8080/; echo   # back to 1
docker rm -f demo1 > /dev/null

echo "=== Demo 2: bind mount ==="
mkdir -p ./local-data
docker run -d -p 8080:8080 -v "$(pwd)/local-data:/data" --name demo2 visit-counter:1.0 > /dev/null
sleep 3
curl -s http://localhost:8080/; echo
curl -s http://localhost:8080/; echo
cat ./local-data/visits.txt; echo
docker rm -f demo2 > /dev/null
docker run -d -p 8080:8080 -v "$(pwd)/local-data:/data" --name demo2 visit-counter:1.0 > /dev/null
sleep 3
curl -s http://localhost:8080/; echo   # 3
docker rm -f demo2 > /dev/null

echo "=== Demo 3: named volume ==="
docker volume create visit-data > /dev/null
docker run -d -p 8080:8080 -v visit-data:/data --name demo3 visit-counter:1.0 > /dev/null
sleep 3
curl -s http://localhost:8080/; echo
docker rm -f demo3 > /dev/null
docker run -d -p 8080:8080 -v visit-data:/data --name demo3 visit-counter:1.0 > /dev/null
sleep 3
curl -s http://localhost:8080/; echo   # 2
docker rm -f demo3 > /dev/null
docker volume inspect visit-data

docker volume rm visit-data