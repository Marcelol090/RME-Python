# Jules Linear Scheduler Workflow

## Purpose
Run Jules on a fixed cadence for `P0/P1` progression while preserving linear learning in one long-running session.

## Session Model (Mandatory)
- Use one fixed session per track (recommended):
  - `tests` -> `JULES_LINEAR_SESSION_TESTS`
  - `refactor` -> `JULES_LINEAR_SESSION_REFACTOR`
  - `uiux` -> `JULES_LINEAR_SESSION_UIUX`
- Do not create a new session from scheduled workflows.
- Each variable must store a stable session id in `sessions/<id>` format.
- Legacy fallback remains supported only for local/manual compatibility:
  - `JULES_LINEAR_SESSION` (used when track-specific variable is missing).

## Required Repository Configuration
- Secret: `JULES_API_KEY`
- Variable: `JULES_SOURCE` (example: `sources/github/<owner>/<repo>`)
- Variables (recommended):
  - `JULES_LINEAR_SESSION_TESTS`
  - `JULES_LINEAR_SESSION_REFACTOR`
  - `JULES_LINEAR_SESSION_UIUX`

## Scheduled Workflows
- `.github/workflows/jules_linear_tests.yml`
- `.github/workflows/jules_linear_refactors.yml`
- `.github/workflows/jules_linear_uiux.yml`

Each workflow has a dedicated concurrency group to keep track isolation:
- `jules-linear-tests-session`
- `jules-linear-refactor-session`
- `jules-linear-uiux-session`

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
  --schedule-slot uiux-07am \
  --prompt-out .quality_reports/jules_linear_uiux_prompt.txt \
  --json-out .quality_reports/jules_linear_uiux_prompt.json
```

By default, `build-linear-prompt`/`send-linear-prompt` resolves env vars by track:
- `tests` -> `JULES_LINEAR_SESSION_TESTS`
- `refactor` -> `JULES_LINEAR_SESSION_REFACTOR`
- `uiux` -> `JULES_LINEAR_SESSION_UIUX`

Send to fixed session:

```bash
python py_rme_canary/scripts/jules_runner.py --project-root . send-linear-prompt \
  --track refactor \
  --schedule-slot refactor-03am \
  --json-out .quality_reports/jules_linear_refactor_response.json
```

Override env binding explicitly (optional):

```bash
python py_rme_canary/scripts/jules_runner.py --project-root . send-linear-prompt \
  --track tests \
  --session-env JULES_LINEAR_SESSION_TESTS \
  --schedule-slot tests-01am
```

Track-specific session status (recommended):

```bash
python py_rme_canary/scripts/jules_runner.py --project-root . track-session-status \
  --track tests \
  --json-out .quality_reports/jules_linear_tests_status.json
```

All tracks status snapshot:

```bash
python py_rme_canary/scripts/jules_runner.py --project-root . track-sessions-status \
  --json-out .quality_reports/jules_linear_tracks_status.json
```

## Operational Notes
- Keep prompts bounded and PR-sized.
- Prioritize pending `P0` items first, then `P1`.
- Keep session artifacts in `.quality_reports/` for auditability.
