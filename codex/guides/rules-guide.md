# Rules

(Source: https://developers.openai.com/codex/rules)

## Create a rules file
1. Create a `.rules` file under `./codex/rules/` (for example, `~/.codex/rules/default.rules`).
2. Add a rule. This example prompts before allowing `gh pr view` to run outside the sandbox.

Rules control which commands Codex can run outside the sandbox.
