import os
import sys
import time
import argparse
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")


def run_command(cmd):
    """Run a shell command, capture output and timing."""
    start = time.monotonic()
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )
    duration = time.monotonic() - start
    return result, duration


def build_message(cmd, env, returncode, stdout, stderr, duration):
    success = returncode == 0
    status = "SUCCESS" if success else f"FAILED (exit {returncode})"
    output = (stdout or stderr or "(no output)")[-500:]
    return (
        f"Deploy to {env} finished\n"
        f"Status: {status}\n"
        f"Duration: {duration:.1f}s\n"
        f"Command: {cmd}\n"
        f"Output:\n{output}"
    )


def send_webhook(message):
    if not WEBHOOK_URL:
        print("No WEBHOOK_URL set - skipping webhook. Message would be:\n")
        print(message)
        return
    try:
        r = requests.post(WEBHOOK_URL, json={"text": message}, timeout=10)
        r.raise_for_status()
        print("Webhook sent.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send webhook: {e}")


def main():
    parser = argparse.ArgumentParser(description="Run a command and notify the result")
    parser.add_argument("--cmd", required=True, help="The shell command to run")
    parser.add_argument("--env", default="staging", help="Environment name")
    args = parser.parse_args()

    print(f"Running: {args.cmd}")
    result, duration = run_command(args.cmd)

    print("--- stdout ---")
    print(result.stdout)
    print("--- stderr ---")
    print(result.stderr)
    print(f"Exit code: {result.returncode} (took {duration:.1f}s)")

    message = build_message(
        args.cmd, args.env, result.returncode,
        result.stdout, result.stderr, duration
    )
    send_webhook(message)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
