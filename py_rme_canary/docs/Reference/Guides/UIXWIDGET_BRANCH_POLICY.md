# UIxWidget Branch Policy

This document defines how UI/UX, Widget and Render changes must flow across branches.

## Scope of `UixWidget`
- Primary branch for:
  - PyQt6 widgets and dialogs
  - UI/UX interactions and visual polish
  - Render-facing UI behavior (canvas overlays, presentation toggles, view controls)

## What must stay out of `UixWidget`
- Non-UI business logic refactors in `core/` and `logic_layer/`
- Data model/schema or protocol-level redesigns not required by UI
- Pipeline/release changes not needed for UI/UX delivery

## Promotion flow
1. `UixWidget`:
   - active UI implementation branch
2. `development`:
   - receives tested UI batches from `UixWidget`
3. `main`:
   - receives only validated releases from `development`

## Minimum validation before promotion
- `ruff check` (changed files)
- `python -m py_compile` (changed files)
- `pytest -q -s py_rme_canary/tests/ui`
- optional full pipeline when release-oriented:
  - `bash py_rme_canary/quality-pipeline/quality_lf.sh --verbose`

## Documentation requirements
- Update UI parity planning:
  - `py_rme_canary/docs/Planning/TODOs/TODO_CPP_PARITY_UIUX_2026-02-06.md`
- Update implementation log:
  - `py_rme_canary/docs/Changelog/Logs/IMPLEMENTACAO_2026-02-09.md`
- Keep feature state synchronized:
  - `py_rme_canary/docs/Planning/Features.md`
