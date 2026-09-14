# Challenge 6 - Firewalls & Ports

## What I did
In a container (started with `--cap-add=NET_ADMIN` so iptables works inside it),
I used iptables to block all incoming traffic except SSH (22) and HTTP (80). I
verified that a test service on port 5000 was unreachable from outside the
container, then explicitly opened that port and confirmed it became reachable.

## Setup
- `firewall-box`: a Python container on my custom network `intern-net`, started
  with `--cap-add=NET_ADMIN` (this capability lets iptables actually apply rules
  inside the container - without it, iptables gets a permission error).
- A test service running on port 5000 (`python3 -m http.server 5000`).
- I tested from another container (`tcp-client`) to check reachability "from
  outside".

## The firewall rules
```
iptables -A INPUT -p tcp --dport 22 -j ACCEPT   # allow SSH
iptables -A INPUT -p tcp --dport 80 -j ACCEPT   # allow HTTP
iptables -A INPUT -i lo -j ACCEPT               # allow internal (localhost) traffic
iptables -A INPUT -j DROP                        # drop everything else
```
- The three ACCEPT rules are exceptions; the final DROP blocks all other
  incoming traffic.
- Order matters: iptables checks rules top to bottom, so the exceptions must
  come before the DROP. If DROP were first, everything would be blocked.
- The `-i lo` rule allows loopback traffic, so processes that talk to themselves
  (localhost) don't break when the DROP rule blocks everything else.

## Before: port 5000 blocked
From `tcp-client`, hitting port 5000 timed out - the firewall blocked it:
```
$ curl --max-time 5 http://firewall-box:5000
curl: (28) Connection timed out after 5002 milliseconds
```
Checking the rules with `iptables -L -n -v` showed the DROP rule's packet
counter increasing, confirming it was dropping the blocked requests.

## Opening port 5000
I inserted an ACCEPT rule for port 5000 - using `-I` (insert at the top) instead
of `-A` (append at the end), so it comes before the DROP rule:
```
iptables -I INPUT -p tcp --dport 5000 -j ACCEPT
```

## After: port 5000 reachable
From `tcp-client`, the same request now succeeded:
```
$ curl --max-time 5 http://firewall-box:5000
<!DOCTYPE HTML>
<html lang="en">
<head><title>Directory listing for /</title></head>
...
```

## What I learned
- `--cap-add=NET_ADMIN` is needed for iptables to work inside a container
  (a plain container can't modify the kernel's firewall).
- iptables rules are checked top to bottom, so rule order is critical - exceptions
  before the catch-all DROP, and `-I` (insert) vs `-A` (append) decides position.
- `iptables -L -n` doesn't show the interface column, but `iptables -L -n -v` does
  (that's how I could see the `lo` rule and the DROP packet counts).

## Files
- `firewall_rules.txt` - the iptables rules used.
- `before_after_output.txt` - the curl output showing the port going from blocked
  to open.
