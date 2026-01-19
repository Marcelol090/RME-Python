# 🧠 Guia Completo - Sistema de Memória do Codex

---

## 📂 Estrutura de Arquivos

### Organização Recomendada
```
py_rme_canary/
├── core/                    # Data models & I/O (zero UI deps)
│   ├── assets/              # Sprite loading & caching
│   ├── config/              # Configuration & projects
│   ├── constants/           # OTBM constants, magic bytes
│   ├── data/                # GameMap, Tile, Item, House, etc.
│   ├── database/            # ItemsXML, ItemsOTB, IdMapper
│   ├── io/                  # OTBM/XML parsers and savers
│   ├── protocols/           # Type protocols
│   ├── memory_guard.py      # Memory protection system
│   └── runtime.py           # Runtime validations
│
├── logic_layer/             # Business logic (UI-agnostic)
│   ├── borders/             # Auto-border algorithms
│   ├── history/             # Undo/Redo system
│   ├── operations/          # Bulk operations (search/replace)
│   ├── session/             # EditorSession, Selection, Clipboard
│   ├── brush_definitions.py # Brush definitions & factory
│   ├── auto_border.py       # Auto-border processor
│   └── geometry.py          # Geometric utilities
│
├── vis_layer/               # UI implementation (PyQt6)
│   ├── renderer/            # OpenGL renderer & drawing
│   ├── ui/                  # UI components
│   │   ├── canvas/          # Map canvas widget
│   │   ├── docks/           # Palette, minimap, properties
│   │   ├── main_window/     # QtMapEditor + mixins
│   │   └── theme.py         # Design token system
│   └── qt_app.py            # Application entry point
│
├── tools/                   # Utility scripts
│   ├── export_brushes_json.py
│   └── read_otbm_header.py
│
├── tests/                   # Test suite
│   ├── unit/                # Unit tests (core/logic)
│   ├── ui/                  # UI tests (pytest-qt)
│   └── performance/         # Benchmarks
│
└── docs/                    # Documentation
    ├── PRD.md               # This document
    ├── ARCHITECTURE.md      # Architecture guide
    ├── IMPLEMENTATION_STATUS.md # Feature parity checklist
    └── WALKTHROUGH.md       # Development walkthrough
```

---

---

## 🎯 Como Funciona

### Fluxo de Sessão (Automático)

1. **Você inicia Codex:**
   ```bash
   codex
   # ou
   codex --profile refactor
   ```

2. **Codex lê automaticamente** (devido ao `docs`):
   - `py_rme_canary/docs/memory_instruction.md` ← **Memória do projeto**
   - `py_rme_canary/docs/agents.md` ← Regras fundamentais

3. **Codex agora tem contexto de:**
   - Decisões arquiteturais passadas (ADRs)
   - Trabalho em progresso (Active Work Tracking)
   - Padrões de código estabelecidos
   - Anti-patterns a evitar
   - Comandos de verificação

4. **Durante a sessão:**
   - Antes de mudar código → Verifica contra `memory_instruction.md`
   - Se detectar inconsistência → Re-lê o arquivo
   - Ao final → Sugere atualizar o arquivo com novo progresso

---

## 📝 Manutenção do memory_instruction.md

### Quando Atualizar

#### ✅ Sempre que:
1. **Tomar decisão arquitetural importante**
   - Exemplo: "Migrar de Celery para asyncio tasks"
   - Ação: Adicionar novo ADR na Seção 2

2. **Completar um milestone**
   - Exemplo: "Refatoração do módulo auth concluída"
   - Ação: Mover de "In-Progress" para "Decision History"

3. **Adicionar nova dependência**
   - Exemplo: "pip install redis"
   - Ação: Documentar na Seção 6 (Dependency Management)

4. **Descobrir novo padrão ou anti-pattern**
   - Exemplo: "Descobrimos que X causa race condition"
   - Ação: Adicionar em "Forbidden Patterns" (Seção 5)

#### ⚠️ Não atualizar para:
- Mudanças triviais (typos, comentários)
- Alterações temporárias/experimentais
- Trabalho que será revertido

### Como Atualizar (Workflow)

