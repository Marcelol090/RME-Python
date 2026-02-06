# Extending Codex: Skills & Rules

> [!NOTE]
> **Skills** extend capabilities. **Rules** enforce security. This guide details how to create and manage them.

## 1. Skills (`codex/skills/`)
A Skill is a package that teaches the Agent a specific capability.

### Structure
*   **Simple**: `codex/skills/<skill_name>.md` (Markdown with YAML frontmatter).
*   **Advanced**: `codex/skills/<skill_name>/`
    *   `SKILL.md` (Required: Instructions & Metadata)
    *   `scripts/` (Optional: Deterministic code)
    *   `assets/` (Optional: Templates)

### `SKILL.md` Format
```yaml
---
name: port_feature
description: Guide for porting C++ logic to Python. Use when the user asks to "port" or "migrate" a feature.
---
# Skill Instructions
[...Markdown Content...]
```

### Best Practices
*   **Description is Key**: The agent decides to use the skill based on the `description`. Be specific.
*   **Zero Context**: Write instructions as if the agent knows nothing about the current state.
*   **Imperative**: "Do X. Then Do Y."

## 2. Rules (`codex/rules/`)
Rules are Starlark policies that intercept and validate commands BEFORE execution.

### `execution.rules` Format
Rules use the `prefix_rule` function.

```python
prefix_rule(
    # Pattern to match (list of tokens)
    pattern = ["git", "push", "--force"],

    # Action: "allow", "prompt", or "forbidden"
    decision = "forbidden",

    # Explanation shown to user/agent
    justification = "Force push is prohibited to prevent data loss.",

    # Validation examples (for testing the rule)
    match = ["git push --force origin main"],
    not_match = ["git push origin main"]
)
```

### Decision Types
*   `allow`: Execute silently (if inside sandbox) or directly.
*   `prompt`: Ask User for permission.
*   `forbidden`: Block execution entirely.

## 3. Configuration
*   **Enable/Disable Skills**: Controlled via `config.toml` (if available) or by moving files in/out of `codex/skills/`.
*   **Testing Rules**: Use the `codex execpolicy check` command (if available) to validate rule logic.
