# Quality Improvement Proposal

## 1. Summary of Findings
- **Security:** Resolved 1 critical vulnerability (Bandit B314/B405) in `py_rme_canary/core/brush_manager.py` by implementing safe XML parsing with `defusedxml`.
- **Ruff Issues:** The provided report context indicated 0 issues, but a local verification run detected ~2200 issues. This discrepancy suggests a need to align local and CI/Report configurations.
- **Complexity:** 187 functions have complexity > 10. `TransactionalBrushStroke.paint` is the highest with complexity 102.
- **Type Checking:** Mypy detected missing stubs and import errors (e.g., `defusedxml`, `PIL`, `PyQt6`).

## 2. High-Value Suggestions

### 2.1 Refactoring High Complexity Functions
The following functions exceed maintainability thresholds and should be prioritized for refactoring:
- `TransactionalBrushStroke.paint` (Complexity: 102) in `py_rme_canary/logic_layer/transactional_brush.py`
- `AutoBorderProcessor._process_terrain_logic` (Complexity: 80) in `py_rme_canary/logic_layer/auto_border.py`

**Action:** Break these functions into smaller, testable sub-functions.

### 2.2 Address Ruff Issues / Configuration
**Action:**
1. Investigate why the report context showed 0 issues while local run showed ~2200.
2. If the 2200 issues are valid, configure `pre-commit` to run `ruff --fix` incrementally.

### 2.3 Improve Type Safety
Mypy errors indicate missing stubs.
**Action:**
- Install `types-defusedxml`, `types-Pillow`, `types-PyQt6` (if available, or use `mypy --install-types`).
- Fix `import-not-found` errors.

### 2.4 Code Duplication
Enable `jscpd` in the quality pipeline to detect and reduce code duplication.

## 3. Next Steps
- Merge the security fix.
- Schedule a "Refactoring Sprint" to address complexity.
- Enable `pre-commit` hooks for all developers.
