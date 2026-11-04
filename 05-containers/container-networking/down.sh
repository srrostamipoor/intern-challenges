#!/bin/bash
docker rm -f nginx api redis 2>/dev/null || true
docker network rm app-net 2>/dev/null || true