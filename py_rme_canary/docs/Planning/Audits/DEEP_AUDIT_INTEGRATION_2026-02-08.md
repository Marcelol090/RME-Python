# Deep Audit & Integration Plan (2026-02-08)

## Scope Reviewed
- `awesome-copilot/` (agent/prompt/instruction quality patterns, repository governance structure).
- `codex/` (execution flow, task lifecycle, Jules/Codex orchestration guides).
- `py_rme_canary/docs/` (planning, architecture, quality pipeline, parity TODOs).
- `remeres-map-editor-redux/` (legacy feature references and expected editor behavior).

## Functional Parity Snapshot (Legacy -> Python)

| Capability | Legacy Reference | Python Status | Notes |
|---|---|---|---|
| OTBM ServerID/ClientID translation | RME OTBM 1-6 flow | Implemented | Load/save translation present in core IO + session flow. |
| Cross-instance clipboard (sprite hash) | Legacy cross-version copy/paste | Implemented | Hash matching + conversion fallback available. |
| Lasso/freehand selection | Legacy selection tools | Implemented | Selection mode + lasso integration active. |
| Lua monster import | Legacy import menu | Implemented | File/folder Lua import integrated. |
| OTMM export | Legacy minimap/export flow | Implemented | UI action and saver integrated. |
| Client profile management | Legacy client data profiles | Implemented | Profile dialog and persistence active. |
| Interactive data-stack loading | Legacy data loading UX expectation | Implemented (this cycle) | New loader with progress + summary + explicit definition override. |
| Interactive map loading UX | Legacy loading feedback | Implemented (this cycle) | `Open Map` now shows progress phases and UI refresh. |
| Show ClientIDs toggle in UI | Legacy/documented feature | Implemented (this cycle) | `View/Window -> Show Client IDs` now overlays client ids using item metadata + id mapper fallback. |

## Documentation Findings
- `codex/` and `py_rme_canary/docs/` already define strong execution protocols and quality gates.
- `awesome-copilot/` provides reusable standards for high-quality agent/instruction authoring.
- The project had good technical depth but lacked a single explicit audit note linking legacy parity checks to current implementation changes and workflow diagnostics.

## Documentation Synthesis (awesome-copilot / codex / py_rme_canary/docs)
- `awesome-copilot`: contributes agent workflow patterns (planning rigor, review checklists, governance templates) useful for repeatable implementation/review loops.
- `codex`: provides project-specific execution contracts (`agent_workflow`, `tool_usage`, `porting_workflow`) that map directly to parity execution in this repository.
- `py_rme_canary/docs`: defines product/technical target state (`Features.md`, parity TODOs, quality guides) and remains the implementation source of truth for acceptance criteria.
- Practical outcome of the synthesis: prioritize parity items that are both user-visible and architecture-safe (e.g., `Show Client IDs`, loader UX, workflow diagnostics), then validate with deterministic tests and quality pipeline output.

## Workflow Findings (Codex Review Skip)
- Root cause of prior invalid-workflow errors: direct `secrets.*` checks inside `if:` expressions (unsupported in that context by GitHub expression validator).
- Existing review workflow had strict pre-filtering for Jules actor checks that could silently skip valid manual/reusable runs.
- Skip reasons were not always explicit to maintainers when secrets were missing.
- Current update replaces direct-secret checks with a detection step (`steps.secrets.outputs.*`) and centralizes gate reasons (`eligible`, `manual_override`, `not_jules_author`, `fork_pr_no_secrets`).

## Implemented in This Iteration
- Added a dedicated **Client Data Loader** dialog (`assets + appearances + items.otb + items.xml`).
- Added staged progress feedback for **Open Map** and **Client Data Load** operations.
- Added UI refresh synchronization after data load (palette/grid/canvas preview consistency).
- Hardened Codex/Jules review workflow skip logic with clearer gate behavior and missing-secret notification comments.

## Validation Snapshot (2026-02-08)
- `python -m pytest -q py_rme_canary/tests` -> `619 passed` (full local suite green).
- `python -m pytest -q py_rme_canary/tests/ui/test_toolbar_menu_sync.py` -> `6 passed`.
- `bash py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --verbose --skip-ui-tests --skip-security --skip-deadcode --skip-sonarlint --skip-jules` -> completed with cache hits and no new normalized issues.
- Workflow lint sanity:
  - YAML parse for Codex workflows succeeded.
  - No direct `secrets.*` references remain in `if:` expressions in `.github/workflows/*.yml`.

## Validation Snapshot (2026-02-08, round 2)
- `python -m pytest -q py_rme_canary/tests` -> `624 passed`.
- `python -m pytest -q py_rme_canary/tests/unit/logic_layer/test_drawing_options.py py_rme_canary/tests/unit/vis_layer/test_map_drawer_overlays.py py_rme_canary/tests/ui/test_toolbar_menu_sync.py` -> `28 passed`.
- `quality_lf.sh` compatibility hardening completed:
  - `ruff`, `mypy`, `radon` now run via `"$PYTHON_BIN" -m ...` in pipeline execution.
  - dependency probing now prefers `PYTHON_BIN` module checks (eliminates false negatives from PATH-only command lookup).

## Next Recommended P0/P1 Follow-ups
1. Add explicit `Show ClientIDs` visualization toggle in renderer/view menu.
2. Extend loader summary with persisted profile save-as option (single-click profile creation).
3. Add UI integration tests for the new loader dialog and map-open progress path.
4. Add workflow-level CI validation for trigger matrix (`pull_request`, `issue_comment`, `workflow_dispatch`, `workflow_call`).
