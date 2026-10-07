# Challenge 12 — Nginx Log Parser

## Scenario

> *"Production had a spike in 5xx errors overnight. Nobody knows which endpoint was hit or which IP was hammering us.
> Your job: write a Python script that parses the Nginx access log and produces a quick summary report."*

Log parsing is a bread-and-butter DevOps skill. You'll practice file I/O, regex, `collections`,
dicts, and writing clean, reusable functions.

---

## What you will build

A script `parse_logs.py` that reads an Nginx `access.log` file and prints (or writes to a file):

1. **Total requests** in the file
2. **Status code breakdown** — count per code (200, 404, 500, …)
3. **Top 10 IPs** by request count
4. **Top 10 most-requested URLs**
5. **All 5xx errors** — timestamp, IP, URL, status code

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
# No external packages needed for the core task (stdlib only)
# Stretch: pip install rich   ← for pretty terminal tables
```

---

## The log format

Standard Nginx combined log format:

```
127.0.0.1 - frank [10/Oct/2023:13:55:36 -0700] "GET /api/users HTTP/1.1" 200 2326 "-" "Mozilla/5.0"
10.0.0.5  - -     [10/Oct/2023:13:55:40 -0700] "POST /api/login HTTP/1.1" 401 512  "-" "curl/7.68.0"
10.0.0.5  - -     [10/Oct/2023:13:55:41 -0700] "GET /api/secret HTTP/1.1" 500 0    "-" "curl/7.68.0"
```

Regex pattern to parse one line:

```python
import re

LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<url>\S+) \S+" '
    r'(?P<status>\d{3}) (?P<size>\S+)'
)
```

---

## Deliverables

```
log-parser/
├── parse_logs.py       # the script
├── sample.log          # a sample Nginx log file you generate (see below)
├── report.txt          # the output your script produces against sample.log
└── README.md           # this file + your write-up
```

---

## Functional requirements

### 1. Data structures to use

| What you're counting | Best Python type | Why |
|---|---|---|
| Status codes → count | `dict` or `collections.Counter` | O(1) lookup |
| IP → count | `collections.Counter` | built-in `most_common()` |
| URL → count | `collections.Counter` | same |
| All 5xx entries | `list` of dicts | ordered, iterable |

### 2. Functions to write

```python
def parse_line(line: str) -> dict | None:
    """Parse one log line. Return None if it doesn't match."""
    ...

def parse_file(path: str) -> list[dict]:
    """Read the file, parse every line, return list of parsed entries."""
    ...

def summarize(entries: list[dict]) -> None:
    """Print the full report to stdout."""
    ...
```

### 3. CLI

```bash
python parse_logs.py --log sample.log
python parse_logs.py --log sample.log --output report.txt
python parse_logs.py --log sample.log --errors-only   # only print 5xx lines
```

---

## Generate a realistic sample log

Run this Python snippet to create `sample.log` with 500 entries:

```python
import random, datetime

URLS   = ["/api/users", "/api/login", "/health", "/api/orders", "/api/secret", "/static/app.js"]
IPS    = ["10.0.0.1", "10.0.0.2", "192.168.1.10", "203.0.113.5", "198.51.100.9"]
STATUS = [200]*70 + [201]*10 + [301]*5 + [400]*5 + [401]*3 + [404]*4 + [500]*2 + [503]*1

with open("sample.log", "w") as f:
    for i in range(500):
        dt  = datetime.datetime(2024, 3, 1, 0, 0, 0) + datetime.timedelta(seconds=i*10)
        ts  = dt.strftime("%d/%b/%Y:%H:%M:%S +0000")
        ip  = random.choice(IPS)
        url = random.choice(URLS)
        st  = random.choice(STATUS)
        sz  = random.randint(100, 5000)
        f.write(f'{ip} - - [{ts}] "GET {url} HTTP/1.1" {st} {sz} "-" "curl/7.68.0"\n')

print("sample.log created")
```

---

## Guided questions

1. What is `collections.Counter` and why is it better than a plain `dict` for counting things?
2. What happens to your script if a log line is malformed (e.g. missing the status code)? How did you handle it?
3. Why use `pathlib.Path` instead of open the file directly with a string path?
4. If the log file were 10 GB, would your current approach work? What would you change?

---

## Write-up

**What I built:**

**What I struggled with:**

**What I'd do differently:**