```bash
# 1. Edite o arquivo
nano py_rme_canary/docs/memory_instruction.md

# 2. Adicione entrada com data
## 2. DECISION HISTORY
### [2026-01-15] Nova decisão importante
- **Reason:** Por que fizemos isso
- **Impact:** O que muda
- **Rollback Plan:** Como reverter se necessário

# 3. Incremente versão no final do arquivo
## 11. VERSION HISTORY
### v1.2 (2026-01-15)
- Added: Decisão sobre X
- Updated: Seção Y com novo padrão
```

---

## 🧪 Testando o Sistema de Memória

### Teste 1: Verificar Leitura Inicial
```bash
codex --profile default

# Dentro do Codex, pergunte:
"What files should you read at the start of every session?"

# Resposta esperada:
# "I must read:
#  1. py_rme_canary/docs/memory_instruction.md
#  2. py_rme_canary/docs/agents.md"
```

### Teste 2: Verificar Contexto de Decisões
```bash
codex

# Pergunte:
"What's our current HTTP client library and why?"

# Resposta esperada (baseada no memory_instruction.md):
# "We use httpx (not requests) because:
#  - Native async support
#  - 40% latency reduction
#  - Decision made: 2026-01-14 (ADR)"
```

### Teste 3: Verificar Anti-Patterns
```bash
codex

# Peça:
"Show me how to make an HTTP request"

# Resposta NÃO deve incluir:
# - import requests (anti-pattern documentado)
# - asyncio.run() dentro de função sync
# - Bare except clauses

# Resposta DEVE incluir:
# - import httpx
# - async with httpx.AsyncClient()
# - Specific exception handling
```

### Teste 4: Continuidade Entre Sessões
```bash
# Sessão 1
codex
"Start implementing rate limiting feature. Just create the basic structure."
# [Codex cria estrutura]
exit

# Sessão 2 (NOVA SESSÃO, mesmo projeto)
codex
"Continue the rate limiting implementation"

# Resposta esperada:
# Codex deve:
# 1. Re-ler memory_instruction.md
# 2. Encontrar "In-Progress: API Rate Limiting" na Seção 3
# 3. Continuar de onde parou (mesmo sem você explicar novamente)
```

---

## 🎓 Uso Avançado

### Estratégia 1: Profiles para Diferentes Contextos

```bash
# Desenvolvimento normal (lê memória completa)
codex --profile default

# Refatoração (foco em Decision History)
codex --profile refactor

# Security audit (foco em patterns de segurança)
codex --profile security-audit

# Prototipagem rápida (ainda respeita anti-patterns)
codex --profile fast-iteration
```

### Estratégia 2: Ancoragem de Contexto

No `memory_instruction.md`, use a **Seção 9 (Context Anchors)** para criar links rápidos:

```markdown
## 9. CONTEXT ANCHORS
### Para Feature X
- Design Doc: docs/feature_x_design.md
- Migration Script: scripts/migrate_x.py
- Related Tests: tests/integration/test_x.py
```

Isso permite que Codex encontre arquivos relacionados instantaneamente.

### Estratégia 3: Recovery Protocols

Se Codex parecer "perdido", use o protocolo documentado:

```bash
codex

# Você percebe que Codex está inconsistente
"I think you're missing context. Please re-read memory_instruction.md and confirm:
1. Current feature we're working on
2. Expected outcome
3. Any constraints"

# Codex vai:
# 1. Re-ler o arquivo
# 2. Extrair informações da Seção 3 (Active Work)
# 3. Sincronizar com você
```

---

## 📊 Métricas de Sucesso

### Como Saber Se Está Funcionando

| Métrica | Antes (Sem Memória) | Depois (Com Memória) |
|---------|---------------------|----------------------|
| **Context Loss** | A cada sessão | Quase zero |
| **Repetição de Info** | Constante | Rara |
| **Consistência de Código** | 60-70% | 95%+ |
| **Tempo de Onboarding** | 5-10 min/sessão | <1 min |
| **Detecção de Anti-Patterns** | Manual | Automática |

### Sinais de Que Está Funcionando
- ✅ Codex menciona ADRs sem você perguntar
- ✅ Sugere padrões documentados em `memory_instruction.md`
- ✅ Evita anti-patterns automaticamente
- ✅ Continua trabalho de sessões anteriores sem explicação extra

