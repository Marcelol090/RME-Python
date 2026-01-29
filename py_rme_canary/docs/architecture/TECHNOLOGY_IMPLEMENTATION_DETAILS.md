# Implementation.md

> ⚠️ **Redundância removida:**
> The master checklist is now in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md). This file contains only deep-dive comparative analysis and technical context. For actionable status, use the master checklist.

# Análise Comparativa: Funcionalidades Faltantes no py_rme_canary
## 📝 Contexto Técnico
Este documento compara detalhadamente o código C++ original (`source/`) com a implementação Python (`py_rme_canary/`). Foca em identificar funcionalidades faltantes ou incompletas, com explicações técnicas e recomendações para agentes e contribuidores.
**Data da Análise:** 2026-01-05
**Versão C++:** Remere's Map Editor (Canary)
**Versão Python:** py_rme_canary
---
## 🏁 Funcionalidades: Resumo e Status (✓ Implementado, ✗ Faltando)
### 1. Brushes
- ✓ GroundBrush, WallBrush, Auto-border básico, BrushManager, BrushFactory
- ✓ FlagBrush (virtual / metadata-only), ZoneBrush (virtual / metadata-only), HouseBrush (virtual / metadata-only), EraserBrush (básico)
- ✓ DoodadBrush (MVP+): aba Doodad usa brushes reais do materials XML (quando disponíveis) via IDs virtuais; suporta alternates, itens com chance e composites multi-tile (determinístico) + flags `on_duplicate` e `one_size`. Alt remove seguindo a mesma seleção.
- ✓ OptionalBorderBrush (MVP / virtual): pinta/limpa “loose gravel” (carpet id 6373) via ferramenta na paleta Terrain.
- ✓ Formas (square/circle) + Tamanho (brush_size) aplicados via offsets no canvas (inclui ring de auto-border)
- ✓ CarpetBrush (auto-border via `brushes.json` keys NORTH/EAST/SOUTH/WEST + CORNER_*; não clobbera itens acima; detecta carpet mesmo quando não é top item)
- ✓ TableBrush (MVP): brush_type `table` (JSON) com placement family-aware (não clobbera itens) + auto-border via borders do brush
- ✓ HouseExitBrush (MVP / virtual): na paleta House, itens "Exit: <id>" setam a entry do house no tile clicado (requer ground e não estar dentro de house tile). Alt limpa a entry. Undo/redo via HouseEntryAction.
- ✓ WaypointBrush (MVP / virtual): na paleta Waypoint, entradas existentes movem o waypoint para o tile clicado (requer tile existir). Alt deleta. Sem drag/smear. Undo/redo via WaypointAction.
- ✓ MonsterBrush/NpcBrush/SpawnMonsterBrush/SpawnNpcBrush (MVP / virtual): paletas Creature/Npc listam criaturas via `data/creatures/*.xml`; ferramentas criam/deletam spawn areas (radius=brush_size); Monster/Npc agora suporta drag/smear para add/delete de entries por múltiplos tiles (Alt remove) com 1 undo por gesto.
- ✓ DoorBrush (MVP+): ferramentas na paleta Terrain (Normal/Locked/Magic/Quest/Window/Hatch). Clique/drag usa door defs do materials (wall -> door por alinhamento) quando disponivel; fallback para porta "default" via `items.xml` se nao houver specs. Nao alterna open/closed; use "Switch Door" para toggling. Alt remove a porta do topo. 1 undo por gesto.
- ✓ Variação (MVP): estado Qt-free `brush_variation` + controle na toolbar (Sizes: `Var:`). No momento, afeta brushes **ground** que definem `randomize_ids` (seleção determinística entre id principal + variantes).
- ✓ Espessura (MVP / Doodad): estado Qt-free de thickness + controle na toolbar (Sizes: `Thickness` + `T:` 1..10). No momento, afeta **doodad** como controle de densidade (probabilidade) na footprint.
- ✗ Drag/Smear (geral), Border Builder, Border Groups, Border Friends/Hate, Border Equivalents
- ✓ Recentes (MVP): aba “Recent” na paleta lista os últimos brushes selecionados (inclui virtuais); dedupe e limite.
### 2. Editor e Sessão
- ✓ Sessão básica, seleção, clipboard, undo/redo, mouse gestures, mover seleções
- ✓ Modos de seleção (box selection apply modes: replace/add/subtract/toggle por modificadores)
- ✓ duplicar, mover up/down, limpar seleção, borderize
- ✓ clear modified tiles (Clear Modified State)
- ✓ randomize (selection/map; opt-in via `randomize_ids` no `brushes.json`)
- ✓ clear invalid tiles (selection/map; remove placeholders/unknown replacements id==0/raw_unknown_id)
- ✓ Waypoints: set/delete (Edit -> Tools) com undo/redo (map-level)
- ✓ Houses: set/clear House ID on selection (Edit -> Tools) com undo/redo
- ✓ Spawns: set/delete Monster/NPC spawn areas at cursor (Edit -> Tools) com undo/redo
- ✓ Spawns: add/delete Monster/NPC entries at cursor (Edit -> Tools) com undo/redo (precisa de uma spawn area cobrindo o cursor)
- ✓ Towns: add/edit/delete + set temple position (Edit -> Tools) com undo/redo; OTBM load/save
- ✓ Houses (definições): add/edit/delete + set entry (Edit -> Tools) com undo/redo; default `header.housefile="houses.xml"` se vazio
- ✓ Zones (definições): add/edit/delete (Edit -> Tools) com undo/redo; default `header.zonefile="zones.xml"` se vazio
- ✓ queue de ações + tipos de ações (ActionType + SessionActionQueue)
- ✗ network queue
### 3. Renderização
- ✓ Canvas PyQt6, renderização básica de tiles, viewport com zoom, minimap básico
- ✓ Sistema de sprites (sheets decode básico + cache LRU limitado por MemoryGuard; pixmap cache com eviction + fallback de emergência)
- ✗ OpenGL context/drawer completo (layers, sombra, seleção, grid, previews), animações, DrawingOptions detalhados, light drawer, screenshots
### 4. Live Server/Client (Faltante)
- ✗ Server, client, socket, peer, gui, logs, chat
### 5. Importação/Exportação
- ✓ OTBM básico, XML básico (houses, spawns, zones)
- ✗ Importar mapas diversos, monsters, npcs, minimap, exportar minimap/tilesets, OTMM, conversão OTBM, auto-detecção de versão
### 6. Busca/Substituir
- ✓ Busca de itens/waypoints, estatísticas
- ✗ Busca/replace avançado, seleção, criaturas, duplicados
### 7-30. Outras (Toolbars, Menu, Hotkeys, Tilesets, About, Backup, Conversão, Database, etc)
- ✓ Alguns núcleos (paleta, config, database, minimap, indicadores)
- ✗ Funcionalidades e janelas específicas (paletas completas, propriedades, navegadores, hotkeys, preferências, toolbars, templates, backup, conversão, complex items, etc)
## 📊 Estatísticas Resumidas
| Categoria | ✓ | ✗ | % |
|---------------------|---|---|----|
| Brushes | 4| 20| ~15|
| Editor/Sessão | 6| 15| ~30|
| Renderização | 3| 25| ~10|
| Live Server/Client | 0| 20| 0|
| Import/Export | 3| 10| ~25|
| Busca/Substituir | 3| 15| ~15|
Total: **~30 implementados**, **200+ faltam**, **~13% concluído**
## 🎯 Prioridades
**Alta:**
- Sistema de Brushes
- Renderização OpenGL
- Sistema de Ações (undo/redo robusto)
- Busca & Substituir
- Propriedades/edição de entidades
**Média:** Import/Export, Paleta, Preferências, Navegação, Limpeza
**Baixa:** Live, Templates, Tilesets, Welcome/About, Toolbars extras
## 🧪 Qualidade de Código (Type Hints/Mypy, Ruff)
### ruff (`pyproject.toml`)
```toml
[tool.ruff]
target-version = "py312"
line-length = 120
extend-exclude = ["py_rme_canary/vis_layer/**","py_rme_canary/tools/**"]
[tool.ruff.lint]
select = ["F", "E", "W", "I", "N", "UP", "B", "C4", "SIM"]
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```
### mypy (`pyproject.toml`)
```toml
[tool.mypy]
python_version = "3.12"
disallow_untyped_defs = true
check_untyped_defs = true
ignore_missing_imports = false
warn_unused_ignores = true
warn_redundant_casts = true
warn_unreachable = true
no_implicit_optional = true
exclude = ["py_rme_canary/vis_layer/","py_rme_canary/tools/"]
```
**Cobertura de type hints:** ~70%. Melhorar para 95%+ em novas funções. Diminuir exclusões gradativamente.
**Exemplo de type hints otimizados**
```python
from __future__ import annotations
from typing import Callable, TypedDict
TileKey = tuple[int, int, int]
TilesChangedCallback = Callable[[set[TileKey]], None]
class LoadReport(TypedDict):
success: bool
errors: list[str]
# Função tipada
def process_tiles(tiles: list[Tile]) -> None:
...
```
**Recomendações:**
- Type hints em todas as funções públicas.
- Usar tipos built-in (list, dict) no Python 3.12.
- Seguir arquitetura (core/logic_layer/vis_layer).
- Menos exclusão em Mypy; habilitar regras extras em Ruff.
- Adotar hooks pre-commit e CI/CD (`ruff`, `mypy`).
## 🏗️ Arquitetura Atual
- `core/`: tipos, I/O, serialização
- `logic_layer/`: edição, lógica
- `vis_layer/`: interface (render, widgets)
## ✔️ Checklist
- [x] Habilitar regras extras Ruff
- [ ] Cobrir funções com type hints
- [ ] Reduzir exclusões Mypy
- [x] Adotar pre-commit/CI
- [x] Documentar e testar funções novas

