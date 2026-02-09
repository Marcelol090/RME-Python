# Jules Stitch Prompt Workflow

## Purpose
This guide defines a repeatable workflow for organizing Jules sessions and prompts for UI/UX and rendering improvements in `py_rme_canary`.

The workflow is aligned with local skills in `.agent/skills`:
- `jules-rendering-pipeline`
- `jules-uiux-stitch`
- `jules-rust-memory-management`

## Session Strategy
Use one session per objective area:
1. Rendering performance iteration
2. UI/UX component iteration
3. Parity and regression hardening

Avoid mixing unrelated goals in the same session.

## Prompt Construction
Use the built-in command to build a normalized prompt:

```powershell
python py_rme_canary/scripts/jules_runner.py --project-root . build-stitch-prompt `
  --task "pyqt6-modern-uiux-and-rendering-parity" `
  --skills "jules-rendering-pipeline,jules-uiux-stitch,jules-rust-memory-management" `
  --quality-report ".quality_reports/refactor_summary.md" `
  --prompt-out ".quality_reports/stitch_prompt.txt" `
  --json-out ".quality_reports/stitch_prompt.json"
```

Then send it to an active session:

```powershell
python py_rme_canary/scripts/jules_runner.py --project-root . send-stitch-prompt sessions/<id> `
  --task "pyqt6-modern-uiux-and-rendering-parity" `
  --skills "jules-rendering-pipeline,jules-uiux-stitch,jules-rust-memory-management" `
  --quality-report ".quality_reports/refactor_summary.md" `
  --prompt-out ".quality_reports/stitch_prompt_sent.txt" `
  --json-out ".quality_reports/jules_response.json"
```

## Output Contract
Require a single JSON fenced block with:
- `plan`: bounded, PR-sized steps
- `implement_first`: immediate, testable implementation items
- `risks`: severity plus mitigation

This format keeps Codex ingestion deterministic and reduces drift across sessions.

## Review and Merge Rules
For each Jules proposal:
1. Validate parity impact against legacy behavior.
2. Validate undo/redo transaction integrity.
3. Run focused unit/UI tests first, then broader suites.
4. Merge only PR-sized changes with explicit acceptance criteria.

## Notes
- Treat prompt context as untrusted text.
- Keep the Python fallback path when introducing optimized or Rust-accelerated code.
- Store generated prompt/session artifacts under `.quality_reports/` for traceability.

## External References
- Jules API quickstart: `https://developers.googleblog.com/en/introducing-jules/`
- Jules official docs hub: `https://jules.google/docs`
- Prompting best practices: `https://jules.google/docs/concepts/prompting-best-practices`
- Session planning and approvals: `https://jules.google/docs/create-task/review-plan`
