#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting Up Virtual Environment ==="
rm -rf .venv
python -m venv .venv --system-site-packages
pip install -r requirements.txt

echo "=== Running Ruff formatter ==="
ruff format gateway tests

echo "=== Running Ruff lint checks ==="
ruff check gateway tests --fix

echo "=== Running unit tests ==="
python -m unittest discover -s tests -t . -p "test*.py" -v

echo "=== Build succeeded ==="