## 🧩 Próximos TODOs (prioridade alta / opções sugeridas)
- [x] Drag/Smear: infraestrutura de gesto (stroke-like) para brushes especiais, mantendo 1 undo por gesto. (Creature/Npc: ✓ smear MVP; DoorBrush: ✓ smear MVP; generalizado via gesto batched de posições.)
- [x] Variação (MVP): `brush_variation` + UI (toolbar) + seletor determinístico para ground brushes com `randomize_ids`.
- [x] Espessura (MVP / Doodad): controle simples (toolbar) + estado Qt-free; aplicado como densidade probabilística na footprint do doodad.
- [x] Recentes: lista de brushes recentes (UI + persistência leve).

## 🧩 TODO Extenso (Prioridade Máxima)

### Renderização (backend moderno)

**Meta:** substituir o render “básico” por um pipeline com layers, grid, seleção, previews e efeitos (paridade com legacy), sem violar a arquitetura (Qt-free em `core/` e `logic_layer/`; somente `vis_layer/` conversa com Qt/GPU).

#### OpenGL (recomendado primeiro)
- [ ] Definir o *contrato* Qt-free de render: uma lista de “draw commands” (tiles, sprites, overlays) gerada a partir do estado do mapa/viewport.
- [ ] Implementar um `RenderModel` Qt-free (cache de sprites/ids visíveis por viewport, ordenação de layers, regras de z-order Tibia-like).
- [ ] Criar um `OpenGLCanvas` na `vis_layer/` (ex.: QOpenGLWidget/QOpenGLWindow) e um renderer que consome os draw commands.
- [ ] Portar layers essenciais: ground, borders, items, creatures (quando existirem), selection highlight, grid, tool preview.
- [ ] Implementar `DrawingOptions` mínimos: toggles de grid/selection/creatures/items, debug overlays.
- [ ] Implementar animações básicas (quando sprites suportarem) sem quebrar cache/MemoryGuard.
- [ ] Validar performance: pan/zoom fluido (60fps alvo), sem travar UI (streaming de tiles visíveis).

