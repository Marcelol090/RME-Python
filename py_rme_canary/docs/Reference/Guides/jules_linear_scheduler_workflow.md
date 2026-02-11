# Jules Linear Scheduler Workflow

## Purpose
Run Jules on a fixed cadence for `P0/P1` progression while preserving linear learning in one long-running session.

## Session Model (Mandatory)
- Use one fixed session for all scheduled runs.
- Do not create a new session from scheduled workflows.
- Store the fixed id in repository variable: `JULES_LINEAR_SESSION` (format: `sessions/<id>`).

## Required Repository Configuration
- Secret: `JULES_API_KEY`
- Variable: `JULES_SOURCE` (example: `sources/github/<owner>/<repo>`)
- Variable: `JULES_LINEAR_SESSION` (single shared session for all tracks)

## Scheduled Workflows
- `.github/workflows/jules_linear_tests.yml`
- `.github/workflows/jules_linear_refactors.yml`
- `.github/workflows/jules_linear_uiux.yml`

All three workflows share `concurrency.group = jules-linear-single-session` to serialize messages into the same session.

## Schedule (America/Sao_Paulo, UTC-3)
- Tests: `01:00` (`cron: 0 4 * * *`)
- Refactors: `03:00` and `06:00` (`cron: 0 6,9 * * *`)
- UI/UX: `07:00` and `12:00` (`cron: 0 10,15 * * *`)

## Prompt Tracks
Prompt templates are versioned in:
- `.github/jules/prompts/linear_tests.md`
- `.github/jules/prompts/linear_refactors.md`
- `.github/jules/prompts/linear_uiux.md`

## Local Commands
Build prompt only:

```bash
python py_rme_canary/scripts/jules_runner.py --project-root . build-linear-prompt \
  --track uiux \
  --session-name sessions/<id> \
  --schedule-slot uiux-07am \
  --prompt-out .quality_reports/jules_linear_uiux_prompt.txt \
  --json-out .quality_reports/jules_linear_uiux_prompt.json
```

Send to fixed session:

```bash
python py_rme_canary/scripts/jules_runner.py --project-root . send-linear-prompt \
  --track refactor \
  --schedule-slot refactor-03am \
  --json-out .quality_reports/jules_linear_refactor_response.json
```

## Operational Notes
- Keep prompts bounded and PR-sized.
- Prioritize pending `P0` items first, then `P1`.
- Keep session artifacts in `.quality_reports/` for auditability.
