# Challenge 2 - DNS Resolution

## What I did
I ran my own DNS server in a Docker container using dnsmasq, configured it to
resolve a fake domain (internship.local) to an internal IP, and confirmed from
a second container that resolution works using dig. I also added CNAME and MX
records and tested them.

## My setup
- I reused the two containers from Challenge 1 (tcp-server and tcp-client)
  since they were already on my custom network intern-net.
- I installed dnsmasq on tcp-server (it acts as the DNS server) and queried it
  from tcp-client.
- The DNS server's IP was 172.18.0.2.

## The config (dnsmasq.conf)
- `address=/internship.local/10.0.0.5` - an **A record** mapping the domain to an IP.
- `address=/mail.internship.local/10.0.0.6` - an A record for the mail server.
- `cname=www.internship.local,internship.local` - a **CNAME record** making
  `www` an alias of the main domain.
- `mx-host=internship.local,mail.internship.local,10` - an **MX record** saying
  mail for the domain goes to mail.internship.local, with priority 10.
- `log-queries` - logs every DNS query, useful for debugging.

## What each record does
- **A record:** maps a name directly to an IPv4 address.
- **CNAME record:** points one name to another name (an alias), not to an IP.
- **MX record:** says which server should receive the domain's email. It points
  to a name, not an IP, so that name needs its own A record (that's why I added
  an A record for mail.internship.local).

## Resolution chain
When a client asks for internship.local, my server answers directly with the A
record (10.0.0.5). For www.internship.local, it returns the CNAME pointing to
internship.local, which then resolves to 10.0.0.5 via the A record. For mail,
the MX record points to mail.internship.local, which has its own A record
resolving to 10.0.0.6. So MX and CNAME never give an IP directly - they point
to a name, and that name is resolved separately. This indirection is
intentional: if an IP changes, only the A record needs updating.

## What I observed
- Every answer came back with the `aa` flag (authoritative answer), because my
  server is the authority for this domain - unlike public lookups (e.g. Google),
  which are non-authoritative and come from cache.
- `dig` shows a warning that `.local` is reserved for Multicast DNS. It still
  works for this test, but in a real setup I'd use a different suffix.
- My dnsmasq returns the CNAME record but does not automatically follow the
  chain to include the final A record in the same response - the client has to
  ask for the target name separately. Fuller resolvers (like BIND or Google's
  public DNS) usually follow the chain and return the final IP too. This is a
  behavior difference worth noting.

## Files
- `dnsmasq.conf` - my DNS server configuration.
