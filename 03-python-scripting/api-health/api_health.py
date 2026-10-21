import os
import sys
import json
import argparse
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

ISSUE_THRESHOLD = 50
RATE_LIMIT_THRESHOLD = 10


def get_json(url):
    """Make a GET request and return the parsed JSON, or raise on error."""
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json()


def check_repo(owner, repo, offline=False):
    if offline:
        with open("sample_response.json") as f:
            data = json.load(f)
    else:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        data = get_json(url)

    name = data.get("full_name", "unknown")
    stars = data.get("stargazers_count", 0)
    issues = data.get("open_issues_count", 0)
    pushed = data.get("pushed_at", "unknown")

    print(f"  Repo: {name} - {stars} stars, {issues} open issues")
    print(f"  Last push: {pushed}")
    if issues > ISSUE_THRESHOLD:
        print(f"  ALERT: open issues ({issues}) exceeds threshold ({ISSUE_THRESHOLD})")


def check_workflow(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=1"
    data = get_json(url)

    runs = data.get("workflow_runs", [])
    if not runs:
        print("  No workflow runs found.")
        return

    run = runs[0]
    name = run.get("name", "unknown")
    status = run.get("status", "unknown")
    conclusion = run.get("conclusion", "unknown")
    created = run.get("created_at", "unknown")

    print(f"  Last workflow: {name} - {status} ({conclusion}) at {created}")
    if conclusion in ("failure", "timed_out"):
        print(f"  ALERT: last workflow run did not succeed ({conclusion})")


def check_rate_limit():
    url = "https://api.github.com/rate_limit"
    data = get_json(url)

    rate = data.get("rate", {})
    remaining = rate.get("remaining", 0)
    limit = rate.get("limit", 0)
    reset = rate.get("reset", 0)
    reset_time = datetime.fromtimestamp(reset).strftime("%Y-%m-%d %H:%M:%S")

    print(f"  Rate limit: {remaining}/{limit} remaining (resets at {reset_time})")
    if remaining < RATE_LIMIT_THRESHOLD:
        print(f"  ALERT: only {remaining} requests left")


def main():
    parser = argparse.ArgumentParser(description="GitHub API health checker")
    parser.add_argument("--owner", default="torvalds", help="Repo owner")
    parser.add_argument("--repo", default="linux", help="Repo name")
    parser.add_argument("--offline", action="store_true", help="Read from sample_response.json instead of the network")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Checking github.com/{args.owner}/{args.repo}")

    try:
        check_repo(args.owner, args.repo, offline=args.offline)
        if not args.offline:
            check_workflow(args.owner, args.repo)
            check_rate_limit()
    except requests.exceptions.ConnectionError:
        print("Error: no internet connection.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        if code == 401:
            print("Error: 401 - check your GITHUB_TOKEN.")
        elif code == 404:
            print(f"Error: 404 - repo not found: {args.owner}/{args.repo}")
        elif code == 403:
            print("Error: 403 - rate limited. Try again later.")
        else:
            print(f"Error: HTTP {code}")
        sys.exit(1)


if __name__ == "__main__":
    main()
