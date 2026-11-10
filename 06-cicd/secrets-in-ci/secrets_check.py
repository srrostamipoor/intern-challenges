#!/usr/bin/env python3
"""
Pre-flight check: run before CI steps to catch hardcoded secrets.
Exit 1 if anything suspicious is found.
"""
import os
import re
import sys

PATTERNS = [
    (r'password\s*=\s*["\'][^${\s][^"\']{4,}["\']', "plain-text password"),
    (r'token\s*=\s*["\'][^${\s][^"\']{4,}["\']', "plain-text token"),
    (r'secret\s*=\s*["\'][^${\s][^"\']{4,}["\']', "plain-text secret"),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub PAT"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID"),
    (r'sk-[A-Za-z0-9]{32,}', "OpenAI API key"),
]

SKIP = {".git", ".venv", "__pycache__", "node_modules", "secrets_check.py"}


def scan(root="."):
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for fname in filenames:
            if fname in SKIP:
                continue
            path = os.path.join(dirpath, fname)
            try:
                with open(path, errors="ignore") as f:
                    for n, line in enumerate(f, 1):
                        for pattern, label in PATTERNS:
                            if re.search(pattern, line, re.IGNORECASE):
                                found.append((path, n, label, line.rstrip()))
            except (OSError, IsADirectoryError):
                pass
    return found


if __name__ == "__main__":
    issues = scan()
    if not issues:
        print("OK: no hardcoded secrets detected.")
        sys.exit(0)
    print(f"FOUND: {len(issues)} potential secret(s):\n")
    for path, lineno, label, content in issues:
        print(f"  {path}:{lineno}  [{label}]")
        print(f"  -> {content[:120]}\n")
    sys.exit(1)
    