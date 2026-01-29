# RME Multi-LLM Setup

## Estrutura Criada

.agents/
+-- workflows/
|   +-- opus_workflow.md      # Architecture (6-8h)
|   +-- sonnet_workflow.md    # Implementation (2-4h)
|   +-- gemini_workflow.md    # Research (30-60min)
|   +-- gpt5_workflow.md      # Advanced reasoning
+-- rules/
    +-- opus_rules.md
    +-- sonnet_rules.md
    +-- gemini_rules.md
    +-- gpt5_rules.md

.cursor/
+-- rules/
|   +-- rme_core.mdc          # Core patterns
|   +-- tfs_canary.mdc        # TFS/Canary
|   +-- otbm_format.mdc       # OTBM deep dive
|   +-- lua_scripting.mdc     # Lua patterns
|   +-- rust_interop.mdc      # Rust optimization
+-- commands/
    +-- rme_commands.json     # Slash commands

## Como Usar

### Antigravity (.agents/)

**Opus (Architecture):**
@opus: Use opus_workflow to design live collaboration system

**Sonnet (Implementation):**
@sonnet: Use sonnet_workflow to port TFS combat system

**Gemini (Research):**
@gemini: Use gemini_workflow to validate border algorithm

**GPT-5-2 (Advanced):**
@gpt5: Use gpt5_workflow to optimize CRDT convergence proof

### Cursor IDE

**Slash Commands:**
/rme-new-brush          # Create new brush
/rme-port-tfs          # Port TFS feature
/rme-port-canary       # Port Canary extension
/rme-lua-script        # Create Lua script
/rme-optimize-rust     # Rust optimization
/rme-otbm-parser       # OTBM parser
/rme-protocol-packet   # Protocol packet

## Proximos Passos

1. **Preencher workflows** em .agents/workflows/
2. **Preencher rules** em .agents/rules/ e .cursor/rules/
3. **Testar comandos** no Cursor IDE
4. **Validar workflows** no Antigravity

## Referencias

- **TFS:** https://github.com/otland/forgottenserver
- **Canary:** https://github.com/opentibiabr/canary
- **RME:** https://github.com/hjnilsson/rme
- **Sonnet 4.5:** https://www.anthropic.com/claude-sonnet-4-5
- **Opus 4.5:** https://www.anthropic.com/claude-opus-4-5
- **Gemini 3:** https://ai.google.dev/gemini-api/docs/gemini-3
- **GPT-5-2:** https://platform.openai.com/docs/guides/latest-model
