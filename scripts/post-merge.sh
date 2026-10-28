#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
uv pip install \
  --no-progress \
  --target ".pythonlibs/lib/python${PYTHON_VERSION}/site-packages" \
  --requirements requirements.txt
