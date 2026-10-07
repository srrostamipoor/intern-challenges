# Challenge 13 — API Health Checker

## Scenario

> *"We integrate with the GitHub API (or any REST API) to check the status of our CI pipelines.
> Write a script that authenticates with a token, polls the API, and warns us if something looks wrong."*

This is where you practice the full API interaction loop: auth headers, JSON parsing,
nested dict navigation, and reacting to the response data — not just the status code.

---

## What you will build

`api_health.py` — a script that:

1. Calls the **GitHub API** (free, no account needed for public repos)
2. Parses the JSON response
3. Extracts specific fields (repo stats, workflow run status, rate limit, …)
4. Alerts if any value crosses a threshold

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests python-dotenv
pip freeze > requirements.txt
```

Create a `.env` file (add it to `.gitignore`!):

```
GITHUB_TOKEN=ghp_your_personal_access_token_here
```

---

## Deliverables

```
api-health/
├── api_health.py
├── .env.example        # template — shows keys but no values
├── requirements.txt
├── sample_response.json  # a saved API response for offline testing
└── README.md
```

---

## Functional requirements

### 1. Authentication

```python
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN", "")   # empty string = unauthenticated (60 req/hr)
HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
```

### 2. The three checks to implement

#### Check A — Repo metadata

```
GET https://api.github.com/repos/{owner}/{repo}
```

Extract and print:
- `full_name`
- `stargazers_count`
- `open_issues_count`
- `pushed_at` (last push time)

Alert if `open_issues_count` > a configurable threshold.

#### Check B — Latest workflow run

```
GET https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=1
```

Extract from `workflow_runs[0]`:
- `name`, `status`, `conclusion`, `created_at`

Alert if `conclusion` is `"failure"` or `"timed_out"`.

#### Check C — Rate limit

```
GET https://api.github.com/rate_limit
```

Extract `rate.remaining` and `rate.reset` (Unix timestamp).
Alert if `remaining` < 10.

### 3. Output format

```
[2024-03-01 14:22:01] Checking github.com/torvalds/linux
  ✓ Repo: torvalds/linux — 180k stars, 432 open issues
  ✗ ALERT: open_issues_count (432) exceeds threshold (50)
  ✓ Last workflow run: CI — completed (success) at 2024-03-01T12:00:00Z
  ✓ Rate limit: 58/60 remaining (resets at 2024-03-01T15:00:00Z)
```

### 4. Offline / test mode

Save a real API response to `sample_response.json`:

```python
import json, requests

r = requests.get("https://api.github.com/repos/torvalds/linux")
with open("sample_response.json", "w") as f:
    json.dump(r.json(), f, indent=2)
```

Add a `--offline` flag that reads from this file instead of hitting the network.
This lets you work on parsing logic without burning API quota.

### 5. Error handling you must cover

| Scenario | How to handle |
|---|---|
| No internet | Catch `ConnectionError`, print friendly message |
| `401 Unauthorized` | Print "Check your GITHUB_TOKEN" |
| `404 Not Found` | Print "Repo not found: {owner}/{repo}" |
| `403 + X-RateLimit-Remaining: 0` | Print "Rate limited. Retry after {reset_time}" |
| Malformed JSON key | Use `.get()` with a default, never assume a key exists |

---

## Guided questions

1. What is the difference between `response.json()` and `json.loads(response.text)`?
2. Why should you use `response.raise_for_status()` and what does it do?
3. What is a Bearer token and how does it differ from Basic Auth?
4. What does `os.getenv("KEY", "")` do differently from `os.environ["KEY"]`?
5. You saved the API response to a JSON file. Why is this useful for testing? How does it compare to mocking?

---

## Stretch goals

- Add `--watch` mode: poll every 60 seconds and show a diff from the previous check
- Write a `test_parser.py` using only `unittest` — load `sample_response.json` and assert your extraction functions return correct values
- Support multiple repos from a `repos.txt` file, one per line

---

## Write-up

**What I built:**

**What I struggled with:**

**What I'd do differently:**
