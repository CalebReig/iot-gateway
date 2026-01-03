#!/usr/bin/env bash
set -euo pipefail

echo "=== Running Ruff formatter ==="
ruff format gateway tests

echo "=== Running Ruff lint checks ==="
ruff check gateway tests

echo "=== Running unit tests ==="
python -m unittest discover -s tests -t . -p "test*.py" -v

echo "=== Build succeeded ==="
