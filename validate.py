"""Workspace validation: validates all projects in parallel.

Each project runs its steps in order and stops at its own first failure.
Reports the first failing step of any project, then exits.

Originally written by Claude Sonnet 4.6 on 2026/03/01
"""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Workspace member directories (relative to this file)
PROJECTS = ["library", "terminal_ui"]

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

ROOT = Path(__file__).parent


def _validate_project(project: str) -> tuple[str, str, subprocess.CompletedProcess[str]] | None:
    """Run steps for a project in order, stopping at the first failure.

    @return: (project, step_name, result) for the first failing step, or None if all pass.
    """
    cwd = ROOT / project
    for step_name, cmd in STEPS:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        if result.returncode != 0:
            return (project, step_name, result)
    return None


def main() -> None:
    with ThreadPoolExecutor(max_workers=len(PROJECTS)) as pool:
        futures = {pool.submit(_validate_project, p): p for p in PROJECTS}
        failures: list[tuple[str, str, subprocess.CompletedProcess[str]]] = []
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                failures.append(result)

    if failures:
        for project, step_name, result in sorted(failures):
            cmd_str = " ".join(next(cmd for name, cmd in STEPS if name == step_name))
            print(f"## {project}: {step_name} failed\n\n`{cmd_str}`\n")
            if result.stdout:
                print(f"```\n{result.stdout.rstrip()}\n```\n")
            if result.stderr:
                print(f"```\n{result.stderr.rstrip()}\n```\n")
        sys.exit(1)

    print("OK")


if __name__ == "__main__":
    main()
