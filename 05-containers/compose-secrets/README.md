# Challenge 24 — Compose Secrets and Config Management

## Scenario

> *"We deployed the stack and the database password is in the `.env` file,
> which got committed to Git by accident. Now we need to handle secrets properly —
> no plain-text passwords in the repo, ever."*

Secrets management is a core DevOps responsibility. This challenge covers the three levels:
`.env` files (basic), Docker secrets (Compose level), and environment-variable best practices.

---

## What you will build

The same Compose stack from Challenge 23, hardened against accidental secret leakage:

1. A `.gitignore` that properly excludes secrets
2. An `.env.example` with every key but no values
3. Docker Compose `secrets:` for database credentials
4. A `secrets_audit.py` script that scans for accidental secret exposure

---

## Deliverables

```
compose-secrets/
├── api/
│   ├── app.py          # reads DB password from /run/secrets/db_password
│   ├── requirements.txt
│   └── Dockerfile
├── secrets/
│   ├── db_password.txt  # local dev only — in .gitignore!
│   └── .gitkeep
├── compose.yaml
├── .env.example
├── .gitignore
├── secrets_audit.py
└── README.md
```

---

## Functional requirements

### 1. What NOT to do (understand the mistake first)

The bad pattern — password in plain text in `compose.yaml`:
```yaml
# BAD — password visible in the file, and in `docker inspect`
environment:
  DB_PASSWORD: mysecretpassword
```

The slightly better pattern — password in `.env`:
```yaml
# BETTER — at least it's not in the YAML itself
environment:
  DB_PASSWORD: ${DB_PASSWORD}
```
But if `.env` is committed to Git, this is still exposed.

### 2. Docker Compose secrets (the right way)

In `compose.yaml`:
```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password

  api:
    build: ./api
    environment:
      DB_HOST: postgres
      DB_NAME: appdb
      DB_USER: appuser
    secrets:
      - db_password
    # api reads the password from /run/secrets/db_password at runtime

secrets:
  db_password:
    file: ./secrets/db_password.txt   # only for local dev
```

### 3. Reading the secret in the API

Modify `api/app.py` to read the password from the secret file instead of an env var:

```python
def read_secret(name):
    """Read a Docker secret from /run/secrets/<name>, fall back to env var."""
    secret_path = f"/run/secrets/{name}"
    if os.path.exists(secret_path):
        with open(secret_path) as f:
            return f.read().strip()
    return os.getenv(name.upper(), "")

DB_PASSWORD = read_secret("db_password")
```

### 4. .gitignore

```gitignore
# Secrets — NEVER commit these
.env
secrets/*.txt
secrets/*.key
secrets/*.pem

# But keep the directory itself
!secrets/.gitkeep
```

### 5. .env.example

```bash
# Copy this to .env and fill in real values
# .env is in .gitignore — never commit it

DB_NAME=appdb
DB_USER=appuser
# DB_PASSWORD is managed via Docker secrets (secrets/db_password.txt)
```

### 6. secrets_audit.py — scan for leaked secrets

Write a script that walks the project directory and warns about risky patterns:

```python
import os, re, sys

DANGEROUS_PATTERNS = [
    (r'password\s*=\s*["\']?\w+["\']?', "plain-text password assignment"),
    (r'secret\s*=\s*["\']?\w+["\']?',   "plain-text secret assignment"),
    (r'ghp_[A-Za-z0-9]{36}',             "GitHub Personal Access Token"),
    (r'AKIA[0-9A-Z]{16}',                "AWS Access Key ID"),
]

SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules"}
SKIP_FILES = {".env.example", "secrets_audit.py", "README.md"}

def audit(root="."):
    issues = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if fname in SKIP_FILES:
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, errors="ignore") as f:
                    for lineno, line in enumerate(f, 1):
                        for pattern, label in DANGEROUS_PATTERNS:
                            if re.search(pattern, line, re.IGNORECASE):
                                issues.append((fpath, lineno, label, line.strip()))
            except (PermissionError, IsADirectoryError):
                pass
    return issues

if __name__ == "__main__":
    issues = audit()
    if not issues:
        print("✓ No obvious secrets found.")
    else:
        print(f"✗ {len(issues)} potential issue(s) found:\n")
        for path, line, label, content in issues:
            print(f"  {path}:{line} [{label}]")
            print(f"    {content}\n")
        sys.exit(1)
```

### 7. Test the full stack

```bash
# Create the secret file (never commit this)
echo "supersecretpassword" > secrets/db_password.txt

# Bring up the stack
docker compose up --build -d

# Verify the API can reach the DB
curl -X POST http://localhost:8080/messages \
  -H "Content-Type: application/json" \
  -d '{"text": "secrets test"}'

# Run the audit
python secrets_audit.py
```

Verify: the password is **not** in `docker inspect` environment output:
```bash
docker inspect compose-secrets-api-1 | grep -i password
# Should return nothing (or only POSTGRES_PASSWORD_FILE)
```

---

## Guided questions

1. Where does Docker mount secrets inside the container? What file permissions does it set, and why?
2. `POSTGRES_PASSWORD_FILE` is a special env var that Postgres supports natively. How does it know to read the file instead of using the variable as the password directly?
3. Why is using `docker inspect` on a container with plain-text env vars a security problem?
4. In production (e.g. Kubernetes or Docker Swarm), how are secrets managed differently from this local file approach?
5. The `read_secret()` function falls back to an env var. Why is this useful for local development outside of Docker?

---

## Stretch goals

