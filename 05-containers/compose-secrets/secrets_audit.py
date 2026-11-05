import os
import re
import sys

DANGEROUS_PATTERNS = [
    (r'password\s*=\s*["\']?\w+["\']?', "plain-text password assignment"),
    (r'secret\s*=\s*["\']?\w+["\']?',   "plain-text secret assignment"),
    (r'ghp_[A-Za-z0-9]{36}',             "GitHub Personal Access Token"),
    (r'AKIA[0-9A-Z]{16}',                "AWS Access Key ID"),
]

SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules"}
SKIP_FILES = {".env.example", "secrets_audit.py", "README.md"}


def audit(root="."):
    issues = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if fname in SKIP_FILES:
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, errors="ignore") as f:
                    for lineno, line in enumerate(f, 1):
                        for pattern, label in DANGEROUS_PATTERNS:
                            if re.search(pattern, line, re.IGNORECASE):
                                issues.append((fpath, lineno, label, line.strip()))
            except (PermissionError, IsADirectoryError):
                pass
    return issues


if __name__ == "__main__":
    issues = audit()
    if not issues:
        print("OK: no obvious secrets found.")
    else:
        print(f"FOUND: {len(issues)} potential issue(s):\n")
        for path, line, label, content in issues:
            print(f"  {path}:{line} [{label}]")
            print(f"    {content}\n")
        sys.exit(1)