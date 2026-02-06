# Contributing

This repo prioritizes parity with the legacy RME C++ implementation while keeping a clean layered architecture.

## Key docs

- ARCHITECTURE.md — module responsibilities and dependency flow
- IMPLEMENTATION_TODO.md — current roadmap
- QUALITY_CHECKLIST.md — pre-commit checklist

## Development setup (Python)

- Create/activate a virtualenv for the workspace (VS Code will usually prompt).
- Install dev dependencies (optional):
  - `python -m pip install -r requirements-dev.txt`

## Checks

- Tests:
  - `python -m pytest`

- Lint (optional):
  - `python -m ruff check py_rme_canary/core py_rme_canary/logic_layer tests`

- Type-check (optional):
  - `python -m mypy py_rme_canary/core py_rme_canary/logic_layer`

## Parity work rules

- Anchor behavior changes to legacy C++ under `source/`.
- Implement the pure algorithm in `py_rme_canary/logic_layer/` first.
- Add unit tests for the pure logic.
- Only then wire it into `py_rme_canary/vis_layer/`.
