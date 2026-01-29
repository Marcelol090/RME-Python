# Agent Skills

(Source: https://developers.openai.com/codex/skills)

## Agent skill definition
A skill captures a capability expressed through Markdown instructions in a `SKILL.md` file. A skill folder can also include scripts, resources, and assets that Codex uses to perform a specific task.

Structure:
```
my-skill/
    SKILL.md    (Required: instructions + metadata)
    scripts/    (Optional: executable code)
    references/ (Optional: documentation)
    assets/     (Optional: templates, resources)
```

## Where to save skills
Load order precedence:
1. `$CWD/.codex/skills` (Repo local)
2. `$CWD/../.codex/skills`
3. `$REPO_ROOT/.codex/skills`
4. `$CODEX_HOME/skills`
5. `~/.codex/skills` (User global)

## SKILL.md format
```yaml
---
name: skill-name
description: Description that helps Codex select the skill
metadata:
  short-description: Optional user-facing description
---
Skill instructions for the Codex agent to follow when using this skill.
```
