# Challenge 19 — Write Your First Dockerfile

## Scenario

> *"Every service we ship runs in a container. Before you touch Docker Compose or Kubernetes,
> you need to know exactly what a Dockerfile does and why each instruction exists."*

This challenge is about reading and writing Dockerfiles fluently — not copying them blindly.
You'll containerise a small Python app and learn what every line of the Dockerfile means.

---

## What you will build

A containerised Python web app with a hand-written, production-quality `Dockerfile`:

1. A minimal Flask "hello-world" app (`app.py`)
2. A `Dockerfile` that packages it correctly
3. A `.dockerignore` that keeps the image lean

---

## Setup

```bash
pip install flask
```

---

## Deliverables

```
dockerfile-basics/
├── app.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
└── README.md
```

---

## Functional requirements

### 1. The app

`app.py`:

```python
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({"message": "hello from container", "env": os.getenv("APP_ENV", "dev")})

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### 2. The Dockerfile — instructions you must use

| Instruction | Purpose |
|---|---|
| `FROM` | Base image — use `python:3.11-slim` |
| `WORKDIR` | Set the working directory inside the image |
| `COPY` | Copy only what you need (requirements first, then app) |
| `RUN` | Install Python dependencies |
| `ENV` | Set `APP_ENV=production` |
| `EXPOSE` | Document the port |
| `CMD` | Start the app |

Your finished Dockerfile should look roughly like this structure (fill it in yourself):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first so Docker can cache this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the app
COPY . .

ENV APP_ENV=production
EXPOSE 8080

CMD ["python", "app.py"]
```

### 3. Build and run

```bash
# Build
docker build -t hello-app:1.0 .

# Run (map host port 8080 to container port 8080)
docker run -p 8080:8080 hello-app:1.0

# Test
curl http://localhost:8080/
curl http://localhost:8080/health
```

Expected response:
```json
{"env": "production", "message": "hello from container"}
```

### 4. Override the ENV at runtime

```bash
docker run -p 8080:8080 -e APP_ENV=staging hello-app:1.0
```

The response should now show `"env": "staging"`.

### 5. The .dockerignore

Create `.dockerignore` and add at minimum:

```
.venv/
__pycache__/
*.pyc
.env
.git
```

Check image size before and after adding `.dockerignore`.

---

## Guided questions

1. What is the difference between `CMD` and `ENTRYPOINT`? When would you use each?
2. Why do we `COPY requirements.txt .` and `RUN pip install` *before* `COPY . .`? What does this save?
3. Why use `python:3.11-slim` instead of `python:3.11`? What does "slim" mean for an image?
4. What does `EXPOSE 8080` actually do? Does it open the port on the host machine?
5. Why is `-e APP_ENV=staging` at `docker run` time more powerful than baking the value into the image?

---

## Stretch goals

- Add a second `FROM` stage (multi-stage build) that copies only the installed packages and app into a final `python:3.11-slim` image — measure the size difference
- Tag the image with both `hello-app:1.0` and `hello-app:latest` in one build command
- Push the image to Docker Hub (create a free account) and pull it back down

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — CMD vs ENTRYPOINT:**

**Q2 — requirements.txt first:**

**Q3 — slim vs full image:**

**Q4 — EXPOSE:**

**Q5 — runtime ENV vs baked-in:**