### Sinais de Problema
- ❌ Codex não menciona `memory_instruction.md`
- ❌ Repete perguntas sobre arquitetura básica
- ❌ Sugere patterns já documentados como anti-patterns
- ❌ Não encontra o arquivo (verificar path)

**Solução:** Execute `codex config show --effective` e verifique se `developer_instructions` está presente.

---

## 🔧 Troubleshooting

### Problema 1: "Codex não está lendo o arquivo"

**Sintomas:**
- Codex não menciona `memory_instruction.md`
- Comportamento inconsistente

**Diagnóstico:**
```bash
# Verificar se arquivo existe
ls -la py_rme_canary/docs/memory_instruction.md

# Verificar se Codex está no diretório correto
pwd
# Deve estar em py_rme_canary/ ou subdiretório

# Verificar config
codex config show --effective | grep developer_instructions
```

**Solução:**
```bash
# Se arquivo não existe
cp [artifact-7-content] py_rme_canary/docs/memory_instruction.md

# Se path está errado, use path absoluto no config.toml
developer_instructions = """
READ: /full/path/to/py_rme_canary/docs/memory_instruction.md
"""
```

### Problema 2: "Codex encontra arquivo mas não segue instruções"

**Causa:** `developer_instructions` muito longo pode ser truncado.

**Solução:**
```toml
# Em vez de colocar TUDO no developer_instructions,
# use referência simples:
developer_instructions = """
READ AND FOLLOW: py_rme_canary/docs/memory_instruction.md
This file contains all project context, standards, and protocols.
"""
```

### Problema 3: "Memory instruction.md fica desatualizado"

**Solução:** Adicione ao seu `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Lembrar de atualizar memória em commits grandes
if git diff --cached --stat | grep -q "src/"; then
  echo "⚠️  REMINDER: Update docs/memory_instruction.md if this changes architecture"
fi
```

---

## 📚 Exemplos Práticos

### Exemplo 1: Nova Feature Completa

```bash
# === SESSÃO 1: Planejamento ===
codex --profile default

"I want to add user authentication with JWT. 
Check memory_instruction.md for existing auth patterns."

# Codex vai:
# 1. Ler memory_instruction.md
# 2. Encontrar Seção 2 (ADR sobre auth module)
# 3. Ver estrutura existente em auth/
# 4. Propor implementação consistente

# === SESSÃO 2: Implementação ===
codex --profile default

"Continue the JWT implementation"

# Codex automaticamente:
# 1. Re-lê memory_instruction.md
# 2. Encontra trabalho em progresso
# 3. Continua de onde parou

# === SESSÃO 3: Atualizar Memória ===
codex --profile default

"JWT implementation is complete. Update memory_instruction.md with:
- New ADR
- Usage examples
- Security considerations"

# Codex vai atualizar o arquivo com novo ADR
```

### Exemplo 2: Code Review Automático

```bash
codex --profile security-audit

"Review this pull request for security issues.
Use memory_instruction.md for our security standards."

# Codex vai verificar contra:
# - Seção 5: Forbidden Patterns
# - Seção 4: Error Handling Pattern
# - Seção 7: Verification Commands (bandit)
```

### Exemplo 3: Onboarding Novo Dev

```bash
# Novo desenvolvedor começa no projeto
codex

"I'm new to this project. Give me an overview based on memory_instruction.md"

# Codex vai extrair e resumir:
# - Seção 1: Project Identity & Architecture
# - Seção 2: Decision History (contexto de por que as coisas são assim)
# - Seção 4: Coding Standards
# - Seção 9: Context Anchors (onde encontrar mais info)
```

---

## 🎯 Próximos Passos

