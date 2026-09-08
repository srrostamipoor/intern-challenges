# Challenge 3 - HTTP/HTTPS

## What I did
I ran an nginx container serving a static page over plain HTTP, captured the
raw request/response with `curl -v`, then generated a self-signed TLS
certificate, configured nginx for HTTPS, and captured the TLS handshake.

## My setup
- I ran an nginx container named `web-server` on my custom network `intern-net`.
- I replaced the default page with my own `index.html`.
- I queried it from the `tcp-client` container using curl.
- nginx listens on port 80 (HTTP) and, after configuration, port 443 (HTTPS).

## Part 1 - HTTP
I served `index.html` over HTTP and ran `curl -v http://web-server`.

Key headers in the response:
- `HTTP/1.1 200 OK` - the request succeeded (2xx = success).
- `Server: nginx/1.31.5` - the server software (my own nginx now, not a public one).
- `Content-Type: text/html` - the response is an HTML page.
- `Content-Length: 238` - the exact size of the page in bytes.
- `Connection: keep-alive` - the connection stays open for the next request.
- `ETag` - a unique tag for this version of the page, used for caching.

## Part 2 - HTTPS with a self-signed certificate

### Generating the certificate (two steps)
1. Create a private key:
   `openssl genrsa -out /etc/nginx/server.key 2048`
2. Create a self-signed certificate from that key:
   `openssl req -new -x509 -key /etc/nginx/server.key -out /etc/nginx/server.crt -days 365 -subj "/CN=web-server"`

The private key got permissions 600 automatically (owner-only), because it
must stay secret. The public key is not a separate file - it lives inside the
certificate.

### nginx config
I added a second server block listening on port 443 with `ssl`, pointing to
the certificate and key:
```
server {
    listen 443 ssl;
    server_name localhost;
    ssl_certificate     /etc/nginx/server.crt;
    ssl_certificate_key /etc/nginx/server.key;
    location / { root /usr/share/nginx/html; index index.html; }
}
```
Then I tested and reloaded: `nginx -t` and `nginx -s reload`.

### Testing HTTPS
I ran `curl -vk https://web-server` (the `-k` tells curl to accept the
self-signed certificate, which it otherwise wouldn't trust).

## What's different between HTTP and HTTPS
The big difference is the TLS handshake, which HTTP does not have. Before any
data is exchanged, the client and server go through:
- **Client Hello** - client sends supported TLS versions, a list of cipher
  suites, and a random number.
- **Server Hello** - server picks the version and cipher and sends its own
  random number.
- **Certificate** - server sends its certificate (which contains its public key).
- **Certificate Verify** - server proves it owns the private key matching the
  certificate.
- **Finished** - both sides derive a shared secret key (never sent over the
  wire) and switch to encrypted communication.

After the handshake, the request/response is the same as HTTP - just encrypted.

## What I observed
- The HTTPS connection used TLSv1.3 with AES-256 encryption.
- The certificate showed `subject: CN=web-server` and `issuer: CN=web-server` -
  both the same, which is exactly what "self-signed" means (it signs itself,
  instead of being signed by a trusted CA).
- curl reported `self-signed certificate (18), continuing anyway` because of the
  `-k` flag. In a real setup with a CA-signed certificate, this warning wouldn't
  appear.
- The public key is embedded inside the certificate, so there's no separate
  `.pub` file like there was with SSH.

## Files
- `index.html` - the static page I served.
- `nginx-default.conf` - my nginx configuration (HTTP + HTTPS server blocks).

## Note on security
I did NOT commit `server.key` (the private key) or `server.crt` to the repo.
Private keys must never be pushed to a shared/public place. The README contains
the exact commands to regenerate them instead.
