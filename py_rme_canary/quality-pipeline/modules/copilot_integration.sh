#!/usr/bin/env bash
# GitHub Copilot Integration Module
# Requires: GITHUB_TOKEN env var

run_copilot_integration() {
  log INFO "GitHub Copilot: Analyzing codebase"

  # Validate dependencies
  if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    log ERROR "GITHUB_TOKEN not set - skipping Copilot integration"
    return 1
  fi

  if ! python3 -c "import openai" 2>/dev/null; then
    log WARN "openai package not installed - installing..."
    pip install -q openai
  fi

  # Run Copilot worker
  local output
  output="$REPORT_DIR/copilot_suggestions.json"

  if python3 "$WORKERS_DIR/copilot_client.py" \
    --project "$ROOT_DIR" \
    --output "$output"; then

    local suggestion_count
    suggestion_count=$(jq 'length' "$output" 2>/dev/null || echo 0)
    log OK "Copilot: $suggestion_count suggestion(s) generated"

    # Optional: auto-apply high-confidence suggestions
    if [[ "${QUALITY_COPILOT_AUTO_APPLY:-false}" == "true" ]]; then
      log INFO "Auto-applying high-confidence suggestions..."
      python3 "$WORKERS_DIR/copilot_client.py" \
        --apply "$output" \
        --confidence-threshold 0.9
    fi

    return 0
  else
    log ERROR "Copilot worker failed"
    return 1
  fi
}