#### Vulkan (exploração)
- [ ] Levantar viabilidade de Vulkan no stack atual (PyQt6 + bindings) e custos de manutenção.
- [ ] Se viável, definir um backend alternativo que consuma o mesmo `RenderModel`/draw commands.

#### DirectX (exploração)
- [ ] Levantar viabilidade de DirectX no stack atual (Windows) e custos de manutenção.
- [ ] Se viável, definir um backend alternativo que consuma o mesmo `RenderModel`/draw commands.

### Qualidade (prioridade máxima: Ruff/Mypy/Typing)

#### Ruff (incremental)
- [ ] Expandir regras do Ruff em `pyproject.toml` (ex.: E/W/I/N/UP/B/C4/SIM) e corrigir por etapas (começar por imports/format).
- [ ] Definir `per-file-ignores` mínimos e justificar exceções.
- [x] Garantir `ruff` + `ruff-format` via pre-commit.

#### Mypy (incremental)
- [x] Trocar `ignore_missing_imports=true` por abordagem mais restritiva (somente libs específicas) e reduzir falsos positivos.
- [x] Ligar `check_untyped_defs=true` para módulos novos/refatorados primeiro.
- [x] Reduzir `exclude` gradualmente: `py_rme_canary/tools/` agora incluído no mypy (mantendo `py_rme_canary/vis_layer/` excluído por enquanto).

