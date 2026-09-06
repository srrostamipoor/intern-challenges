# Challenge 1 — TCP vs UDP

## What I did
I created a custom Docker network and put two containers on it, then made
them talk to each other — first with TCP, then with UDP. After that I broke
the server on purpose to see how TCP and UDP react differently.

## My setup
- I made a custom network called `intern-net` so the containers could find
  each other by name instead of by IP address.
- I ran two containers on it: `tcp-server` and `tcp-client`, both from the
  `python:3.12` image.

## Files
- `server/` — my TCP and UDP servers (a simple version and a looping version)
- `client/` — my TCP and UDP clients, plus `udp_fire.py`, which only sends
  and does not wait for a reply

## The main difference in the code
For TCP I used `SOCK_STREAM`, with `listen()` and `accept()` on the server
and `connect()` on the client — so a real connection is set up first. For UDP
I used `SOCK_DGRAM` with `sendto()` and `recvfrom()`, and there is no
connection at all — the client just throws the message at the address.

## What I tested and what happened

**1. Normal exchange.** Both TCP and UDP sent a message and got a reply back.
Since I used a custom network, the client reached the server by its name
(`tcp-server`) instead of an IP.

**2. Server not running, client waits for a reply.** With TCP I got an
immediate error, `Connection refused`, because TCP first tries to open a
connection and instantly sees there is nothing there. With UDP, the client
sent the message and then sat on `recvfrom()` waiting for a reply that never
came — so it just hung.

**3. Server not running, client does NOT wait (udp_fire.py).** This was the
interesting one. The client only called `sendto()` and then finished
normally, printing its success message — even though no server existed at
all. It behaved as if everything was fine, but the message was actually lost
and the client never knew.

**4. Server killed mid-transfer.** I ran a looping client that sent a message
every 2 seconds. With TCP, after a few successful messages, killing the
server immediately gave me a `Broken pipe` error — TCP noticed the connection
dropped right away. With UDP, the client just hung on `recvfrom()` forever,
completely unaware that the server had died.

## What I learned (the why)
TCP keeps a live connection open, so it always knows when something goes
wrong — whether the server was never there or died halfway through, it tells
me with a clear error. UDP keeps no connection, so it just sends and hopes:
if the client waits for a reply it hangs forever, and if it does not wait it
carries on as if nothing happened, even when the message went nowhere.
