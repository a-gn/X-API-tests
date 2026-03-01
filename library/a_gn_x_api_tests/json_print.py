"""Colorized JSON printing, similar to jq output."""

import json
import sys
from typing import TextIO

from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import JsonLexer


def print_json(obj: object, *, file: TextIO = sys.stdout) -> None:
    """Pretty-print a JSON-serializable object with jq-style colors.

    Falls back to plain pretty-printing when stdout is not a TTY.

    @param obj: JSON-serializable object to print
    @param file: File to write to. Defaults to sys.stdout.
    """
    text = json.dumps(obj, indent=2, ensure_ascii=False)

    if file.isatty():
        text = highlight(text, JsonLexer(), Terminal256Formatter())

    print(text, file=file, end="")
