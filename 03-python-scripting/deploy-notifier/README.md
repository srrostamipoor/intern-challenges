# Challenge 14 — Deploy Notifier

## Scenario

> *"Our deployment script is a Bash one-liner that someone wrote 3 years ago.
> We need a Python wrapper that runs it, captures stdout/stderr, times how long it takes,
> and sends a Slack (or Discord) webhook message with the result — success or failure."*

This challenge is about `subprocess` — the bridge between Python and the shell.
It's essential for any DevOps tooling that wraps existing scripts.

---

## What you will build

`deploy_notifier.py` — a Python script that:

1. Runs an arbitrary shell command as a **subprocess**
2. Captures stdout and stderr separately
3. Measures the wall-clock duration
4. Sends a webhook notification (Slack or Discord) with the result
5. Exits with the same return code as the subprocess (important for CI!)

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests python-dotenv
pip freeze > requirements.txt
```

`.env`:
```
WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
# OR for Discord:
# WEBHOOK_URL=https://discord.com/api/webhooks/XXX/YYY
```

---

## Deliverables

```
deploy-notifier/
├── deploy_notifier.py
├── fake_deploy.sh          # a fake "deploy script" to test against
├── .env.example
├── requirements.txt
└── README.md
```

---

## Functional requirements

### 1. CLI

```bash
# Wrap any command
python deploy_notifier.py --cmd "bash fake_deploy.sh" --env production
python deploy_notifier.py --cmd "echo hello world"
python deploy_notifier.py --cmd "ls /nonexistent"   # should notify on failure
```

### 2. Running the subprocess

Use `subprocess.run()` — **not** `os.system()`.

```python
import subprocess, time

start = time.monotonic()
result = subprocess.run(
    cmd,
    shell=True,
    capture_output=True,
    text=True,
)
duration = time.monotonic() - start
```

| Attribute | What it contains |
|---|---|
| `result.returncode` | 0 = success, anything else = failure |
| `result.stdout` | Everything the command printed to stdout |
| `result.stderr` | Everything printed to stderr |

### 3. Build the notification payload

Create a function `build_payload(cmd, env, returncode, stdout, stderr, duration)` that returns a dict:

```python
# Slack format
{
    "text": "🚀 Deploy to *production* finished",
    "attachments": [
        {
            "color": "#36a64f" if success else "#ff0000",
            "fields": [
                {"title": "Status",   "value": "✅ Success" or "❌ Failed (exit 1)", "short": True},
                {"title": "Duration", "value": "12.3s", "short": True},
                {"title": "Command",  "value": "`bash fake_deploy.sh`", "short": False},
                {"title": "Output",   "value": stdout[-500:] or "(empty)", "short": False},
            ]
        }
    ]
}
```

### 4. Send the webhook

```python
import requests

def send_webhook(url: str, payload: dict) -> None:
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
```

### 5. Exit with the same code as the subprocess

```python
import sys
sys.exit(result.returncode)
```

This is critical — CI systems (GitHub Actions, GitLab CI) check the exit code of every step.
If you swallow the failure, the pipeline thinks the deploy succeeded.

---

## The fake deploy script

Create `fake_deploy.sh` to simulate a real deployment:

```bash
#!/bin/bash
set -e

ENV=${1:-staging}
echo "[$(date)] Starting deploy to $ENV..."
sleep 2
echo "[$(date)] Pulling latest Docker image..."
sleep 1
echo "[$(date)] Running migrations..."

# Simulate a 30% chance of failure
if [ $((RANDOM % 10)) -lt 3 ]; then
    echo "ERROR: Migration failed — connection refused" >&2
    exit 1
fi

echo "[$(date)] Restarting service..."
sleep 1
echo "[$(date)] Deploy complete. Version: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
```

---

## Guided questions

1. What is the difference between `subprocess.run()`, `subprocess.call()`, and `subprocess.Popen()`? When would you use each?
2. Why is `shell=True` convenient but also potentially dangerous? What would be the safer alternative for a fixed command?
3. What does `capture_output=True` do? What happens to stdout/stderr without it?
4. Why does the script re-exit with `sys.exit(result.returncode)`? What goes wrong if you always exit 0?
5. What is `time.monotonic()` and why is it preferred over `time.time()` for measuring durations?

---

## Stretch goals

- Add `--timeout 60` that kills the subprocess if it runs longer than N seconds (use `subprocess.run(timeout=...)`and catch `subprocess.TimeoutExpired`)
- Log every run to a `deploy_history.jsonl` file (one JSON object per line) for auditing
- Support Discord webhooks as well as Slack (they have different payload formats — detect by URL)
- Read the webhook URL from AWS Secrets Manager or HashiCorp Vault instead of a `.env` file

---
## Write-up

**What I built:**
A Python script that runs any shell command as a subprocess, captures its stdout, stderr, and how long it took, and sends the result as a webhook message (Slack/Discord style). It exits with the same exit code as the command, so a CI pipeline can tell whether the command succeeded. If no webhook URL is set, it just prints the message, so it can be tested without a real webhook.

**What I struggled with:**
Understanding why the exit code matters so much was new to me — at first I didn't see why re-exiting with the command's code was important. Once I saw that CI systems read the exit code to decide pass or fail, it made sense. Separating stdout from stderr with capture_output was also new.

**What I'd do differently:**
I'd add a --timeout option that kills the command if it runs too long, and log every run to a file for history. I'd also support both Slack and Discord payload formats by detecting the webhook URL.

---

## Guided questions — answers

**Q1 — run() vs call() vs Popen():** subprocess.run() is the modern, simple way — it runs a command, waits for it to finish, and gives back the result (output, exit code). subprocess.call() is older and only returns the exit code, not the output. subprocess.Popen() is the low-level tool that gives full control (you can stream output, run things in the background) but it's more complex. I used run() because it's the simplest for this task.

**Q2 — shell=True convenience vs danger:** shell=True lets me pass the whole command as one string, which is convenient. But it's dangerous because the shell interprets the string — if any part comes from untrusted input, someone could inject extra commands (command injection). For a fixed, trusted command it's fine; for user input, passing a list of arguments without shell=True is safer.

**Q3 — capture_output=True:** It captures the command's stdout and stderr into the result object instead of letting them print straight to the terminal. Without it, the output would just go to the screen and I couldn't store it, measure it, or put it in the webhook message.

**Q4 — sys.exit(result.returncode):** It makes my script exit with the same exit code as the command it ran. This is critical for CI/CD: pipelines check the exit code of each step to decide if it passed or failed. If I always exited 0, the pipeline would think the deploy succeeded even when it actually failed.

**Q5 — time.monotonic() vs time.time():** time.monotonic() is a clock that only ever moves forward, so it's reliable for measuring how long something took. time.time() is the real-world clock, which can jump backward or forward (for example if the system clock is adjusted), which would give a wrong duration. That's why monotonic is preferred for measuring elapsed time.