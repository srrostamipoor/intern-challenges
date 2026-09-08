# Challenge 4 - Load Balancing

## What I did
I ran three instances of a simple web app (each returning a different server
ID), put nginx in front as a load balancer using round-robin, sent many
requests to confirm they were distributed, then configured a health check,
killed one backend, and confirmed traffic stopped going to it.

## My setup
- Three backend containers (`backend1`, `backend2`, `backend3`) on my custom
  network `intern-net`, each running the same Python app but with a different
  `SERVER_ID` (1, 2, 3) passed as an environment variable.
- One nginx container (`load-balancer`) in front of them.
- I sent requests from the `tcp-client` container.

## The web app (app.py)
A small Python HTTP server that listens on port 8080 and returns
`Response from SERVER <id>`. The ID comes from the `SERVER_ID` environment
variable, so the same code produces a different response in each container.

## The load balancer config (lb.conf)
```
upstream backends {
    server backend1:8080 max_fails=1 fail_timeout=5s;
    server backend2:8080 max_fails=1 fail_timeout=5s;
    server backend3:8080 max_fails=1 fail_timeout=5s;
}

server {
    listen 80;
    location / {
        proxy_pass http://backends;
    }
}
```
- `upstream backends` groups the three servers. nginx load-balances between
  them with round-robin by default.
- `proxy_pass http://backends` forwards each incoming request to one of the
  backends instead of serving content itself.
- `max_fails=1 fail_timeout=5s` is the health check: if a backend fails once,
  nginx stops sending traffic to it for 5 seconds (passive health check).

## The counting script (count.sh)
```
#!/bin/bash
for i in $(seq 1 30); do
    curl -s http://load-balancer
done | sort | uniq -c
```
It sends 30 requests and uses `sort | uniq -c` to count how many times each
backend answered.

## Results

### Round-robin working (all backends up)
Running `./count.sh` with all three backends alive:
```
      9 Response from SERVER 1
     11 Response from SERVER 2
     10 Response from SERVER 3
```
30 requests split almost evenly across the three servers - round-robin works.

### Health check working (one backend killed)
After `docker stop backend2`, running `./count.sh` again:
```
     13 Response from SERVER 1
     17 Response from SERVER 3
```
SERVER 2 disappears completely. The load balancer detected that backend2 was
down and sent all traffic only to the two healthy servers - exactly what the
health check should do.

## What I learned
- A load balancer forwards requests to backends instead of serving content
  itself; round-robin distributes them in turn.
- A container only stays alive while its main command runs. My backends use
  `sleep infinity` (plus the app) so they stay up; an early attempt with `bash`
  died as soon as the shell closed.
- With a health check configured, the service keeps working even when a backend
  fails - traffic automatically avoids the dead server.

## Files
- `app.py` - the backend web app.
- `lb.conf` - the nginx load balancer configuration.
- `count.sh` - the script that sends N requests and tallies the responses.
