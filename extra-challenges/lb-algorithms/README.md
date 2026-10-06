# Load Balancing Algorithms — nginx configs

This folder contains nginx configurations for the main load balancing
algorithms. Each `.conf` file shows how to set up that algorithm in an
`upstream` block.

## The algorithms

### Round Robin (`lb-round-robin.conf`)
Requests are distributed to the backends in turn (1 → 2 → 3 → 1 → ...).
This is nginx's default — no special directive is needed. Best when the
servers are roughly equal.

### Weighted Round Robin (`lb-weighted.conf`)
Like round robin, but each server has a `weight`. Servers with a higher
weight receive more traffic (e.g. `weight=3` gets three times the requests
of `weight=1`). Best when some servers are more powerful than others.

### Least Connections (`lb-least-conn.conf`)
Enabled with `least_conn;`. Each new request goes to the backend with the
fewest active connections. Best when requests take different amounts of
time, so load is balanced by real usage rather than just turn order.

### IP Hash (`lb-ip-hash.conf`)
Enabled with `ip_hash;`. A given client IP is always sent to the same
backend. Best for session persistence — when a user's session is stored
on one specific server.

## Static vs dynamic
- **Static** (round robin, weighted, IP hash) — the decision doesn't depend
  on the servers' current state.
- **Dynamic** (least connections) — the decision is based on the servers'
  real-time load.

## Key point
The algorithm is chosen with a single line in the `upstream` block:
- Round robin → nothing (default)
- Weighted → `weight=N` next to each server
- Least connections → `least_conn;`
- IP hash → `ip_hash;`

## Files
- `lb-round-robin.conf`
- `lb-weighted.conf`
- `lb-least-conn.conf`
- `lb-ip-hash.conf`
