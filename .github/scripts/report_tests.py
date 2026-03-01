"""Parse JUnit XML test results and emit GitHub Actions annotations.

Reads one or more JUnit XML files, prints ::error annotations for each
failed/errored test case, and exits with code 1 if any failures were found.

Originally written by Claude Sonnet 4.6 on 2026/03/01
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _report_file(path: Path) -> int:
    """Emit annotations for all failures in a JUnit XML file.

    @param path: Path to a JUnit XML file.
    @return: Number of failed/errored test cases.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    # Both <testsuites><testsuite> and bare <testsuite> are valid roots.
    suites = root.findall("testsuite") if root.tag == "testsuites" else [root]

    failures = 0
    for suite in suites:
        for case in suite.findall("testcase"):
            classname = case.get("classname", "")
            name = case.get("name", "")
            title = f"{classname}.{name}" if classname else name

            for outcome in ("failure", "error"):
                node = case.find(outcome)
                if node is None:
                    continue
                failures += 1
                message = (node.get("message") or node.text or outcome).splitlines()[0]
                # file= and line= are not in JUnit XML; omit them so GitHub
                # still shows the annotation in the job summary.
                print(f"::error title={title}::{message}")

    return failures


def main() -> None:
    if len(sys.argv) < 2:
        raise ValueError("Usage: report_tests.py <junit.xml> [...]")

    total_failures = 0
    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"::warning title=report_tests::No test results found at {path}")
            continue
        total_failures += _report_file(path)

    if total_failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
