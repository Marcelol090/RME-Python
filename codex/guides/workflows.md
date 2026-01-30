# Codex Workflows & Prompting Guide

(Source: User Provided Documentation + OpenAI Cookbook)

## Prompting Tips
- **Be Specific:** Codex works best with explicit context and clear "definitions of done".
- **Break it Down:** Split complex tasks into smaller, focused steps.
- **Provide Context:** Always mention relevant files (`@filename`) or add them to the context.

## Standard Workflows

### 1. Explain a Codebase
**Goal:** Onboarding or understanding a flow.
- **Action:** Open relevant files.
- **Prompt:** "Explain how the request flows through the selected code. Include responsibilities, validation, and gotchas."

### 2. Fix a Bug
**Goal:** Resolve a reproduction.
- **Action:** Provide reproduction recipe + suspect files.
- **Prompt:** "Bug: [Description]. Repro: [1, 2, 3]. Constraints: [No API changes]. Find the bug and propose a fix."

### 3. Write a Test
**Goal:** High coverage.
- **Action:** Select function code.
- **Prompt:** "Write a unit test for this function. Follow conventions used in other tests."

### 4. Prototype from Screenshot
**Goal:** Quick UI scaffolding.
- **Action:** Attach image.
- **Prompt:** "Create a new dashboard based on this image. Constraints: [PyQt6, Theme tokens]. Deliverables: [Widget code]."

### 5. Iterate on UI
**Goal:** Polish.
- **Action:** Run app/preview.
- **Prompt:** "Propose 3 styling improvements. Change only the header..."

## Strategic Planning (The "Plan" Skill)
Use `$plan` or explicit planning prompts for major refactors.
- **Prompt:** "We need to refactor [System]. Constraints: [No breaking changes]. Output a step-by-step migration plan."

## References
- [Codex Executive Plans](https://cookbook.openai.com/articles/codex_exec_plans)
- [Code Modernization Example](https://developers.openai.com/cookbook/examples/codex/code_modernization)
