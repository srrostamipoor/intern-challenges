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

**What I built:**
A small Flask app with two endpoints (`/` and `/health`) packaged into a Docker image (`hello-app:1.0`) using a hand-written Dockerfile and a `.dockerignore`. I built the image, ran it with `-p 8080:8080`, tested both endpoints, and overrode `APP_ENV` at runtime with `-e`. I also generated `requirements.txt` with `pip freeze` from a clean virtual environment so the dependency versions are pinned.

**What I struggled with:**
At first I did not understand how the Dockerfile paths relate to my own files: `WORKDIR /app` and `COPY` work inside the image, not on my Windows machine. I also ran into a PowerShell execution policy error when activating the virtual environment, and I had created an empty `app.py` by mistake (0 bytes) before noticing it with `dir`. It also took me a while to understand why Docker does not need a virtual environment: the image is already an isolated environment.

**What I'd do differently:**
I would pin the base image version more strictly, run the app as a non-root user, and use a production server such as gunicorn instead of the Flask development server (Flask printed a warning about it). I would also use a multi-stage build to reduce the image size further.

**Numbers from my runs:**
- Image size: 211 MB on disk (51.4 MB compressed content)
- First build: about 69 s to pull the base image and 11 s for `pip install`
- Rebuild with no changes: about 4 s, every layer shown as `CACHED`
- `.dockerignore`: image size did not change, because the Dockerfile copies only `app.py`; the build context did get smaller (543 B to 417 B)

---

## Guided questions — answers

**Q1 — CMD vs ENTRYPOINT:**
`CMD` sets the default command that runs when the container starts, and it can be replaced by passing another command to `docker run`. `ENTRYPOINT` sets the main executable that always runs, and anything passed to `docker run` becomes its arguments. I use `CMD` for a normal app like this one, and `ENTRYPOINT` when the container should behave like a fixed tool, for example always running one CLI program.

**Q2 — requirements.txt first:**
Docker caches each layer. Dependencies change rarely while my code changes often, so I copy `requirements.txt` and run `pip install` first. When only `app.py` changes, Docker reuses the cached install layer and rebuilds only the last steps. In my rebuild the `pip install` layer showed `CACHED` instead of taking 11 seconds again.

**Q3 — slim vs full image:**
`slim` is a smaller variant of the Python image. It leaves out extra system packages and build tools that most apps do not need, so the image is smaller, downloads faster, and has a smaller attack surface. The trade-off is that if a package needs to be compiled, I may have to install build tools myself.

**Q4 — EXPOSE:**
`EXPOSE 8080` is only documentation. It tells people which port the app listens on, but it does not open the port on the host machine. The port is actually published with `-p 8080:8080` in `docker run`.

**Q5 — runtime ENV vs baked-in:**
With `-e APP_ENV=staging` the same image can run in different environments (dev, staging, production) without being rebuilt. I tested this by running the same `hello-app:1.0` image with and without `-e`, and the `env` value in the response changed.