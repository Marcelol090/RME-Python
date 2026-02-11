## Track Scope: Refactors (P0 -> P1)

### Goal
- Improve maintainability, readability, and reliability without changing user-visible behavior.
- Prioritize hotspots with duplicated logic, weak boundaries, or performance drag in session/render paths.

### Implementation Rules
- Keep every change bounded to a clear technical objective.
- Preserve undo/redo semantics and transactional editing guarantees.
- Prefer extracting small, tested helpers over large rewrites.

### Required Validation
- Run impacted unit suites and any quality checks relevant to touched code.
- Report complexity/performance deltas when applicable.
- List potential regressions and mitigation checks.

### Acceptance Criteria
- Behavior remains equivalent for existing flows.
- Complexity is reduced measurably or code paths become easier to validate.
- Quality pipeline signals remain green for the changed scope.
