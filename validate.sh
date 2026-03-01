#!/bin/bash

echo "=== Type Checking ===" && \
uv run --dev pyright && \
echo "=== Linting ===" && \
uv run --dev ruff check && \
echo "=== Formatting ===" && \
uv run --dev ruff format && \
echo "=== Import Sorting ===" && \
uv run --dev ruff check --select I --fix && \
echo "=== Running Tests ===" && \
uv run --dev pytest -v --tb=short -W error::UserWarning
