#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE="${SCRIPT_DIR}/py_rme_canary/quality-pipeline/quality_lf.sh"

if [[ ! -f "${PIPELINE}" ]]; then
  echo "ERROR: quality pipeline not found: ${PIPELINE}" >&2
  exit 1
fi

exec bash "${PIPELINE}" "$@"
