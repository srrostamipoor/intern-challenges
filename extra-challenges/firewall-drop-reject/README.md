# Extra Challenge - iptables DROP vs REJECT

## Goal
Understand the difference between `DROP` and `REJECT` in iptables by testing
both on the same blocked port.

## Setup
- A container `fw-test` started with `--cap-add=NET_ADMIN` so iptables works.
- A test web server on port 8080 (`python3 -m http.server 8080`).
- I tested from another container (`tcp-client`), because iptables INPUT rules
  apply to traffic coming from outside, not to localhost traffic (which uses the
  `lo` interface).

## Test 1 - DROP
```
iptables -A INPUT -p tcp --dport 8080 -j DROP
```
From the client:
```
$ curl --max-time 5 http://fw-test:8080
curl: (28) Connection timed out after 5002 milliseconds
```
The packet was silently discarded. The sender got no reply at all and waited the
full timeout (~5000 ms) before giving up.

## Test 2 - REJECT
```
iptables -D INPUT -p tcp --dport 8080 -j DROP     # remove the DROP rule
iptables -A INPUT -p tcp --dport 8080 -j REJECT
```
From the client:
```
$ curl --max-time 5 http://fw-test:8080
curl: (7) Could not connect ... after 1 ms
```
An error was sent back immediately, so the sender knew it was refused after only
~1 ms.

## The difference

| | DROP | REJECT |
|---|---|---|
| Behavior | silently discards the packet | sends back an error reply |
| Sender experience | waits until timeout | fails immediately |
| Time I measured | ~5000 ms (timeout) | ~1 ms |
| Security | better - gives an attacker no info | weaker - reveals something is there |

## Key takeaway
Both block traffic, but DROP stays silent so the sender just times out, while
REJECT replies with an error so the sender fails instantly. DROP is usually
better for security: it gives an attacker no information - they can't tell if
there's a closed port or nothing at all. REJECT is friendlier for legitimate
users, since they find out immediately instead of waiting.