- Integrate `secrets_audit.py` as a pre-commit hook using the `pre-commit` framework
- Use `age` (a modern encryption tool) to encrypt `db_password.txt` at rest and decrypt at container start
- Read secrets from HashiCorp Vault (free OSS) instead of a local file — run Vault in a container

---
## Write-up

**What I built:**
The Challenge 23 stack (nginx, Flask API, PostgreSQL, Redis) hardened against
secret leakage. The database password now lives in `secrets/db_password.txt`,
which is git-ignored (`secrets/*.txt`, with `!secrets/.gitkeep` to keep the
folder). Compose mounts it into `postgres` and `api` as a Docker secret at
`/run/secrets/db_password`. Postgres reads it through
`POSTGRES_PASSWORD_FILE`, and the API reads it with `read_secret()`, which
falls back to an environment variable. `.env` now contains only `DB_NAME` and
`DB_USER`, and `.env.example` documents the keys without real values. I also
wrote `secrets_audit.py`, a script that walks the project and reports risky
patterns.

**What I observed:**
- POST and GET through nginx worked, so the password from the file is the same
  on both sides.
- `docker compose exec api ls -l /run/secrets` showed
  `-rwxrwxrwx root root 19 db_password` (19 bytes, no trailing newline).
- `docker inspect` of the api container never contained the password value
  (searching for `supersecret` returned nothing). Searching for the word
  `password` only matched the mount path `db_password.txt`. For postgres it
  showed `POSTGRES_PASSWORD_FILE=/run/secrets/db_password`, which is a path,
  not the secret.
- For comparison, a container started with `-e DB_PASSWORD=supersecretpassword`
  showed `"DB_PASSWORD=supersecretpassword"` in `docker inspect`.
- `secrets_audit.py` reported 2 false positives in `api/app.py`
  (`DB_PASSWORD = read_secret(...)` and `password=DB_PASSWORD,`) because the
  regex matches the word `password` followed by `=` even when the value is a
  variable. It did catch a fake leak (`password = hunter2` in a test file) and
  exited with code 1.

**What I struggled with:**
- The first builds failed with `Temporary failure in name resolution` and a
  `ReadTimeoutError` while pip downloaded `psycopg2-binary` over a weak
  connection. I fixed it with `pip install --default-timeout=120 --retries 10`
  in the Dockerfile.
- On Windows, `echo "..." > file` writes UTF-16, and the default newline
  (`\r\n`) would end up in the password. I created the file with
  `Set-Content -Encoding ascii -NoNewline` and checked that its length is
  exactly 19 bytes.
- Understanding that a secret is still readable by anyone who can run
  `docker exec`; it only keeps the value out of Git, the YAML, `inspect` and
  logs.

**What I'd do differently:**
- Make the audit regex stricter (only flag quoted literal values) or add an
  allow-list to remove the false positives.
- Run `secrets_audit.py` as a pre-commit hook or in the CI pipeline, since it
  exits with code 1 when it finds something.
- Add a Postgres healthcheck and use a real secret store (Vault, cloud secret
  manager) outside local development.

---

## Guided questions — answers

**Q1 — where secrets are mounted:**
Docker mounts each secret as a file at `/run/secrets/<name>`, here
`/run/secrets/db_password`, and only into the services that list it under
`secrets:` (redis and nginx do not get it). In my test (Docker Desktop on
Windows, plain Compose) the file showed `-rwxrwxrwx root root`, because in
standalone Compose a file-based secret is a bind mount of the host file, so the
permissions come from that file rather than from Docker. In Swarm, secrets are
kept in memory (tmpfs) and are read-only for the container (the documented
default mode is 0444). The point of a file is that it does not appear in
`docker inspect`, is not inherited as an environment variable by child
processes, and can be protected with file permissions.

**Q2 — POSTGRES_PASSWORD_FILE:**
It is not the Postgres server that understands `_FILE`; it is the official
image's entrypoint script (`docker-entrypoint.sh`). For variables such as
`POSTGRES_PASSWORD` it has a helper (`file_env`) that checks whether
`POSTGRES_PASSWORD_FILE` is set, reads the file content into
`POSTGRES_PASSWORD`, and refuses to start if both are set. I confirmed the
helper exists with `grep file_env` inside the container.

**Q3 — docker inspect env var risk:**
`docker inspect` prints every environment variable of a container in clear
text, so anyone who can run Docker commands (or read a saved inspect output
or a support bundle) sees the password. I reproduced it: a container started
with `-e DB_PASSWORD=supersecretpassword` showed the value in `inspect`, while
my api container with a secret did not. Plain env vars are also easy to leak
through logs, crash reports and child processes, and if they are written in
`compose.yaml` they end up in Git.

**Q4 — secrets in production (K8s/Swarm):**
In Docker Swarm, secrets are stored encrypted in the cluster's Raft log,
sent only to the nodes that run a service that needs them, and mounted in
memory. In Kubernetes, Secret objects are stored in etcd (only base64-encoded
unless encryption at rest is enabled), access is controlled with RBAC, and
they are mounted as files or env vars in pods. Often an external secret
manager (Vault, a cloud provider's secret manager) is used on top, which adds
access control, auditing and rotation. A password file on a developer's disk,
like mine, has none of these.

**Q5 — read_secret() env var fallback:**
`read_secret("db_password")` first looks for `/run/secrets/db_password`, and
if it does not exist it reads the env var `DB_PASSWORD`. This lets me run
`app.py` outside Docker (on my laptop, in unit tests or in CI) by exporting an
environment variable, without changing code. It should be used only for
development, because env vars are less safe than a mounted secret.