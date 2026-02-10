## Track Scope: UI/UX Design + Integration (P0 -> P1)

### Goal
- Deliver modern, interactive PyQt6 UX with backend-integrated actions.
- Keep iconography consistent, remove decorative-only controls, and ensure every interaction maps to real editor logic.

### Implementation Rules
- UI changes must preserve existing shortcuts and productivity flows.
- Use project icon/resources conventions (no emoji-based controls).
- Connect controls to session/backend operations with explicit state sync.

### Required Validation
- Validate action wiring (menus/toolbars/context actions -> session operations).
- Validate selection/map scope behavior for search and editing dialogs.
- Run relevant UI and unit tests for modified components.

### Acceptance Criteria
- UI reflects a coherent modern style and consistent interaction model.
- Controls are functional end-to-end (UI -> backend -> undo/redo).
- No regressions in map editing fundamentals.
