import re
import argparse
from collections import Counter
from pathlib import Path

LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<url>\S+) \S+" '
    r'(?P<status>\d{3}) (?P<size>\S+)'
)


def parse_line(line):
    match = LOG_PATTERN.match(line)
    if match:
        return match.groupdict()
    return None


def parse_file(path):
    log_path = Path(path)
    if not log_path.exists():
        print(f"Error: file not found: {path}")
        return []
    entries = []
    with log_path.open() as f:
        for line in f:
            entry = parse_line(line)
            if entry:
                entries.append(entry)
    return entries

def build_report(entries, errors_only=False):
    lines = []
    errors = [e for e in entries if e["status"].startswith("5")]

    if errors_only:
        lines.append(f"5xx errors ({len(errors)}):")
        for e in errors:
            lines.append(f"  [{e['time']}] {e['ip']} {e['url']} {e['status']}")
        return "\n".join(lines)

    total = len(entries)
    status_counts = Counter(e["status"] for e in entries)
    ip_counts = Counter(e["ip"] for e in entries)
    url_counts = Counter(e["url"] for e in entries)

    lines.append(f"Total requests: {total}\n")

    lines.append("Status code breakdown:")
    for status, count in sorted(status_counts.items()):
        lines.append(f"  {status}: {count}")

    lines.append("\nTop 10 IPs:")
    for ip, count in ip_counts.most_common(10):
        lines.append(f"  {ip}: {count}")

    lines.append("\nTop 10 URLs:")
    for url, count in url_counts.most_common(10):
        lines.append(f"  {url}: {count}")

    lines.append(f"\n5xx errors ({len(errors)}):")
    for e in errors:
        lines.append(f"  [{e['time']}] {e['ip']} {e['url']} {e['status']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Nginx access log parser")
    parser.add_argument("--log", required=True, help="Path to the log file")
    parser.add_argument("--output", help="Write the report to this file instead of stdout")
    parser.add_argument("--errors-only", action="store_true", help="Show only 5xx errors")
    args = parser.parse_args()

    entries = parse_file(args.log)
    if not entries:
        return
    report = build_report(entries, errors_only=args.errors_only)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report + "\n")
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
