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

*(Fill this in after completing the challenge.)*

**What I built:**

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — where secrets are mounted:**

**Q2 — POSTGRES_PASSWORD_FILE:**

**Q3 — docker inspect env var risk:**

**Q4 — secrets in production (K8s/Swarm):**

**Q5 — read_secret() env var fallback:**
