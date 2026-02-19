# Jules API Integration Guide

## Scope

This project uses Jules as an asynchronous coding agent through the official API and GitHub workflows.

Current integration files:
- Client: `py_rme_canary/scripts/jules_api.py`
- Runner CLI: `py_rme_canary/scripts/jules_runner.py`
- CI workflows: `.github/workflows/jules-on-issue-label.yml`, `.github/workflows/codex_review_for_jules_prs.yml`

## API Baseline

The client is aligned to the official `v1alpha` surface:
- base URL: `https://jules.googleapis.com/v1alpha`
- auth header: `x-goog-api-key: <JULES_API_KEY>`

Primary resources used:
- `sources`
- `sessions`
- session activities and plan/message actions

## Environment Contract

Required:
- `JULES_API_KEY`
- `JULES_SOURCE`

Optional:
- `JULES_BRANCH`

Resolution strategy:
1. CLI arguments (highest priority)
2. environment variables
3. `.env` defaults loaded by `load_env_defaults()`

## Prompt Safety Controls

`jules_runner.py` applies prompt-hardening before sending context:
- strips control characters;
- normalizes task labels;
- neutralizes common prompt-injection strings in report context;
- enforces deterministic JSON contract extraction (`implemented`, `suggested_next`).

## Persona Packs (Legacy-aware Refactor)

To preserve legacy specialization without monolithic prompts, the runner now loads modular persona packs from:
- `.github/jules/personas/`

Default behavior:
- `tests` track -> `tests_contract_guard.md`
- `refactor` track -> `refactor_code_health.md`
- `uiux` track -> `uiux_widget_render.md`
- fallback -> `general_quality.md`

CLI overrides:
- `--persona-pack <name-or-path>`
- `--max-persona-chars <n>`

Audit support:
- `audit-persona-structure` for machine-readable comparison between legacy persona structure
  and the current modular packs.

Persona content is injected into prompt blocks as `<persona_context>` for:
- quality suggestions
- stitch prompts
- linear scheduled prompts

## Codex + Jules Asynchronous Pattern

Recommended flow:
1. Jules creates or updates code through issue-driven automation.
2. GitHub PR events and comments trigger Codex review workflows.
3. Codex reads Jules artifacts (`reports/jules/*.json|*.md`) and snapshot context (`.codex_context/*`).
4. Human review remains mandatory before merge.

This model does not require internal access to Jules reasoning traces; it relies on repository artifacts and workflow events as the system-of-record.

## Workflow Security Notes

For issue-triggered automation (`.github/workflows/jules-on-issue-label.yml`):
- keep actor allowlists on workflow conditions (`if:`) to prevent untrusted prompt injection from arbitrary users;
- keep `contents` permissions read-only unless write is strictly required;
- keep the output contract in-repo (`reports/jules/suggestions.*` + schema validation) to allow deterministic review by Codex/humans.
