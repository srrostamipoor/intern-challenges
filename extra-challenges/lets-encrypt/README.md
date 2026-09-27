# Extra Challenge - Let's Encrypt & self-signed certificates

## Goal
Understand how Let's Encrypt / certbot works, and how it differs from a
self-signed certificate. The point wasn't to get a real certificate (that needs
a real public domain), but to understand the process.

## What is Let's Encrypt?
Let's Encrypt is a free, trusted Certificate Authority (CA). You get a
certificate from it using a tool called **certbot**. Because it's a trusted CA,
browsers trust its certificates - unlike a self-signed certificate.

## How certbot works (what I observed)
I installed certbot and ran:
```
certbot certonly --standalone -d <domain>
```
- `certonly` - just obtain the certificate.
- `--standalone` - certbot starts its own temporary web server for verification.
- `-d <domain>` - the domain to get a certificate for.

The process I saw:
1. certbot registers an account with Let's Encrypt (the ACME server).
2. It requests a certificate for the domain.
3. To prove I own the domain (an **ACME HTTP-01 challenge**), certbot:
   - creates a challenge file on the machine,
   - starts a temporary web server on port 80 to serve that file.
4. Let's Encrypt then tries to reach `http://<domain>/.well-known/acme-challenge/...`
   to check the file is there. If it is, it proves I control the domain, and the
   certificate is issued.

## What happened in my local setup (the two tests)

**Test 1 - example.com:**
```
Cannot issue for "example.com": ... forbidden by policy
```
`example.com` is a reserved example domain, so Let's Encrypt refuses it by policy
before even checking ownership.

**Test 2 - a made-up domain:**
```
DNS problem: NXDOMAIN looking up A for sara-test-internship.com
Hint: The Certificate Authority failed to download the challenge files from the
temporary standalone webserver started by Certbot on port 80.
```
This time certbot went further and actually started the temporary web server and
created the challenge file. It failed because:
- the domain doesn't exist in DNS (NXDOMAIN), and
- even if it did, it doesn't point to my local container, so Let's Encrypt (from
  the internet) can't reach the challenge file.

This is exactly why Let's Encrypt needs a **real, publicly reachable domain**.

## Let's Encrypt vs self-signed

| | self-signed | Let's Encrypt |
|---|---|---|
| Signed by | yourself (openssl) | a trusted CA |
| Browsers trust it? | No (security warning) | Yes |
| Ownership check | none | ACME challenge (proves you own the domain) |
| Validity | any length you set | 90 days |
| Renewal | manual | automatic (certbot renew) |
| Needs a real domain? | No | Yes |
| Use case | testing / internal | real public sites |
| Tool | openssl | certbot |

## Key takeaway
A self-signed certificate you sign yourself, so browsers don't trust it - fine
for testing. A Let's Encrypt certificate is signed by a trusted CA and proves
domain ownership through an ACME challenge, so browsers trust it - which is why
it's used for real public websites. The trade-off is that it needs a real domain
and auto-renews every 90 days.

## Note
No real certificate was issued, because this was a local environment with no
public domain. The goal (per the task) was to understand how certbot and the
ACME process work, which the two tests above demonstrate.
