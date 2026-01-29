#!/usr/bin/env bash
# Google AntiGravity Integration Module
# Docs: https://antigravity.google/docs/get-started

run_antigravity_integration() {
  log INFO "AntiGravity: AI-powered code analysis"

  # Validate API key
  if [[ -z "${ANTIGRAVITY_API_KEY:-}" ]]; then
    log ERROR "ANTIGRAVITY_API_KEY not set - export from https://antigravity.google/console"
    return 1
  fi

  # Check worker
  if [[ ! -f "$WORKERS_DIR/antigravity_client.py" ]]; then
    log ERROR "AntiGravity worker not found: $WORKERS_DIR/antigravity_client.py"
    return 1
  fi

  # Run analysis
  local output
  output="$REPORT_DIR/antigravity_analysis.json"
  local mode
  mode="${QUALITY_ANTIGRAVITY_MODE:-refactor}"  # refactor|review|security

  log INFO "Mode: $mode | Target: $ROOT_DIR"

  if python3 "$WORKERS_DIR/antigravity_client.py" \
    --project "$ROOT_DIR" \
    --mode "$mode" \
    --output "$output" \
    --api-key "$ANTIGRAVITY_API_KEY"; then

    # Parse results
    local high_priority
    high_priority=$(jq '[.[] | select(.priority == "high")] | length' "$output" 2>/dev/null || echo 0)
    local total
    total=$(jq 'length' "$output" 2>/dev/null || echo 0)

    log OK "AntiGravity: $total finding(s), $high_priority high-priority"

    # Generate actionable report
    python3 -c "
import json
from pathlib import Path

data = json.loads(Path('$output').read_text())
high = [item for item in data if item.get('priority') == 'high']

if high:
    print('\n🔴 High-Priority Findings:')
    for item in high[:5]:
        print(f\"  • {item.get('file')}: {item.get('message')}\")
"

    return 0
  else
    log ERROR "AntiGravity analysis failed"
    return 1
  fi
}
