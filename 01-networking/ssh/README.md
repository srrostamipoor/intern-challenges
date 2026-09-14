# Challenge 5 - SSH

## What I did
I ran a container with an SSH server, set up key-based SSH auth into it from my
host machine, disabled password auth entirely, added a `~/.ssh/config` alias so
`ssh myserver` works, then ran a second container with a web app on port 8080
and used SSH local port forwarding to reach that web app from localhost on my
own machine.

## Setup
- `ssh-box`: an Ubuntu container running an OpenSSH server, on my custom network
  `intern-net`, with port 22 mapped to host port 2222 (`-p 2222:22`).
- `web-app`: a Python container running a small web app on port 8080 (returns
  `Response from SERVER web`).
- I connect from the Windows host (PowerShell).

## Part 1 - Key-based SSH auth
1. Installed `openssh-server` in the container.
2. Created a normal user `sara`.
3. Generated a key pair on my host with `ssh-keygen -t ed25519`.
4. Copied the public key into `/home/sara/.ssh/authorized_keys` on the container.
5. Fixed ownership and permissions (`chown sara:sara`, `chmod 700` on the dir,
   `chmod 600` on authorized_keys) - SSH refuses to use keys with loose
   permissions.
6. Connected successfully with the private key from the host:
   `ssh -i <key> -p 2222 sara@localhost`

## Part 2 - Disabling password auth
In `/etc/ssh/sshd_config` I set `PasswordAuthentication no`, then restarted sshd.
After that, password login is rejected (`Permission denied (publickey)`) and only
key-based login works.

## Part 3 - ~/.ssh/config alias
I added this entry to `~/.ssh/config` so I can type `ssh myserver` instead of the
full command (sensitive path kept generic):
```
Host myserver
    HostName localhost
    Port 2222
    User sara
    IdentityFile <path-to-private-key>
```

## Part 4 - Local port forwarding
The web app runs inside the Docker network and isn't reachable directly from the
Windows host. I created an SSH tunnel through `ssh-box` to reach it:

Command used:
```
ssh -L 9000:web-app:8080 myserver -N
```
- `-L 9000:web-app:8080` - forward local port 9000 to `web-app:8080` through the
  SSH connection.
- `-N` - just create the tunnel, don't open a shell.

Then, from the host, hitting `http://localhost:9000` reached the web app:
```
StatusCode: 200
Content: Response from SERVER web
Server: BaseHTTP/0.6 Python/3.12.14
```
Before the tunnel, `curl http://web-app:8080` from the host failed
("could not be resolved") because the host is not on the Docker network. With the
tunnel, `localhost:9000` reaches it - proof that port forwarding works.

## Notes
- The tunnel stays up only while the SSH session (that PowerShell window) is open.
  Closing it or pressing Ctrl+C ends the tunnel.
- For this exercise the key has no passphrase, to keep the tunnel automatic. In a
  real setup the private key would have a passphrase for extra security.
- Two ports with different roles: 2222 is for connecting to SSH itself; 9000 is
  the local end of the tunnel that reaches the web app.

## Files
- `ssh_config_entry.txt` - the ~/.ssh/config alias (sensitive path redacted).
- `port_forwarding_command.txt` - the tunnel command used.
- `forwarding_output.txt` - the log showing localhost:9000 reaching the web app.