1. **✅ Criar `memory_instruction.md`** (copiar Artifact #7)
2. **✅ Atualizar `config.toml`** (copiar Artifact #6)
3. **⚠️ Testar sistema** (rodar Testes 1-4 acima)
4. **📝 Fazer primeira atualização** de memória com decisão real
5. **🔄 Estabelecer rotina** de atualização semanal/por milestone

---

## 📖 Recursos Adicionais

### Documentação Oficial
- Config reference: https://developers.openai.com/codex/config-reference
- Developer instructions: https://developers.openai.com/codex/guides/agents-md

### Templates Úteis
- **ADR Template:** Use na Seção 2 de `memory_instruction.md`
  ```markdown
  ### [YYYY-MM-DD] Título da Decisão
  - **Context:** Por que precisamos decidir
  - **Decision:** O que decidimos
  - **Consequences:** Impacto esperado
  - **Rollback Plan:** Como reverter
  ```

- **Active Work Template:** Use na Seção 3
  ```markdown
  **Feature:** Nome da Feature
  - **Branch:** feature/nome
  - **Status:** X% complete
  - **Blocker:** Descrição do blocker
  - **Next Steps:** Lista de próximas ações
  ```

---

**Sistema de memória configurado! 🧠✨**

Agora o Codex tem "memória de longo prazo" e não vai se perder entre sessões.
---

## ACTIVE WORK (auto-updated)

### [2026-01-14] Legacy parity implementation started
- Implemented: mirror drawing refactor in `vis_layer/ui/canvas/widget.py` using shared logic; added unit tests for mirroring.
- Next: implement missing legacy brushes (Wall/Carpet/Table) parity checks and wiring, then start Live collaboration (`live_socket`/`live_peer`) with basic integration.

### [2026-01-14] Wall/Carpet/Table parity update
- Implemented: wall-like neighbor expansion for carpet/table auto-border; added unit tests for carpet/table stacking rules.
- Updated: phase4 verifier keywords to detect wall/carpet/table implementations.
- Next: start Live collaboration base (live_socket/live_peer) and OTMM I/O skeleton.

## MEGA TODOs (one-shot backlog)
- Live: port LiveSocket/LivePeer from legacy, wire basic sync into EditorSession, add packet handlers + tests.
- OTMM: ✅ COMPLETE - loader + saver + roundtrip tests passing.
- Render: complete MapDrawer + DrawingOptions layer toggles; minimal OpenGL render path for tiles.
- UI: ✅ PySide6 stubs moved to _experimental; tileset window PyQt6 implementation pending.
- Search/Replace: advanced search modes + replace on selection parity + results export.
- Cleanup: ✅ data_layer already removed; brushes.py is now valid data container (not stub).
- Quality: DONE quality-pipeline --apply (unit + UI tests). Missing: sonar-scanner + shellcheck in env; confirm normalized issue backlog and update status docs if needed.

### [2026-01-14] Live collaboration base (MVP)
- Implemented: LiveSocket + LivePeer base classes; LiveServer now uses LivePeer and broadcasts TILE_UPDATE.
- Implemented: LiveClient now inherits LiveSocket; EditorSession handles TILE_UPDATE without rebroadcast loop.
- Next: implement OTMM saver + roundtrip tests.

### [2026-01-14] OTMM detection + placeholder loader
- Implemented: detect .otmm magic; added OTMM loader entry with explicit error and OTBM fallback for mislabeled files.
- Added: unit tests for map detection and OTMM error path.
- Next: implement OTMM saver + roundtrip tests.

### [2026-01-14] OTMM loader (read)
- Implemented: OTMM constants + NodeFile-based loader for tiles/items/towns/houses/spawns with warnings + memory guard.
- Added: unit test for OTMM tile/item parsing, regression test for legacy U16 house payloads, town/spawn data parsing tests, plus unknown item placeholder + empty node coverage.
- Next: run quality pipeline when env is ready.

### [2026-01-14] OTMM saver (write)
- Implemented: OTMM serializer + atomic save with items/tiles/towns/houses/spawns; aligned house town/rent/beds to legacy U16 and loader accepts U16/U32 house payloads.
- Added: OTMM serialize->load roundtrip unit test.
- Next: run quality pipeline (black/isort/mypy/pytest).

### [2026-01-15] OTMM saver byte ordering fix + UI cleanup
- **Fixed:** Critical bug in `otmm_saver.py` - ground_id was written AFTER tile_flags, but loader expects ground_id FIRST. This caused roundtrip test failures with corrupted tile data (ground.id read as 4609 instead of 111).
- **Moved:** PySide6 experimental files (`dialogs.py`, `tileset.py`) to `vis_layer/ui/_experimental/` with deprecation warnings and README.
- **Verified:** All 19 unit tests pass, including OTMM roundtrip test.
- **Completed:** TODO_EXPENSIVE EPIC P1 "Isolate or remove UI experimental (Tkinter + PySide6)"
- **Status:** P0 items (mirror, data_layer, brushes.py, tests) verified as complete. P1 UI cleanup done.
- **Next:** OTBM attribute parity audit (P1) or brush footprint/borders parity (P1).

### [2026-01-15] OTBM Attribute Parity + Type Annotations Fix
- **Audited:** OTBM attribute parity between Python and C++ legacy - confirmed excellent parity (all RME-used attributes implemented)
- **Added:** Warning callback for unknown OTBM item attributes in `core/io/otbm/item_parser.py` (line ~268)
- **Added:** Server-side attribute constants (DURATION, DECAYING_STATE, WRITTENDATE, etc.) to `core/constants/otbm.py` for documentation/future compatibility
- **Fixed:** Return type annotations in `core/protocols/live_client.py` and `live_server.py` (13 methods)
- **Fixed:** `LiveClient.send_packet()` return type to match `LiveSocket.send_packet()` signature (bool instead of None)
- **Fixed:** SelectionApplyMode exhaustive check in `logic_layer/session/selection.py`
- **Verified:** All 19 unit tests passing
- **Verified:** mypy errors reduced from 13 to 3 (remaining are false-positive "unreachable" enum checks)
- **Status:** P1 OTBM attribute audit complete. Type safety improved.
- **Next:** Brush footprint/borders parity (P1) or MapDrawer/OpenGL render layer (P1).

### [2026-01-15] Brush Footprint Parity + DrawingOptions/MapDrawer Implementation
- **Validated:** Brush footprint/borders parity with C++ legacy in `logic_layer/geometry.py`:
  - Square shape: (2*size+1)² formula matches C++ exactly
  - Circle shape: distance formula with ±0.005 tolerance matches C++
  - Border ring calculation validated for both shapes
- **Created:** 59 new brush footprint tests in `tests/unit/logic_layer/test_brush_footprint.py`
- **Created:** `logic_layer/drawing_options.py` - Qt-free DrawingOptions dataclass:
  - 30+ toggle fields matching C++ legacy (`source/editor.h` DrawingOptions struct)
  - `set_default()`, `set_ingame()` methods for presets
  - `is_only_colors()`, `is_tile_indicators()`, `is_tooltips()` query methods
  - Change notification callback system
- **Created:** `vis_layer/renderer/map_drawer.py` - MapDrawer render coordinator:
  - `RenderBackend` protocol for abstraction (QPainter/OpenGL)
  - `MapDrawerViewport` dataclass for view state
  - Decision methods: `should_draw_grid()`, `should_draw_creatures()`, etc.
  - `draw(backend)` main entry point (ready for backend implementation)
- **Created:** `vis_layer/renderer/drawing_options_coordinator.py` - Qt ↔ DrawingOptions bridge:
  - Two-way sync between QtMapEditor attributes and DrawingOptions
  - Action checkbox state synchronization
  - Automatic canvas repaint on option change
- **Added:** 11 new DrawingOptions unit tests
- **Verified:** All 89 unit tests passing (was 19 → 78 → 89)
- **Status:** P1 Brush footprint parity ✅ COMPLETE. P1 MapDrawer/DrawingOptions ✅ COMPLETE.
- **Next:** Quality polish (ruff, mypy, CONTRIBUTING.md) or wire coordinator into QtMapEditor.

### [2026-01-15] DrawingOptions wiring + quality pipeline attempt
- **Implemented:** wired DrawingOptionsCoordinator into QtMapEditor init; view toggle handlers now sync DrawingOptions on change.
- **Attempted:** ran `quality-pipeline/quality.sh` under WSL; failed to execute Windows `python.exe` (Exec format error). SonarScanner/ShellCheck missing warnings.
- **Next:** rerun quality pipeline in a Windows-compatible bash (Git Bash/MSYS2) or install WSL Python + ruff/mypy/radon/sg, then fix any reported issues.

### [2026-01-15] Quality pipeline dry-run + test verification (Windows)
- **Executed:** `quality-pipeline/quality.sh --dry-run --verbose` via Git Bash with .venv on PATH (deps OK).
- **Observed:** Ruff reported 1433 issues; Radon reported 190 functions > 10; Sonar ran in local mode; issues normalized; report generated.
- **Verified:** `python -m pytest` passed (127 tests).
- **Next:** decide whether to run `quality.sh --apply` or scope down the ruff/radon backlog; update CHANGELOG.md + IMPLEMENTATION_STATUS.md.

### [2026-01-15] Docs update for parity/quality status
- **Updated:** `docs/CHANGELOG.md` with quality pipeline fixes, Python 3 tooling update, and type-safety notes.
- **Updated:** `docs/IMPLEMENTATION_STATUS.md` to mark OTMM + DrawingOptions complete and clarify Live Server/Client as partial.
- **Next:** pick a scope for the Ruff/Radon backlog or run `quality.sh --apply` after confirming desired scope.

### [2026-01-16] Quality pipeline apply + UI smoke fixes
- **Fixed:** added missing `QTabWidget` import for FindEntityDialog in `vis_layer/ui/main_window/dialogs.py`.
- **Updated:** `quality-pipeline/quality.sh` now detects `.exe` tools (python/ruff/mypy/radon/sg) in Git Bash PATH.
- **Executed:** `quality-pipeline/quality.sh --apply --verbose` via Git Bash; unit + UI tests passed. SonarScanner/ShellCheck missing (non-blocking).
- **Next:** review normalized issues report and decide whether to tackle remaining TODO_EXPENSIVE items or quality backlog.

### [2026-01-19] Implementation status corrections (brush parity)
- **Updated:** `docs/IMPLEMENTATION_STATUS.md` to reflect MVP/virtual brush parity (Table/Carpet/Door/House/Waypoint/Monster/Npc/Spawn/Flag/Zone/OptionalBorder/Eraser) and fixed obsolete doc links to `TECHNOLOGY_IMPLEMENTATION_DETAILS.md`.
- **Next:** choose next implementation priority (render backend vs QGraphicsScene benchmark).

### [2026-01-19] MapDrawer integration (QPainter backend)
- **Implemented:** `vis_layer/renderer/qpainter_backend.py` and wired `MapDrawer` into `vis_layer/ui/canvas/widget.py` with QPainter rendering and indicator overlay preservation.
- **Updated:** `vis_layer/renderer/map_drawer.py` color hashing to match minimap colors; `docs/IMPLEMENTATION_STATUS.md` High-Priority TODOs split into MapDrawer integration (done) vs OpenGL backend (pending).
- **Next:** implement OpenGL backend for MapDrawer (tile sprites + batching).

### [2026-01-19] MapDrawer OpenGL backend (tile sprites + batching)
- **Implemented:** `vis_layer/renderer/opengl_backend.py` with shader-based batching (color quads, lines, sprite runs) and sprite texture cache.
- **Wired:** `vis_layer/renderer/opengl_canvas.py` now drives `MapDrawer` using the OpenGL backend with viewport sync + fallback handling; added `_sprite_bgra_for_server_id` in `vis_layer/ui/main_window/qt_map_editor_assets.py` for texture uploads.
- **Updated:** `docs/IMPLEMENTATION_STATUS.md` marked OpenGL backend as complete.
- **Next:** decide whether to switch main canvas to OpenGL or keep QPainter as default; validate OpenGL render parity against legacy.

### [2026-01-19] Event-driven map rendering parity (legacy ARCHITECTURE.md)
- **Implemented:** event compression + input coalescing in `vis_layer/ui/canvas/widget.py` (flags `is_rendering`, `render_pending`, `pending_zoom_step`, `HARD_REFRESH_RATE_MS`).
- **Added:** optional `AnimationTimer` (100ms) tied to `show_preview` + zoom threshold, mirroring legacy refresh behavior.
- **Extended:** `vis_layer/renderer/opengl_canvas.py` now uses the same event-driven refresh compression + animation timer for OpenGL rendering.
- **Updated:** `docs/IMPLEMENTATION_STATUS.md` notes MapCanvasWidget event-driven parity.
- **Next:** validate redraw frequency (idle vs active) and decide whether to wire OpenGLCanvasWidget into the main UI.

### [2026-01-19] OpenGLCanvasWidget promoted to main canvas
- **Implemented:** OpenGL canvas now handles full map interactions (mouse, selection, wheel zoom) and draws overlays (indicators + selection) via QPainter.
- **Updated:** `QtMapEditor` now instantiates `OpenGLCanvasWidget` as the central canvas.
- **Updated:** `docs/IMPLEMENTATION_STATUS.md` notes OpenGLCanvasWidget as the primary canvas.
- **Next:** validate OpenGL/QPainter fallback parity and confirm no interaction regressions.

### [2026-01-19] Tooling parity + quality pipeline
- **Added:** `pyproject.toml` with Ruff/Mypy config (py312, line-length 120, excludes vis_layer/tools) to satisfy quality pipeline expectations.
- **Updated:** `quality-pipeline/quality.sh` normalization step now tolerates non-dict radon entries and missing ast-grep output; reran `quality.sh --dry-run --verbose` with sonar-scanner, ruff, mypy, radon, sg all discovered in PATH.
- **Fixed:** `BrushSettings.apply_brush_with_size` now typed (Callable[..., list[Any]]); mypy baseline clean again.
- **Added:** `.gitignore` entries for `.agent/` and `Remeres-map-editor-linux-4.0.0/` to avoid committing local agent metadata and legacy reference tree.
- **Note:** Latest `quality.sh` dry-run completes; 576 Ruff issues and 183 high Radon CC remain; Sonar ran without token (local mode).

### [2026-01-19] Quality pipeline refactor - Fase 1 start
- **Added:** `tools/quality_scripts/index_symbols.py` and `normalize_issues.py`; `quality.sh` now calls these external scripts and detects `uv` for faster installs.
- **Added:** `QUALITY_TODOS.md` summarizing pipeline rollout (Semanas 1-6 + opcionais) and `.pre-commit-config.yaml` with ruff/mypy/radon/shellcheck hooks.
- **Adjusted:** `quality.sh` paths now resolve scripts via `QUALITY_SCRIPTS_DIR`; duplicate headers cleaned.
- **Next:** Finish Fase 1 items (run pre-commit install/run, uv setup test), then parallel/cache (Fase 2) and Taskfile migration (Fase 3).

### [2026-01-19] Quality pipeline CRLF cleanup + uv verified
- **Fixed:** `quality.sh` rewritten with LF endings; ShellCheck now only warns about placeholder `PYTHON_INSTALL_CMD` (silenced via SC2034 disable).
- **Verified:** `quality.sh --dry-run --verbose` passes with uv detected in PATH; outputs 576 Ruff issues / 184 Radon high CC / 0 mypy errors; Sonar runs without token (local).
- **Updated:** `QUALITY_TODOS.md` checkboxes for completed Fase 1 items.

### [2026-01-19] Quality pipeline Phase 2 — parallel baseline & cache
- **Implemented:** `run_baseline` wrapper that forks into parallel workers if GNU Parallel is installed, falling back to sequential baseline otherwise, and logs cache hits/misses via `run_with_cache`.
- **Added:** `tools/quality_scripts/hash_python.py` to fingerprint the Python tree; caching wrappers now reuse Ruff/Mypy/Radon outputs whenever sources unchanged (two dry-run runs show cache hits).
- **Note:** `QUALITY_TODOS.md` now tracks Phase 2 progress (parallel baseline + caching done, install Parallel/time measurement pending); Stage 2 still logs GNU Parallel as missing so sequential path used.

### [2026-01-19] Quality pipeline Phase 3 — Task migration groundwork
- **Added:** `Taskfile.yml` as a Task-based orchestration entrypoint covering `setup`, `quality:check`, `quality:fix`, individual tool checks, `tests` group, `clean`, and `snapshot`.
- **Updated:** `QUALITY_TODOS.md` checkboxes now reflect Task tasks (cleanup/snapshot tasks already wired, Taskfile created, per-tool tasks ported; Task binary install + Task run still pending).
- **Next:** Install `task` (Go 1.19+) and run `task quality:check` to validate the Task-based workflow; document Task usage in README once onboarding is complete.

