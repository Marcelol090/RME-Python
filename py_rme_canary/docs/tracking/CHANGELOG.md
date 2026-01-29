## Unreleased (py_rme_canary)

Documentation:
* **Documentation Accuracy Session Part 7 - Extended** (2026-01-23):
  - ANALISE_FALTANTE.md: Take Screenshot ❌ → ✅ (`_take_screenshot()` com F10 shortcut)
  - ANALISE_FALTANTE.md: FindItemDialog, FindEntityDialog, ReplaceItemsDialog, FindPositionsDialog marcados ✅
  - ANALISE_FALTANTE.md: Adicionados WaypointQueryDialog, FindNamedPositionsDialog, MapStatisticsDialog ✅
  - ANALISE_FALTANTE.md: Preferences Window seção adicionada (confirmado ❌ NÃO implementado)
  - IMPLEMENTATION_STATUS.md: Adicionadas 8 novas entradas UI/dialogs
  - PRD.md seção 2.3 (Rendering & Display): Take Screenshot adicionado com status ✅
  - Verificação C++ legacy: 107 arquivos .cpp verificados contra implementações Python
  - Dialogs implementados: 8 classes (FindItemDialog, FindEntityDialog, ReplaceItemsDialog, FindPositionsDialog, WaypointQueryDialog, FindNamedPositionsDialog, MapStatisticsDialog, + Screenshot)
  - Selection Modes C++ (SELECT_MODE_*): confirmados como NÃO implementados em Python
  - Preferences Window: confirmado como NÃO implementado (735 linhas C++ vs 0 Python)
  - Total features descobertas Part 7: +8 (5 já documentadas + 3 novas)
  - Total features confirmadas como faltantes: +1 (Preferences)

* **Documentation Accuracy Session Part 6** (2026-01-23):
  - PRD.md: Action History Panel ❌ → ✅ (implementado em `actions_history.py`)
  - PRD.md: Feature Parity Status 85.0% → 87.5% (UI/UX agora 100%)
  - ANALISE_FALTANTE.md: Clear Invalid House Tiles ❌ → ✅ (`clear_invalid_tiles()`)
  - ANALISE_FALTANTE.md: Clear Modified Tile State ❌ → ✅ (`clear_modified_state()`)
  - ANALISE_FALTANTE.md: ActionType enum atualizado (41 tipos implementados)
  - IMPLEMENTATION_STATUS.md: Action Types ⚠️ → ✅ (`ActionType` enum)
  - IMPLEMENTATION_STATUS.md: Adicionado Actions History UI entry
  - IMPLEMENTATION_TODO.md: mirroring.py ❌ → ✅ (122 linhas implementadas)
  - IMPLEMENTATION_TODO.md: Nota de profissionalismo 88/100 → 92/100
  - Verificação C++ legacy: `actions_history_window.cpp` vs `actions_history.py`

* **IMPLEMENTATION_STATUS.md Path Corrections** (2025-01-23):
  - Corrigidos caminhos de arquivos de brush que apontavam para `logic_layer/brushes/` (pasta inexistente)
  - Caminhos atualizados para localização correta: `logic_layer/monster_brush.py`, `logic_layer/npc_brush.py`, etc.
  - Status atualizados: TableBrush ⚠️ → ✅, CarpetBrush ⚠️ → ✅, DoorBrush ⚠️ → ✅, DoodadBrush ⚠️ → ✅
  - MonsterBrush, NpcBrush, FlagBrush, EraserBrush: separados com caminhos corretos e status ✅
  - BrushShape/Size: caminho corrigido para `logic_layer/brush_settings.py`
  - Border Groups/Friends/GroundEquivalents: caminhos atualizados para `logic_layer/borders/`
  - Nota de auditoria adicionada com data 2025-01-23

* **Toolbars & Summary Table Update** (2025-01-23):
  - ANALISE_FALTANTE.md seção 19 (Toolbars): ❌ → ✅ (5 toolbars completas implementadas)
  - ANALISE_FALTANTE.md seção 18 (About Window): ❌ → ⚠️ (parcial, PySide6 deprecado)
  - ANALISE_FALTANTE.md tabela de resumo: Reescrita de 13% → 65% (~122 implementadas vs ~30 anterior)
  - Total features corrigidas nesta sessão: +2

