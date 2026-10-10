import time
import argparse
from datetime import datetime
import requests
import os

def check_url(url):
    try:
        timeout = int(os.environ.get("TIMEOUT", 5))
        response = requests.get(url, timeout=timeout)
        if 200 <= response.status_code < 300:
            return True, f"OK ({response.status_code})"
        else:
            return False, f"Bad status: {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "Timeout - no response in 5s"
    except requests.exceptions.ConnectionError:
        return False, "Connection error - site unreachable"
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {e}"


def send_alert(url, reason):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] ALERT: {url} is DOWN - {reason}"
    print(message)
    with open("monitor.log", "a") as f:
        f.write(message + "\n")


def main():
    parser = argparse.ArgumentParser(description="Website uptime monitor")
    parser.add_argument("--url", required=True, help="URL to monitor")
    default_interval = int(os.environ.get("CHECK_INTERVAL", 60))
    parser.add_argument("--interval", type=int, default=default_interval, help="Seconds between checks")
    args = parser.parse_args()

    print(f"Monitoring {args.url} every {args.interval}s. Press Ctrl+C to stop.")
    while True:
        is_up, reason = check_url(args.url)
        if is_up:
            print(f"[OK] {args.url} - {reason}")
        else:
            send_alert(args.url, reason)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