#### Type hints (incremental)
- [ ] Aumentar cobertura em `core/` e `logic_layer/` para 95%+ (priorizar APIs públicas e código novo).
- [x] Tornar `disallow_untyped_defs=true` inicialmente só para `core/` e `logic_layer/` (e liberar `vis_layer/`).

Obs.: nesta etapa, `disallow_untyped_defs` e `check_untyped_defs` foram habilitados via overrides do mypy para `core/`, `logic_layer/` e `tools/`.

#### Dev workflow
- [x] Adotar pre-commit/CI (ruff/mypy/compileall).

## 🧩 TODO Extenso (Doodad + outra prioridade)

### Doodad (paridade com C++ / materiais XML)
- [x] Validar parsing completo de `data/materials/brushs/*.xml` (inclui arquivos grandes e nomes com caracteres inválidos) + registrar warnings amigáveis.
- [x] Cobrir atributos adicionais do doodad: `draggable`, `on_blocking`, `redo_borders` (definir semântica no Python e onde aplicar).
- [x] Implementar semântica de thickness baseada no próprio brush (ex.: `thickness="12/100"`) combinada com o override da toolbar (`Thickness/T:`).
- [x] Refinar escolha determinística: alinhar com legacy. (MVP: alternates são selecionados por `brush_variation`, e a escolha de item/composite é determinística por posição.)
- [x] Melhorar remoção (Alt): opção de remover “qualquer item do brush” no tile (quando múltiplos ids) vs remover apenas o id escolhido.
- [x] Tratar composites com múltiplos itens por tile: suportar stacks explícitas (todos) vs variações (chance -> escolhe um).
- [x] Otimizar performance: cache de doodad specs e parsing lazy/assíncrono (sem travar UI ao abrir editor) se necessário.
- [x] Adicionar validações in-memory para:
	- [x] alternates por `brush_variation` (determinístico)
	- [x] pick ponderado por chance (estável por posição)
	- [x] composites multi-tile (aplica offsets e z)
	- [x] `on_duplicate` (bloqueia/permite duplicatas)
	- [x] `one_size` (ignora footprint)

### Outra prioridade: Drag/Smear (geral)
- [x] Generalizar infraestrutura “1 undo por gesto” para brushes/tooling especiais (reaproveitar padrão de Creature/Npc e DoorBrush).
- [x] Definir contrato comum: como um tool acumula posições/mutações e comita uma única ação (tile-level e metadata-level).
- [x] Aplicar a generalização em pelo menos 1 brush adicional (além de Creature/Npc e Door), para validar arquitetura. (SpawnMonster/SpawnNpc agora aceitam drag/smear para criar/deletar múltiplas spawn areas por gesto.)

---