* **PRD.md Feature Parity Update** (2025-01-23):
  - Feature Parity Status corrigido de 72.2% → 85.0% (+12.8%)
  - Seção 1.1 Map I/O: OTMM Load/Save separados com detalhes de implementação
  - Seção 1.2 Brush System: expandido de 8 → 15 brushes (Monster, NPC, Flag, Eraser, BrushShape, BrushSettings)
  - Seção 1.4 Map Operations: todas 8 operações agora ✅
  - Priority Roadmap: Phases 1-2 ✅, Phase 3 🔄 in progress
  - Nota de auditoria adicionada à tabela de Feature Parity

* **Documentation Accuracy Refactor** (2025-01-23):
  - ANALISE_FALTANTE.md seção 1 (Brushes): 15+ brushes atualizados ❌→✅ (TableBrush, CarpetBrush, DoorBrush, DoodadBrush, MonsterBrush, NpcBrush, FlagBrush, EraserBrush, BrushShape, Brush Size, Recent Brushes)
  - ANALISE_FALTANTE.md seção 2 (Selection): duplicate_selection, move_selection_z, borderize_selection, randomize_selection marcados ✅
  - ANALISE_FALTANTE.md seção 3.3 (DrawingOptions): todas 24 opções show_* atualizadas para ✅
  - ANALISE_FALTANTE.md seção 4 (Live Server/Client): status atualizado para ⚠️ Parcialmente Implementado
  - ANALISE_FALTANTE.md seção 6 (Busca/Substituição): Replace/Remove items marcados como ✅
  - ANALISE_FALTANTE.md seção 9 (Palette): todos 10 tipos de paleta marcados ✅
  - ANALISE_FALTANTE.md seção 10 (Navigation): 6 funções marcadas ✅
  - ANALISE_FALTANTE.md seção 13 (Statistics): MapStatistics completo com 17 métricas ✅
  - **Total:** ~85 status incorretos corrigidos, precisão de documentação aumentada para ~95%

Features:
* **Asset System completo** (2025-01-23):
  - `AssetProfile` auto-detecta modern (catalog-content.json) vs legacy (Tibia.dat/.spr).
  - `LegacySpriteArchive` carrega sprites de clientes antigos com decode RLE e cache LRU.
  - `appearances_dat.py` parseia protobuf appearances.dat com suporte a animações (SpriteAnimation, phase selection by time_ms).
  - `loader.py` unifica carregamento com `load_assets_from_path()` retornando `LoadedAssets`.
  - `animation_time_ms()` e `advance_animation_clock()` no editor para sprites animados.
  - `_resolve_sprite_id_from_client_id()` integra appearances para resolver sprite correto por tempo.
* ActionQueue completo: stacking delay, CompositeAction para lotes, labels descritivos, reset de timer.
* Border system avançado: border_friends (friend/enemy entre brushes), border_groups (agrupamento de bordas), ground_equivalents (equivalências de terreno).
* Live Protocol: login payload encoding/decoding com LOGIN_SUCCESS/LOGIN_ERROR handling.
* MapValidator: validação completa de estrutura do mapa (tiles, houses, zones, spawns, waypoints, towns).
* PropertiesPanel: inspeção de Tile/Item/House/Spawn/Waypoint/Zone com métodos dedicados.
* MinimapRenderer: exportação PNG de minimapa por floor com MinimapColorTable.
* Render fallbacks: QPainter e OpenGL backends com cores placeholder para sprites ausentes.
* UI parity: implementado “Find Item…” (Ctrl+F) com busca real no mapa e navegação até o resultado.
* UI parity: implementado “Find on Map → Waypoint…” (busca por substring, case-insensitive) com seleção de resultado e centralização.
* UI parity: implementado “Find on Map → Item…” reutilizando o pipeline do Find Item.
* Legacy parity: implementado “Replace Items…” como operação em lote, undoable (um único passo), com limite de segurança padrão alinhado ao legado (500) e suporte a containers.
* Legacy parity: implementado “Replace Items on Selection…” (variante restrita à seleção), mantendo semântica/undo do legado.
* Legacy parity: implementado “Remove Item on Selection…” (remove em ground + stack de topo; melhor-esforço para pular itens “complex”).
* Legacy parity: implementado “Map Statistics…” com relatório textual (Refresh/Export) inspirado no RME.

