#!/bin/bash
for i in $(seq 1 30); do
    curl -s http://load-balancer
done | sort | uniq -c
