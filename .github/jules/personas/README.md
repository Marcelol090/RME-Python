# Jules Persona Packs

This folder adds role-specialized prompt context for `py_rme_canary/scripts/jules_runner.py`.

## Why this exists

Legacy `remeres-map-editor-redux/.jules/newagents/` has strong specialization (`Profiler`, `Smeller`, `Upgrader`, `wxwidgets`) but in long monolithic prompts.
This folder keeps that specialization while using a compact, schema-first format aligned with the current Python automation pipeline.

## Track mapping

- `tests` -> `tests_contract_guard.md`
- `refactor` -> `refactor_code_health.md`
- `uiux` -> `uiux_widget_render.md`
- fallback (non-track) -> `general_quality.md`

## Design constraints

- Keep output contract deterministic (JSON block expected by `jules_runner.py`).
- Keep scope PR-sized and verifiable.
- Always preserve legacy parity and Python fallback behavior.
- Mention concrete use of `Stitch`, `Render`, and `Context7`.

## Legacy parity crosswalk

- Legacy `Profiler.md` -> `uiux_widget_render.md` (render/interaction/perf constraints).
- Legacy `Smeller.md` + `Upgrader.md` -> `refactor_code_health.md`.
- Legacy audit/test pressure -> `tests_contract_guard.md`.
- General contract and safety -> `general_quality.md`.