* Legacy parity: mirror drawing behavior (axis + dedupe + bounds) centralized in logic layer and used by the PyQt6 canvas.
* OTBM parity: improved loader/saver compatibility (attribute map roundtrip, OTBM v1 subtype byte support, and stackable COUNT rules for v2+).
* Legacy parity: brush footprint and border-ring offset generation extracted into a pure geometry module with tests.

Quality:

* Architecture: mantida a separação por camadas (logic_layer Qt-free + vis_layer Qt), com operações testáveis fora do GUI.
* UI robustness: corrigida a inicialização de menus/ações no app Qt (evita menus temporários e chamadas para helpers inexistentes).
* UI bugfix: corrigido bug de indentação onde dialogs de waypoint/resultados ficaram acidentalmente “nested” dentro de outra classe.
* Tests: adicionados/expandido testes de busca (itens/waypoints), replace (incl. seleção) e remove (seleção), mantendo `pytest -q` verde.
* Quality pipeline: `quality.sh` agora usa `PYTHON_BIN`, corrige normalização de issues e comparação de símbolos, e faz mypy apenas em core/logic_layer.
* Tooling: `tools/convert_png2cpp.py` migrado para Python 3 com I/O em UTF-8.
* Type safety: ajustes de tipagem em selection/live_server para alinhar com protocolos.

* Repository cleanup: removed deprecated `data_layer/` and eliminated experimental UI codepaths (no PySide6/Tk in the canonical UI).
* Test standardization: consolidated on pytest-only under `tests/`.
* Optional quality tooling: added incremental `ruff`/`mypy` setup and contributor documentation.

Planned / Future:

* Legacy parity: “Remove Monsters on Selection…” (e variações de contagem), seguindo o padrão: lógica Qt-free + operação undoable + wiring no menu.
* Legacy parity: “Remove duplicated items on selection…” (limpeza por duplicatas, restrito à seleção).
* Legacy parity: “Search for … on Selection” (action/containers/writeable/tiles/properties) com janela de resultados e export, inspirado no legado.
* Config parity: expor limites de segurança (REPLACE_SIZE/REMOVE_SIZE) como setting configurável, mantendo defaults do legado.

#### 3.5

Features:

* Implements flood fill in Terrain Brush.
* Update wall brushes for 10.98
* Added Show As Minimap menu.
* Make spawns visible when placing a new spawn.

Fixed bugs:

* Fix container item crash.

#### 3.4

Features:

* New Find Item / Jump to Item dialog.
* Configurable copy position format.
* Add text ellipsis for tooltips.
* Show hook indicators for walls.
* Updated data for 10.98

Fixed bugs:

* Icon background colour; white and gray no longer work.
* Only show colors option breaks RME.

#### 3.3

Features:

* Support for tooltips in the map.
* Support for animations preview.
* Restore last position when opening a map.
* Export search result to a .txt file.
* Waypoint brush improvements.
* Better fullscreen support on macOS.

Fixed bugs:

* Items larger than 64x64 are now displayed properly.
* Fixed potential crash when using waypoint brush.
* Fixed a bug where you could not open map files by clicking them while the editor is running.
* You can now open the extensions folder on macOS.
* Fixed a bug where an item search would not display any result on macOS.
* Fixed multiple issues related to editing houses on macOS.

#### 3.2

Features:

* Export minimap by selected area.
* Search for unique id, action id, containers or writable items on selected area.
* Go to Previous Position menu. Keyboard shortcut 'P'.
* Data files for version 10.98.
* Select Raw button on the Browse Field window.

Fixed bugs:

* Text is hidden after selecting an item from the palette. Issue #144
* Search result does not sort ids. Issue #126
* Monster direction is not saved. Issue #132

#### 3.1

Features:

* In-game box improvements. Now the hidden tiles, visible tiles and player position are displayed.
* New _Zoom In_, _Zoom Out_ and _Zoom Normal_ menus.
* New keyboard shortcuts:
	- **Ctrl+Alt+Click** Select the relative brush of an item.
	- **Ctrl++** Zoom In
	- **Ctrl+-** Zoom Out
	- **Ctrl+0** Zoom Normal(100%)
* If zoom is 100%, move one tile at a time.

Fixed bugs:

* Some keyboard shortcuts not working on Linux.
* Main menu is not updated when the last map tab is closed.
* In-game box wrong height.
* UI tweaks for Import Map window.
