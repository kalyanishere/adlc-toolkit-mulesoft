#!/bin/sh
# mule-lint — POSIX shell wrapper that delegates to check.py
# Usage: sh tools/mule-lint/check.sh [path] [--format text|json|junit]

set -e

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PYTHON=${PYTHON:-python3}

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "mule-lint: $PYTHON not found in PATH" >&2
  exit 2
fi

exec "$PYTHON" "$SCRIPT_DIR/check.py" "$@"
