"""Validation script: runs type checking, linting, formatting, and tests.

Originally written by Claude Sonnet 4.6 on 2026/03/01
"""

import subprocess
import sys

STEPS = [
    ("Type Checking", ["uv", "run", "--dev", "pyright"]),
    ("Linting", ["uv", "run", "--dev", "ruff", "check"]),
    ("Formatting", ["uv", "run", "--dev", "ruff", "format"]),
    (
        "Import Sorting",
        ["uv", "run", "--dev", "ruff", "check", "--select", "I", "--fix"],
    ),
    (
        "Tests",
        [
            "uv",
            "run",
            "--dev",
            "pytest",
            "-v",
            "--tb=short",
            "-W",
            "error::UserWarning",
        ],
    ),
]


def main() -> None:
    for name, cmd in STEPS:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            cmd_str = " ".join(cmd)
            print(f"## {name} failed\n\n`{cmd_str}`\n")
            if result.stdout:
                print(f"### stdout\n\n```\n{result.stdout.rstrip()}\n```\n")
            if result.stderr:
                print(f"### stderr\n\n```\n{result.stderr.rstrip()}\n```\n")
            sys.exit(result.returncode)
    print("OK")


if __name__ == "__main__":
    main()
