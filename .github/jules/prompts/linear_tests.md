## Track Scope: Tests (P0 -> P1)

### Goal
- Increase confidence in critical editor flows with deterministic coverage.
- Prioritize regressions around map loading, session actions, search parity, and context menu transactional behavior.

### Implementation Rules
- Add focused tests first; expand only when failures indicate related risk.
- Keep fixtures lightweight and explicit.
- Avoid flaky timing assertions and network dependencies.

### Required Validation
- Run targeted unit tests for touched modules.
- Run UI-focused tests when UI handlers/actions were changed.
- Provide exact command list and expected pass/fail criteria.

### Acceptance Criteria
- New tests are stable across repeated runs.
- Critical P0 gaps have direct test coverage.
- Test names clearly map to behavior being protected.