## ✅ Atualizações Recentes (2026-01-05)
- Implementado MemoryGuard opcional (soft/hard) com config via env + `data/memory_guard.json`.
- OTBM loader: validação pré-load (tamanho do arquivo) + checks incrementais (tiles/items).
- Cache de sprites/pixmaps: LRU com eviction agressiva em hard limit; fallback de emergência desativa sprites temporariamente (editor nunca cai por pixmap).
- Brushes metadata-only: Flag/Zone virtuais (sem editar `brushes.json`) + seleção considera tiles com metadata como não-vazios.
- Auto-border wall-like: suporte a aliases de keys do `brushes.json` (END_* ⇄ NORTH/EAST/SOUTH/WEST), destravando carpet/table-like básicos.
- CarpetBrush: escrita/borderize agora substitui apenas a família do carpet e preserva itens acima (sem sobrescrever o top item).
- Tiles modified-state: Tile.modified (runtime-only) + "Only show modified" funcional + ação "Clear Modified State" (Window menu).
- Editor/Sessão: Action queue/types (Qt-free) integrado no EditorSession.
- Tools: "Clear Invalid Tiles" (selection/map) + "Randomize" (selection/map) com undo + UI (Edit -> Tools).
- Undo/Redo: HistoryManager generalizado para aceitar ações não-tile (metadata) via interface `describe/undo/redo`.
- Tools: Waypoints "Set Waypoint Here..." + "Delete Waypoint..." (Edit -> Tools) com undo/redo.
- Tools: Houses "Set House ID on Selection..." + "Clear House ID on Selection" (Edit -> Tools) com undo/redo.
- Tools: Houses metadata "Add/Edit House...", "Set House Entry Here...", "Delete House..." (Edit -> Tools) com undo/redo; ao criar/editar a primeira definição, se o header não tiver `housefile`, usa default `houses.xml` para permitir persistência no bundle save.
- Tools: Spawns "Set/Delete Monster Spawn Here" e "Set/Delete NPC Spawn Here" (Edit -> Tools) com undo/redo; ao criar o primeiro spawn, se o header não tiver arquivo externo definido, usa defaults `spawns.xml`/`npcspawns.xml` para permitir persistência no bundle save.
- Tools: Spawns entries "Add/Delete Monster Here..." e "Add/Delete NPC Here..." (Edit -> Tools) com undo/redo; adiciona/remova entradas no tile do cursor dentro da spawn area mais próxima que cobre a posição.
- Tools: Towns "Add/Edit Town...", "Set Town Temple Here...", "Delete Town..." (Edit -> Tools) com undo/redo; suporte de load/save via OTBM nodes OTBM_TOWNS/OTBM_TOWN.
- Brushes: TableBrush (MVP) suportado no stroke pipeline: não clobbera itens acima (family-aware) e auto-border também respeita a família para não sobrescrever a stack.
- Brushes: HouseBrush (virtual) suportado via paleta House (usa definições de `houses.xml`): pintar seta `Tile.house_id`; Alt+paint limpa.
- Brushes: OptionalBorderBrush (MVP / virtual) adicionado na paleta Terrain: pinta/limpa o carpet “loose gravel” (id 6373) de forma family-aware (não clobbera stack).
- Tools: Switch Door (MVP): ação undoable em Edit -> Tools que alterna uma porta (open/closed) no cursor via heurística de pairing em `data/items/items.xml`.
- Brushes: DoodadBrush (MVP): seleção na aba Doodad agora usa IDs virtuais para aplicar semântica de doodad (coloca item no topo; Alt remove 1; sem auto-border).
- Brushes: HouseExitBrush (MVP / virtual): paleta House expõe "Exit: <id>" que seta/limpa entry do house no tile (Alt limpa), com undo/redo.
- Brushes: WaypointBrush (MVP / virtual): paleta Waypoint lista waypoints existentes e permite mover (clique) / deletar (Alt) com undo/redo.
- Brushes: Creature/Npc + Spawn tools (MVP / virtual): paletas expõem Monsters/NPCs e ferramentas de spawn area; clique/drag adiciona/remove entries via smear em múltiplos tiles (Alt remove), com 1 undo por gesto.
- Brushes: DoorBrush (MVP+): paleta Terrain expoe ferramentas de porta por tipo; clique/drag usa door defs do materials quando disponivel, fallback para default via `items.xml`; nao alterna open/closed (use "Switch Door"); Alt remove; 1 undo por gesto.
- UI/Paleta: Recentes (MVP): nova aba “Recent” lista brushes recentemente selecionados (estado Qt-free na sessão).

