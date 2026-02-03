# Quality Scan Report

**Date:** 2026-02-01

## Executive Summary
A full quality scan was performed using the project's quality pipeline and manual execution of tools where the pipeline was blocked.

- **Dependencies**: Missing `types-Pillow`.
- **Linting (Ruff)**: 1883 issues.
- **Type Checking (Mypy)**: blocking errors found.
- **Complexity (Radon)**: 177 functions with complexity > 10.
- **Security (Bandit)**: No issues found.
- **Structure (ast-grep)**: Configuration error prevented scan.

## Actionable Issues

### 1. Dependencies
The project relies on `Pillow` but is missing type stubs, causing Mypy errors.
**Action:** Install `types-Pillow`.

### 2. Type Checking (Mypy)
Mypy failed during baseline check with the following critical errors:
- **Unreachable Code:** In `py_rme_canary/logic_layer/operations/map_import.py`, `ImportMapReport` fields are typed as strict but default to `None`.
  *Fix:* Update type hints to `Optional[...]` or `... | None`.
- **Variable Shadowing/Type Confusion:** In `py_rme_canary/logic_layer/operations/map_import.py`, the loop variable `area` is reused for both `monster_spawns` and `npc_spawns`, causing type inference conflicts.
  *Fix:* Rename the loop variable in the second loop (e.g., to `npc_area`).

### 3. Structural Analysis (ast-grep)
The rule file `py_rme_canary/tools/ast_rules/anti-patterns.yml` is invalid for the installed version of `ast-grep` (0.40.5). It uses a `rules:` list which is not supported by `sg scan --rule`.
**Action:** Split the rules into separate files or update the configuration strategy.

### 4. Code Complexity
177 functions exceed the complexity threshold (10). Top offenders:
- `py_rme_canary/logic_layer/transactional_brush.py:paint` (CC: 102)
- `py_rme_canary/logic_layer/borders/processor.py:_process_terrain_logic` (CC: 80)
- `py_rme_canary/logic_layer/borders/alignment.py:select_border_alignment` (CC: 53)

**Action:** Refactor these functions to reduce complexity.

### 5. Linting
1883 linting issues reported by Ruff.
**Action:** Run `ruff check . --fix` to automatically resolve most issues.
