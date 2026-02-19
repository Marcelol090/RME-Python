# Jules Prompt Persona Architecture

## Context

This project now uses persona packs to keep the best part of legacy `.jules/newagents` specialization while preserving strict JSON contracts and deterministic automation from `jules_runner.py`.

## Legacy vs Current (Audit Summary)

Legacy strengths (`remeres-map-editor-redux/.jules/newagents`):
- Strong role specialization (Profiler, Smeller, Upgrader, wxWidgets).
- Deep domain constraints per role.

Legacy weaknesses:
- Very long monolithic prompts.
- Higher drift risk and weaker structured-output guarantees.

Current strengths (`py_rme_canary/scripts/jules_runner.py`):
- Contract-first prompts (schema-friendly JSON output).
- Session/track controls and safer context sanitation.
- Better automation fit with quality pipeline and reports artifacts.

Gap identified and closed:
- Missing modular persona layer in Python workflow.

## Refactor Implemented

- Added persona templates:
  - `.github/jules/personas/general_quality.md`
  - `.github/jules/personas/uiux_widget_render.md`
  - `.github/jules/personas/refactor_code_health.md`
  - `.github/jules/personas/tests_contract_guard.md`
  - `.github/jules/personas/security_live_stack.md`
- Added mapping and loader in `jules_runner.py`:
  - track defaults (`tests`, `refactor`, `uiux`)
  - fallback (`general_quality`)
  - explicit override via `--persona-pack`
- Injected `<persona_context>` into:
  - `build_quality_prompt()`
  - `build_stitch_ui_prompt()`
  - `build_linear_scheduled_prompt()`
- Added CLI controls:
  - `--persona-pack`
  - `--max-persona-chars`
  for `build-stitch-prompt`, `send-stitch-prompt`, `build-linear-prompt`, `send-linear-prompt`, and `generate-suggestions`.
- Added structural audit command:
  - `audit-persona-structure`
  - compares `remeres-map-editor-redux/.jules/newagents` with `.github/jules/personas`
  - emits machine-readable summary for drift detection.

Example:

```bash
python py_rme_canary/scripts/jules_runner.py --project-root . audit-persona-structure \
  --json-out .quality_reports/jules_persona_audit.json
```

## Why this is better than legacy now

- Keeps role specialization from legacy.
- Keeps deterministic output contract required by this repository pipeline.
- Reduces prompt size/noise while preserving scope constraints.
- Improves traceability by storing persona metadata in generated artifacts.

## External references used

- Jules API docs: https://developers.google.com/jules/api
- Jules REST reference: https://developers.google.com/jules/api/reference/rest
- Jules Action repository: https://github.com/google-labs-code/jules-action
- Gemini API structured output guidance: https://ai.google.dev/api/generate-content
