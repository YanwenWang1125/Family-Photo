"""
Run structural and naming consistency checks.
"""
import os
import sys
import re

ALLOWED_TOP_FOLDERS = {"app", "tests", "scripts", "docs"}
SNAKE_CASE_PATTERN = r"^[a-z0-9_]+\.py$"

def check_structure():
    errors = []
    for root, _, files in os.walk("app"):
        for f in files:
            if f.endswith(".py") and not re.match(SNAKE_CASE_PATTERN, f):
                errors.append(f"Invalid filename: {root}/{f}")
    return errors

if __name__ == "__main__":
    errs = check_structure()
    if errs:
        print("\n".join(errs))
        sys.exit(1)
    print("Consistency OK ✔")