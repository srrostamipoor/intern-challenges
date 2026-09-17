# Challenge 11 (Extra) - nginx Reverse Proxy Routing

## What I did
I ran three different services on the same host, put nginx in front of them as
a reverse proxy, and routed traffic to each service based on the request path.

## Scenario
Three services run on the same container (`svc-host`), each on its own port:
- API service   -> port 3000
- Admin service -> port 5000
- Web service   -> port 4000

nginx runs on the same host, listens on port 80, and routes:
- `/api`   -> API service
- `/admin` -> Admin service
- `/`      -> Web service (default)

## How it works
nginx acts as a **reverse proxy** - a middleman in front of the services.
Clients only talk to nginx on port 80; nginx forwards each request to the right
backend service based on the URL path. The services are never exposed directly.

Key parts of the config:
- **`upstream`** - defines each backend service by address and port
  (`127.0.0.1:3000` etc., since nginx and the services share the same host).
- **`server`** - nginx itself: `listen 80` is the port it accepts requests on,
  `server_name` is the domain it answers for.
- **`location`** - the routing rule: matches the URL path and forwards it.
- **`proxy_pass`** - sends the request to the chosen backend service.

nginx checks more specific paths (`/api`, `/admin`) first; anything else falls
through to `location /` (the default).

## The app (app.py)
A small Python HTTP server that returns `Response from SERVER <id>`. Both the
ID and the port come from environment variables, so the same file runs three
times on three ports with three different IDs.

## How to run
```
# start three services on one host
SERVER_ID=API   PORT=3000 python /app.py &
SERVER_ID=ADMIN PORT=5000 python /app.py &
SERVER_ID=WEB   PORT=4000 python /app.py &

# install nginx, drop in routing.conf, then:
nginx -t      # test the config
nginx         # start it
```

## Test results
From inside the host:
```
$ curl http://localhost/api        -> Response from SERVER API
$ curl http://localhost/admin      -> Response from SERVER ADMIN
$ curl http://localhost/           -> Response from SERVER WEB
$ curl http://localhost/anything   -> Response from SERVER WEB   (default)
```
Each path was correctly routed to its service, and unmatched paths fell through
to the default web service.

## Real-world note
In production, a client types a domain (e.g. `example.com`), DNS resolves it to
the nginx server's IP, and the browser sends a `Host` header. nginx uses that
`Host` header (`server_name`) to pick the right server block, then the path
(`location`) to route to the right service. In this test setup there's no real
DNS, so the same idea is reproduced with `localhost` / container names and, for
a custom domain, a `Host` header or the `/etc/hosts` file.

## Files
- `routing.conf` - the nginx reverse proxy configuration.
- `app.py` - the backend service (ID and port from environment variables).
