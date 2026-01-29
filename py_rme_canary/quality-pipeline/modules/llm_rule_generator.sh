#!/usr/bin/env bash
# LLM-Powered ast-grep Rule Generator
# Provider-agnostic: supports Copilot, AntiGravity, Claude

run_llm_rule_generator() {
  log INFO "LLM Rule Generator: Creating ast-grep rules"

  # Determine provider
  local provider
  provider="${QUALITY_LLM_PROVIDER:-auto}"

  if [[ "$provider" == "auto" ]]; then
    # Auto-detect based on available API keys
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
      provider="copilot"
    elif [[ -n "${ANTIGRAVITY_API_KEY:-}" ]]; then
      provider="antigravity"
    elif [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
      provider="claude"
    else
      log ERROR "No LLM provider configured - set GITHUB_TOKEN, ANTIGRAVITY_API_KEY, or ANTHROPIC_API_KEY"
      return 1
    fi
  fi

  log INFO "Using provider: $provider"

  # Analyze codebase for anti-patterns
  local analysis_file
  analysis_file="$CACHE_DIR/codebase_analysis.json"

  log INFO "Analyzing codebase for patterns..."
  python3 "$WORKERS_DIR/rule_generator.py" \
    --analyze "$ROOT_DIR" \
    --output "$analysis_file"

  # Generate rules via LLM
  local rules_output
  rules_output="$ROOT_DIR/tools/ast_rules/python/generated_rules.yml"

  log INFO "Generating ast-grep rules via LLM ($provider)..."

  if python3 "$WORKERS_DIR/rule_generator.py" \
    --provider "$provider" \
    --analysis "$analysis_file" \
    --output "$rules_output" \
    --max-rules "${QUALITY_LLM_MAX_RULES:-20}"; then

    # Validate generated rules
    if command -v sg &>/dev/null; then
      log INFO "Validating generated rules..."
      if sg test "$rules_output"; then
        log OK "Generated rules are valid"
      else
        log WARN "Some generated rules failed validation - review manually"
      fi
    fi

    local rule_count
    rule_count=$(yq eval '.rules | length' "$rules_output" 2>/dev/null || echo \"?\")
    log OK "Generated $rule_count ast-grep rule(s)"

    # Optional: auto-apply generated rules
    if [[ "${QUALITY_LLM_AUTO_APPLY:-false}" == "true" ]]; then
      log INFO "Auto-applying generated rules..."
      sg scan --rule "$rules_output" --rewrite "$ROOT_DIR" || log WARN "Some rewrites failed"
    fi

    return 0
  else
    log ERROR "Rule generation failed"
    return 1
  fi
}
