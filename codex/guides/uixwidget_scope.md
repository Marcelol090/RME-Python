# UixWidget Branch Scope (Codex)

This guide defines the hard scope for branch `UixWidget`.

## Allowed Scope
- `py_rme_canary/vis_layer/**`
- `py_rme_canary/tests/ui/**`
- `py_rme_canary/tests/unit/vis_layer/**`
- UI/UX planning and changelog docs only:
  - `py_rme_canary/docs/Planning/TODOs/TODO_CPP_PARITY_UIUX_2026-02-06.md`
  - `py_rme_canary/docs/Changelog/Logs/IMPLEMENTACAO_2026-02-09.md`

## Out of Scope
- `py_rme_canary/core/**`
- `py_rme_canary/logic_layer/**` (except minimal adapter calls strictly required by UI wiring)
- Release/versioning pipeline changes unrelated to UI/UX
- Database/network/protocol features not required for widget/render behavior

## Branch Policy
1. `UixWidget` is the integration branch for:
   - Widget work
   - Renderer/UI visual behavior
   - UX interactions
2. `development` receives only stable UI/UX batches from `UixWidget`.
3. `main` receives only approved, tested merges from `development`.

## Merge Contract (`UixWidget` -> `development` -> `main`)
1. Run at least:
   - `pytest -q -s py_rme_canary/tests/ui`
   - `ruff check` for changed files
   - `python -m py_compile` for changed files
2. Keep changelog updated for each UI/UX session.
3. Keep `Features.md` and TODO parity docs aligned with shipped behavior.