### ✅ Entregue nesta rodada
- DoorBrush (MVP / virtual) + ferramenta na paleta + validação in-memory + atualização deste documento.
- Recentes (MVP) + nova aba na paleta + atualização deste documento.
- Creature/Npc (MVP): drag/smear para spawn entries com 1 undo por gesto.
- DoorBrush (MVP): drag/smear (place/remove) com 1 undo por gesto.
 - Variação (MVP): `brush_variation` + controle na toolbar + variação determinística para ground brushes com `randomize_ids`.
 - Espessura (MVP / Doodad): `doodad_use_custom_thickness` + `Thickness/T:` na toolbar; controla densidade (probabilidade) de colocação do doodad na footprint.
- (Quality) Mypy: corrigido baseline e agora `mypy py_rme_canary/core py_rme_canary/logic_layer` passa sem erros (incluiu ajustes de `Optional` e compatibilidade `PaintAction`↔`EditorAction`).
- (Quality) Mypy: config mais estrita (desligado `ignore_missing_imports`) e redução de exclusões: `py_rme_canary/tools/` passou a ser checado; `mypy py_rme_canary/core py_rme_canary/logic_layer py_rme_canary/tools` passa.
- (Quality) Mypy: enforcement incremental de typing em `core/`/`logic_layer`/`tools` via overrides (`check_untyped_defs=true` + `disallow_untyped_defs=true`) sem impactar `vis_layer/`.

- DoodadBrush (MVP+): carregamento Qt-free de doodads a partir de `data/materials/brushs.xml` (inclui `<alternate>` e `<composite>`); a aba Doodad passa a listar esses brushes quando disponíveis.
- Semântica de doodad (MVP+): seleção determinística (chance/alternates) + composites multi-tile e suporte a `on_duplicate` e `one_size`. Alt remove seguindo a mesma seleção.

- DoodadBrush (paridade / TODO Extenso): parsing tolerante com warnings, lazy-load na UI (sem travar startup), semântica extra (`draggable`, `on_blocking` (aprox. conservadora), `redo_borders`, thickness XML + override da toolbar), remoção Alt “owned-item”, composites com stack explícita e validações in-memory ampliadas.
- Drag/Smear (geral / TODO Extenso): gesto comum batched para ferramentas especiais (1 undo por gesto) aplicado em Creature/Npc, DoorBrush e SpawnMonster/SpawnNpc (spawn areas em drag/smear).

### ✅ Continuação (2026-01-05)
- Qualidade/Dev workflow: adicionado `.pre-commit-config.yaml` (ruff + ruff-format), workflow de CI em `.github/workflows/python-quality.yml` (ruff/mypy/compileall) e `requirements-dev.txt` atualizado com `pre-commit`.
- Smoke-check local: `python -m compileall -q py_rme_canary`.
- Documentação: criado “TODO Extenso (Prioridade Máxima)” (render moderno + Ruff/Mypy/typing) para guiar as próximas rodadas.
- Qualidade/Ruff (core + logic): regras expandidas no `pyproject.toml` (E/W/I/N/UP/B/C4/SIM) + aplicação de `ruff --fix` e `ruff format`; `ruff check py_rme_canary/core py_rme_canary/logic_layer` agora passa limpo.

### 🧾 Resumo desta continuação
- Implementado Variação (MVP) de forma Qt-free: `EditorSession.brush_variation` propaga para `GestureHandler` e `TransactionalBrushStroke`.
- UI: adicionado controle simples na toolbar Sizes (`Var:`) e sincronização com a sessão.
- Hotkeys (legacy-inspired): `Z`/`X` agora ciclam a variação (decrementa/incrementa). Para evitar conflito, “Show npcs” saiu de `X` e foi movido para `Alt+X`.
- Semântica atual (intencionalmente mínima): apenas **ground** com `randomize_ids` é afetado; variação escolhe determinísticamente entre (id principal + variantes).
- Implementado Espessura (MVP) para Doodad: controle de thickness (checkbox + nível 1..10) e estado Qt-free; aplicado como densidade probabilística de colocação no brush footprint, sempre colocando no tile inicial do gesto.
