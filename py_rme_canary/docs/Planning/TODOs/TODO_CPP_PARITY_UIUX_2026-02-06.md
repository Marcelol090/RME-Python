# TODO CPP Parity UI/UX - Paridade C++/Lua -> Python (2026-02-06)

## Escopo auditado
- Referência C++/Lua:
  - `remeres-map-editor-redux/data/menubar.xml`
  - `remeres-map-editor-redux/source/ui/main_menubar.cpp`
  - `remeres-map-editor-redux/source/ui/map_popup_menu.cpp`
  - `remeres-map-editor-redux/source/ui/menubar/map_actions_handler.cpp`
  - `remeres-map-editor-redux/source/ui/menubar/search_handler.cpp`
- Planejamento/visão de produto:
  - `py_rme_canary/docs/Planning/Features.md`
- Implementação Python:
  - `py_rme_canary/vis_layer/ui/main_window/*`
  - `py_rme_canary/vis_layer/ui/menus/context_menus.py`
  - `py_rme_canary/logic_layer/*`
  - `py_rme_canary/core/*`

## Resultado da análise (resumo)

### Implementado (base sólida)
- OTBM ClientID/ServerID com tradução de IDs em load/save.
- Lasso/freehand selection integrado no canvas.
- Import de monsters/NPC via Lua.
- Conversão de formato de mapa exposta no UI.
- Highlight visual de posição ao navegar.
- Infra de cross-version clipboard e sprite hash presente no projeto.

### Parcial / com lacunas de integração
- Context menu de item exibe opções avançadas, mas canvas conecta somente `set_find`, `set_replace`, `find_all`, `replace_all`.
- `FindItemDialog` possui flag `selection_only`, mas a busca itera o mapa inteiro.
- `Border Builder` atual é visualizador (sem edição persistente de regras).
- `PreferencesDialog` ainda sem persistência completa no `ConfigurationManager`.
- Export OTMM tem ação no menu, mas não há método `_export_otmm` no editor.
- Recursos "modern UX" dependentes de `menu_file/menu_edit` não são acionados porque esses atributos não são inicializados no builder atual.

### Ausências importantes vs C++ e vs Features.md
- Ações de limpeza/paridade de mapa:
  - Remove item por ID (mapa todo), remove corpses, remove unreachable, clear invalid houses.
- Busca dedicada por tipo (unique/action/container/writeable) com atalhos de menu equivalentes.
- Export Tilesets / Reload Data / Preferences / Extensions / Goto Website equivalentes de menu.
- Pipeline de ícones próprio (SVG/PNG) ainda incompleto; grande parte da UI usa emojis em labels/ações.
- "Show ClientIDs" (feature documentada) sem toggle funcional equivalente no UI.
- Aviso automático de UID duplicado no fluxo de edição/paste/load (atualmente foco manual por relatório).

## TODO de implementação (10 tarefas)

- [x] `P0-MENU-001` Paridade de menus File/About/Search/Selection com C++.
  - Incluir ações ausentes: Preferences, Reload Data, Export Tilesets, Extensions, Goto Website, Search dedicado.
  - Integrar ações no `build_actions.py` + `build_menus.py` com handlers reais.
  - Critério de aceite: menus equivalentes operando sem ação "dummy".

- [x] `P0-MAP-002` Implementar operações de limpeza de mapa em paridade.
  - Adicionar: remove item por ID (global), remove corpses, remove unreachable, clear invalid houses.
  - Integrar com `EditorSession` e histórico undo/redo quando aplicável.
  - Critério de aceite: cada ação executa, atualiza mapa/status e possui cobertura de teste unitário.
  - Status (2026-02-06): implementado no `EditorSession` + `Map` menu com ações undoable e cobertura em `tests/unit/logic_layer/test_map_cleanup_operations.py`.

- [x] `P0-SEARCH-003` Fechar paridade de busca avançada por mapa/seleção.
  - Expor ações de `Find Unique/Action/Container/Writeable` e equivalentes em seleção.
  - Corrigir `selection_only` em `FindItemDialog` para respeitar seleção ativa.
  - Critério de aceite: resultados mudam conforme escopo (mapa vs seleção) e filtros.
  - Status (2026-02-06): implementado no `map_search.py`, `find_item.py`, menus/ações da main window e testes unitários.

- [x] `P0-CONTEXT-004` Completar integração backend↔context menus (item/tile).
  - Substituir callbacks parciais dos canvases por callback set completo.
  - Implementar ações padrão pendentes em `context_menu_handlers.py` com ações transacionais.
  - Critério de aceite: ações de contexto editam mapa de fato e atualizam undo/redo.
  - Status (2026-02-06): callbacks completos conectados no canvas/software renderer com cobertura de testes.

- [x] `P0-BORDER-005` Evoluir Border Builder para autor de regras persistentes.
  - Permitir criar/editar/remover regras e salvar no armazenamento de brush definitions.
  - Aplicar reload seguro no `AutoBorderProcessor` sem reiniciar editor.
  - Critério de aceite: regra criada no UI impacta resultado de borderize.
  - Status (2026-02-06): Border Builder ganhou editor de regra por máscara (apply/clear), persistência em `brushes.overrides.json`, reload em runtime e carga automática no startup.

- [x] `P1-PREFS-006` Persistência real de preferências.
  - Ligar `PreferencesDialog` ao `ConfigurationManager`/config de projeto.
  - Remover TODOs de load/save e sincronizar defaults com runtime.
  - Critério de aceite: reiniciar app preserva ajustes de preferência.
  - Status (2026-02-06): persistência completa via `QSettings` (`UserSettings`) para todos campos do diálogo.

- [x] `P1-EXPORT-007` Concluir exportação OTMM no fluxo de UI.
  - Implementar `_export_otmm` no editor e dialog/opções mínimas de export.
  - Conectar com `core/io/otmm_saver.py` e validação de caminho/erro.
  - Critério de aceite: menu exporta `.otmm` válido para mapa de teste.
  - Status (2026-02-06): exportação consolidada para mapa OTMM completo via `core/io/otmm_saver.py` com validação de caminho/erro no fluxo de UI.

- [x] `P1-UIUX-008` Migrar UI para iconografia própria (sem emojis).
  - Criar pacote de ícones (`resources/icons`) para ações, ferramentas e categorias.
  - Substituir labels com emoji em menus, dialogs, status widgets e tooltips.
  - Critério de aceite: interface usa ícones consistentes e sem emoji-format icon.
  - Status (2026-02-06): pacote `vis_layer/ui/resources/icons` criado (SVG próprios), ações/toolbars migradas para `icon_pack.py` e emojis removidos dos módulos ativos de UI.

- [x] `P1-UX-009` Paridade de Toolbars/Docks e integração moderna.
  - Ajustar builder para expor `menu_file/menu_edit` e ativar ações modernas hoje órfãs.
  - Reforçar toolbar de brushes/indicators com assets reais e estados sincronizados.
  - Critério de aceite: todas ações modernas aparecem no menu correto e executam.
  - Status (2026-02-06): sincronização bidirecional menu↔toolbar concluída (indicators, visibilidade de toolbars, automagic) com cobertura de integração em `tests/ui/test_toolbar_menu_sync.py`.

- [x] `P2-QA-010` Endurecimento de qualidade, performance e validação final.
  - Adicionar testes de integração UI↔session para features críticas.
  - Rodar `quality_lf.sh`, otimizar gargalos de cache/IO das ferramentas de quality.
  - Executar workflows locais equivalentes ao CI e anexar relatório final.
  - Critério de aceite: pipeline verde e tempo de quality reduzido de forma mensurável.
  - Status (2026-02-06): suíte `pytest -q` verde (591 passed), `quality_lf.sh` e `quality.sh` em dry-run concluídos com cache ativo e Jules local `status=ok`; execução otimizada de quality medida em ~296s -> ~172s.

## Progresso executado (2026-02-06)
- Menus/actions/handlers implementados para `Preferences`, `Reload Data`, `Export Tilesets`, `Extensions`, `Goto Website`, `Export OTMM`.
- Menus `Search` e `Selection` adicionados para aproximar a estrutura legada C++.
- Compatibilidade de workflow Jules corrigida para Python 3.10 (`datetime.UTC` fallback em scripts).
- Validação local concluída:
  - `python -m pytest -q py_rme_canary/tests/ui` -> 16 passed
  - `python -m pytest -q py_rme_canary/tests/unit` -> 394 passed
  - `python -m pytest -q py_rme_canary/tests/unit/scripts/test_jules_runner.py` -> 7 passed
  - `python -m pytest -q` -> 591 passed
  - `bash py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --timeout 900 --jobs 4`
  - `bash py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --skip-tests --skip-libcst --skip-sonarlint --timeout 120 --jobs 4` (cache/escopo otimizado)
  - `bash ./quality.sh --dry-run --skip-tests --skip-libcst --skip-sonarlint`

## Ordem de execução recomendada
1. `P0-MENU-001`
2. `P0-MAP-002`
3. `P0-SEARCH-003`
4. `P0-CONTEXT-004`
5. `P0-BORDER-005`
6. `P1-PREFS-006`
7. `P1-EXPORT-007`
8. `P1-UIUX-008`
9. `P1-UX-009`
10. `P2-QA-010`

## Incremental Update (2026-02-08)
- Added interactive **Client Data Loader** UX (`Load Client Data...`) with staged progress and summary output.
- Added staged progress feedback for **Open Map** flow (detect -> parse -> session -> context -> refresh).
- Expanded asset-definition synchronization in UI refresh path (palette + canvas + preview after data stack load).
- Hardened Codex review workflow gating/diagnostics to reduce silent skips and surface missing-secret reasons in PR comments.
- Added UI regression assertion for the new Assets action (`Load Client Data...`) in `tests/ui/test_toolbar_menu_sync.py`.
- Implemented **Show Client IDs** parity:
  - Added `Show Client IDs` action in `View`/`Window`.
  - Synced action with `DrawingOptions.show_client_ids`.
  - Added client-id overlays in `MapDrawer` with item metadata + id-mapper fallback.
- Hardened quality execution path:
  - `quality_lf.sh` now executes `ruff/mypy/radon` via `"$PYTHON_BIN" -m ...` for deterministic interpreter/tool resolution.
- Validation refresh:
  - `python -m pytest -q py_rme_canary/tests` -> `624 passed`.
  - `bash py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --verbose --skip-ui-tests --skip-security --skip-deadcode --skip-sonarlint --skip-jules` -> green run with cache reuse and no new normalized issues.

## Incremental Update (2026-02-09)
- Added regression coverage for staged progress in `Open Map` flow:
  - `py_rme_canary/tests/unit/vis_layer/ui/test_qt_map_editor_file_open_progress.py`.
  - Covers success path (all 6 phases) and cancelation/error path handling.
- Added regression coverage for interactive `Load Client Data` flow:
  - `py_rme_canary/tests/unit/vis_layer/ui/test_qt_map_editor_assets_loader.py`.
  - Covers summary generation with saved-profile suffix and explicit `items.otb/items.xml` branch.
- Validation refresh:
  - `python -m pytest -q py_rme_canary/tests/unit/vis_layer/ui/test_qt_map_editor_file_open_progress.py py_rme_canary/tests/unit/vis_layer/ui/test_qt_map_editor_assets_loader.py` -> `4 passed`.
  - `python -m pytest -q py_rme_canary/tests/unit/vis_layer/ui/test_qt_map_editor_assets_profiles.py py_rme_canary/tests/ui/test_toolbar_menu_sync.py` -> `12 passed`.
- Modern palette integration hardening:
  - `ModernPaletteDock` now exposes legacy-compatible API (`refresh_primary_list`, `select_palette`, `set_icon_size`, `create_additional`, `primary/current_palette_name`) used by existing mixins/actions.
  - Added search filter + icon-size propagation to tab widgets and synchronized `editor.brush_filter/editor.brush_list` bindings with current tab.
  - `build_docks.py` now points `editor.palettes` to modern palette dock compatibility layer.
  - Added tests:
    - `py_rme_canary/tests/unit/vis_layer/ui/test_modern_palette_dock.py`
    - `py_rme_canary/tests/ui/test_toolbar_menu_sync.py::test_palette_menu_actions_target_modern_palette_dock`
- Asset mapping robustness hardening (`items.otb` + `items.xml`):
  - Added mapper merge strategy that keeps OTB mappings as primary and fills missing entries from XML.
  - Applied merge path for both context-driven load and explicit `items.otb/items.xml` load.
  - Warnings now report merge delta (e.g. `items_mapper_merge: added N mappings ...`) for diagnostics.
  - Added tests:
    - `py_rme_canary/tests/unit/vis_layer/ui/test_qt_map_editor_assets_mapping_merge.py`
  - Validation:
    - `python -m pytest -q py_rme_canary/tests/unit/vis_layer/ui/test_qt_map_editor_assets_mapping_merge.py py_rme_canary/tests/unit/vis_layer/ui/test_qt_map_editor_assets_loading_helpers.py py_rme_canary/tests/unit/vis_layer/ui/test_qt_map_editor_assets_loader.py py_rme_canary/tests/unit/vis_layer/ui/test_qt_map_editor_assets_profiles.py` -> `11 passed`.

## Incremental Update (2026-02-10)
- Deep parity re-check against legacy C++ (`data/menubar.xml`, `ui/menubar/palette_menu_handler.cpp`, `palette/palette_window.cpp`, `ui/map_popup_menu.cpp`) identified two concrete gaps:
  - Missing `Collection` entry in `Window > Palette` for modern UI flow.
  - `ModernToolOptionsWidget` variation slider was not wired to backend/session methods.
- Implemented Collection parity in modern UI:
  - Added `act_palette_collection` (`N`) and moved `NPC` to `Alt+N`.
  - Added `Collection` entry in `Window > Palette`.
  - Added `Collection` tab/content source in `ModernPaletteDock` with compatibility fallback in legacy palette manager.
- Closed UI/UX -> backend integration gap:
  - Wired modern variation signal to runtime handlers:
    - `terrain/others` -> `_set_brush_variation`.
    - `doodad/collection` -> `_set_doodad_thickness_enabled` + `_set_doodad_thickness_level`.
  - Added `collection` behavior in tool-options visibility map.
- Extended context-menu parity:
  - Added `Select Collection` action in item context menu.
  - Added handler `select_collection_brush()` to select brush and switch palette to `collection`.
- Added/updated regression coverage:
  - `tests/ui/test_toolbar_menu_sync.py::test_palette_collection_action_targets_modern_palette_dock`
  - `tests/unit/vis_layer/ui/test_modern_palette_dock.py::test_modern_palette_dock_collection_and_variation_backend_binding`
  - `tests/unit/logic_layer/test_context_menu_handlers.py::test_select_collection_brush_selects_collection_palette`

## Incremental Update (2026-02-10 - Phase 2)
- Deepened legacy popup parity based on `remeres-map-editor-redux/source/ui/map_popup_menu.cpp` and `source/rendering/ui/brush_selector.cpp`:
  - Added explicit smart brush handlers for:
    - `Select Wallbrush`, `Select Carpetbrush`, `Select Tablebrush`, `Select Doodadbrush`, `Select Doorbrush`, `Select Groundbrush`.
    - `Select House`, `Select Creature`, `Select Spawn` (tile-driven).
  - Kept `Select RAW` and `Select Collection`, with collection now preferring collection-compatible brush families from tile context.
- Closed additional UI/UX -> backend integration gaps:
  - `ContextMenuActionHandlers` now resolves brush families through `brush_manager.get_brush_any()` before selecting.
  - Palette switching is now synchronized with selected brush type (`terrain/item/doodad/house/creature/npc/collection/raw`).
  - Item callback map became capability-aware (legacy options only appear when tile/item context supports them).
- Updated item context menu labels/order toward legacy wording:
  - Uses legacy-style entries (`Select RAW`, `Select Wallbrush`, `Select Groundbrush`, etc.) when callbacks exist.
- Added regression coverage:
  - `tests/unit/logic_layer/test_context_menu_handlers.py::test_select_wall_brush_uses_resolved_brush_and_palette`
  - `tests/unit/logic_layer/test_context_menu_handlers.py::test_get_item_context_callbacks_include_legacy_select_keys`
  - `tests/unit/logic_layer/test_context_menu_handlers.py::test_select_spawn_brush_prefers_spawn_marker_tool`
- Validation refresh:
  - `python3 -m py_compile py_rme_canary/logic_layer/context_menu_handlers.py py_rme_canary/vis_layer/ui/menus/context_menus.py py_rme_canary/tests/unit/logic_layer/test_context_menu_handlers.py` -> OK
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -s py_rme_canary/tests/unit/logic_layer/test_item_type_detector.py` -> `22 passed`
  - `pytest` for Qt-dependent suites remains blocked in this environment (`libEGL.so.1` / `libxkbcommon.so.0` missing)

## Incremental Update (2026-02-10 - Phase 3)
- Unified canvas right-click flow toward legacy C++ popup behavior:
  - `MapCanvasWidget` now opens a single context menu pipeline for both item and tile-empty cases.
  - Context menu now receives selection state and supports legacy top actions in one place:
    - `Cut`, `Copy`, `Copy Position`, `Paste`, `Delete`, `Replace tiles...`.
- Extended backend handlers for selection operations from context menu:
  - Added session/editor delegates in `ContextMenuActionHandlers`:
    - `copy_selection`, `cut_selection`, `delete_selection`, `replace_tiles_on_selection`, `paste_at_position`.
  - Added state helpers:
    - `has_selection`, `can_paste_buffer`.
  - Added `get_tile_context_callbacks()` for empty-tile context menu fallback.
  - Added `open_tile_properties()` fallback to browse dialog.
- Updated UI labels/order for legacy alignment:
  - Renamed tile inspector action from `Browse Tile...` to `Browse Field` in item/tile unified menu.
  - Kept item-local actions (`Copy Item`, `Delete Item`) separated from selection/global top actions.
- Added regression coverage for new context flow API:
  - `tests/unit/logic_layer/test_context_menu_handlers.py`:
    - `test_tile_context_callbacks_include_selection_operations`
    - `test_selection_callbacks_delegate_to_editor_methods`
    - `test_paste_at_position_uses_session_paste_buffer`
  - Hardened module skip behavior in constrained environments:
    - `pytest.importorskip("PyQt6.QtWidgets")`.
- Validation refresh:
  - `python3 -m py_compile py_rme_canary/logic_layer/context_menu_handlers.py py_rme_canary/vis_layer/ui/menus/context_menus.py py_rme_canary/vis_layer/ui/canvas/widget.py py_rme_canary/tests/unit/logic_layer/test_context_menu_handlers.py` -> OK
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -s py_rme_canary/tests/unit/logic_layer/test_item_type_detector.py` -> `22 passed`
  - Attempted Qt bootstrap on WSL local environment:
    - `apt-get update/install ...` blocked due permission on `/var/lib/apt/lists/lock` (no sudo/root in this runtime).

## Incremental Update (2026-02-10 - Phase 4)
- Quality/validation hardening for the new context flow:
  - `ruff check` now clean for all edited files:
    - `logic_layer/context_menu_handlers.py`
    - `vis_layer/ui/menus/context_menus.py`
    - `vis_layer/ui/canvas/widget.py`
    - `tests/unit/logic_layer/test_context_menu_handlers.py`
  - Qt-dependent unit module skip guard adjusted to future-proof pytest behavior:
    - `pytest.importorskip("PyQt6.QtWidgets", exc_type=ImportError)`.
- Validation refresh:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -s py_rme_canary/tests/unit/logic_layer/test_context_menu_handlers.py` -> `1 skipped` (expected in this environment).
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -s py_rme_canary/tests/unit/logic_layer/test_item_type_detector.py` -> `22 passed`.

## Incremental Update (2026-02-10 - Phase 5)
- Closed parity gap for context menu in **empty map fields** and OpenGL path:
  - `MapCanvasWidget` no longer aborts context menu flow when `map.get_tile(...)` returns `None`.
  - `OpenGLCanvasWidget` now uses the same unified context pipeline as QWidget canvas.
  - Both canvases now route callbacks as:
    - `get_item_context_callbacks(...)` for item/ground contexts.
    - `get_tile_context_callbacks(...)` for empty-field contexts.
- Hardened context position handling:
  - `ItemContextMenu.show_for_item(...)` now accepts `position=(x, y, z)` even when `tile` is `None`.
  - `Copy Position` and tile header use explicit coordinates from `position` fallback.
  - Enables practical legacy-like flow: right-click empty field -> `Paste`/`Copy Position` available.
- Added regression coverage for canvas-level UI/backend wiring:
  - `tests/unit/vis_layer/ui/test_context_menu_canvas_integration.py`
    - `test_map_canvas_context_menu_supports_empty_tile`
    - `test_opengl_canvas_context_menu_supports_empty_tile`
    - `test_item_context_menu_uses_position_for_copy_when_tile_is_empty`
- Validation refresh:
  - `ruff check ...` on edited files -> `All checks passed`.
  - `python3 -m py_compile ...` on edited files -> `OK`.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -s py_rme_canary/tests/unit/vis_layer/ui/test_context_menu_canvas_integration.py py_rme_canary/tests/unit/logic_layer/test_context_menu_handlers.py py_rme_canary/tests/unit/logic_layer/test_item_type_detector.py` -> `22 passed, 2 skipped`.
  - Full pytest with plugins still blocked by missing native Qt dependency in this runtime:
    - `ImportError: libfontconfig.so.1`.

## Incremental Update (2026-02-10 - Phase 6)
- Refined legacy `Properties...` behavior for item context menu:
  - `ContextMenuActionHandlers.open_item_properties(...)` now opens direct item-properties editing
    (Action ID / Unique ID / Text) instead of always routing to full tile-browser flow.
  - Property edits are now committed transactionally through `_apply_item_change(...)`,
    preserving undo/redo and action queue consistency (`Item Properties` label).
  - Added fallback mutation only when session/history commit is unavailable.
- Added regression tests for properties flow:
  - `tests/unit/logic_layer/test_context_menu_handlers.py`
    - `test_open_item_properties_is_transactional`
    - `test_open_item_properties_cancel_keeps_item_unchanged`
- Quality + Jules run completed:
  - `PYTHON_BIN=python3 bash py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --verbose --skip-ui-tests` -> pipeline concluded with Jules artifacts.
  - Explicit Jules trigger:
    - `python3 py_rme_canary/scripts/jules_runner.py --project-root . check --source sources/github/Marcelol090/RME-Python`
    - `python3 py_rme_canary/scripts/jules_runner.py --project-root . generate-suggestions --source sources/github/Marcelol090/RME-Python --task "continuacao-context-properties-parity" --quality-report .quality_reports/refactor_summary.md --output-dir reports/jules --schema .github/jules/suggestions.schema.json`
- Validation refresh:
  - `ruff check py_rme_canary/logic_layer/context_menu_handlers.py py_rme_canary/tests/unit/logic_layer/test_context_menu_handlers.py` -> `All checks passed`.
  - `python3 -m py_compile py_rme_canary/logic_layer/context_menu_handlers.py py_rme_canary/tests/unit/logic_layer/test_context_menu_handlers.py` -> `OK`.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -s py_rme_canary/tests/unit/vis_layer/ui/test_context_menu_canvas_integration.py` -> `3 passed`.
  - Full logic-layer context-menu unit module remains blocked in this runtime by Python mismatch:
    - local interpreter is `Python 3.10`, while project source includes `Python 3.12` syntax in unrelated imports (e.g. `class LRUCache[T]`).

## Incremental Update (2026-02-10 - Phase 7)
- Closed another C++ parity gap (`Edit Towns` action):
  - `qt_map_editor_dialogs._edit_towns()` no longer shows stub-only message.
  - Action now routes to real Town Manager (`show_town_manager`) with fallback to session helper flow.
- Refactored `TownListDialog` to align with real backend model:
  - Uses `Town.temple_position` (instead of stale `temple` attribute assumption).
  - Uses real `Town` dataclass creation on add.
  - Temple update path now writes `temple_position` and supports session-backed mutation (`set_town_temple_position`).
  - Delete now blocks when houses are linked to the town (legacy parity behavior from redux `towns_window.cpp`).
  - Added parent refresh hooks after mutations (`canvas.update`, dirty flag).
- Added regression coverage:
  - `tests/unit/vis_layer/ui/test_town_list_dialog.py`
    - loads `temple_position` correctly
    - add uses current cursor position
    - set temple delegates to session
    - delete is blocked with linked houses

## Incremental Update (2026-02-10 - Phase 8)
- Removed `Generate Map` dead-end stub in file menu parity flow:
  - `qt_map_editor_file._generate_map()` now routes to the real template-based map creation flow (`_new_map()`).
  - Added status feedback for action visibility in UI telemetry (`Generate Map: template flow opened`).
- Added regression coverage:
  - `tests/unit/vis_layer/ui/test_qt_map_editor_generate_map.py::test_generate_map_routes_to_new_map_flow`

## Incremental Update (2026-02-10 - Phase 9)
- Closed `Map Cleanup` parity gap for undo/redo safety:
  - `qt_map_editor_dialogs._map_cleanup()` no longer mutates tiles directly.
  - Cleanup now delegates to transactional session flow via `_map_clear_invalid_tiles()` when available.
  - Fallback path now uses `session.clear_invalid_tiles(selection_only=False)` and keeps UI/action refresh behavior.
- Removed `id_mapper` hard requirement from cleanup path:
  - cleanup now follows `EditorSession.clear_invalid_tiles` definition of invalid items (placeholder/unknown replacements).
- Added map-level session wrapper:
  - `qt_map_editor_session._map_clear_invalid_tiles(confirm: bool = True)` to centralize map cleanup routing and avoid duplicated confirmation prompts.
- Added regression coverage:
  - `tests/unit/vis_layer/ui/test_qt_map_editor_map_cleanup.py`
    - cancel path (no changes)
    - delegation path (`_map_clear_invalid_tiles`)
    - fallback path (`session.clear_invalid_tiles(selection_only=False)`)
    - behavior without `id_mapper`

## Incremental Update (2026-02-11 - Phase 10)
- Validation closure for Phase 7/8 parity items (`Edit Towns` + `Generate Map`):
  - `tests/unit/vis_layer/ui/test_town_list_dialog.py` -> validated temple position flow, add by current cursor, session delegation and house-linked delete guard.
  - `tests/unit/vis_layer/ui/test_qt_map_editor_generate_map.py` -> validated `_generate_map()` delegates to `_new_map()` template flow.
- Quality pipeline analytical run completed:
  - `bash py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --verbose --skip-ui-tests --skip-security --timeout 120` -> concluded with Jules artifacts.
  - Noted environment-specific blocker when security stage is enabled: `bandit` process may hang in this runtime; mitigated by using `--skip-security` for deterministic local validation and keeping targeted security runs isolated.

## Incremental Update (2026-02-11 - Phase 11)
- Performance optimization using Rust acceleration boundary (legacy-compatible output preserved):
  - `logic_layer/minimap_png_exporter.py` now routes heavy pixel-buffer rendering through `logic_layer.rust_accel.render_minimap_buffer(...)`.
  - PNG IDAT assembly/compression now routes through `logic_layer.rust_accel.assemble_png_idat(...)`.
  - Fallback behavior remains deterministic because `rust_accel` preserves pure-Python path when Rust module is unavailable.
- Added dedicated regression coverage:
  - `tests/unit/logic_layer/test_minimap_png_exporter_rust_path.py`
    - validates `render_minimap_buffer` integration in floor export flow.
    - validates `assemble_png_idat` integration in `_write_png`.

## Incremental Update (2026-02-11 - Phase 12)
- Context-menu `select` actions hardened for backend capability parity:
  - `ItemContextMenu` now uses a centralized action registry (`_ITEM_SELECT_ACTIONS`) to keep legacy action order stable.
  - Added capability gates via `can_*` callbacks for dynamic enable/disable without breaking visibility of legacy entries.
  - `Move To Tileset...` now reflects runtime capability from user settings instead of always appearing actionable.
- Backend callback map expanded in `ContextMenuActionHandlers`:
  - Added `can_move_item_to_tileset()` and wired `can_move_to_tileset` callback.
  - Added `can_replace_tiles_on_selection()` and wired `can_selection_replace_tiles` callback for tile/item context menus.
  - Added `can_selection_paste` callback to align paste action enablement with session capability.
- Regression coverage added:
  - `tests/unit/logic_layer/test_context_menu_handlers.py`
    - `test_can_move_item_to_tileset_reflects_user_setting`
    - `test_item_context_callbacks_expose_can_move_to_tileset`
    - `test_tile_context_callbacks_expose_selection_replace_capability`
  - `tests/unit/vis_layer/ui/test_context_menus_select_actions.py` (new)
    - validates disabled state for `Move To Tileset...` when capability is false.
    - validates deterministic order for select actions (`Wallbrush` -> `Groundbrush` -> `Collection`).

## Incremental Update (2026-02-11 - Phase 13)
- Selection menu parity hardening (`Selection` top-level actions):
  - `QtMapEditorSessionMixin._update_action_enabled_states()` now controls all selection-scoped actions
    according to `session.has_selection()` (legacy-aligned enable/disable behavior):
    - `Replace Items on Selection`
    - `Find Item on Selection`
    - `Remove Item on Selection`
    - `Find Everything/Unique/Action/Container/Writeable (Selection)`
- Added regression coverage:
  - `tests/unit/vis_layer/ui/test_qt_map_editor_action_enabled_states.py` (new)
    - validates all selection-scoped actions disabled when no selection.
    - validates all selection-scoped actions enabled when selection exists.

## Incremental Update (2026-02-11 - Phase 14)
- Palette `select` menu parity/UX hardening (`Window > Palette`):
  - Palette actions are now `checkable` and grouped via exclusive `QActionGroup`,
    mirroring legacy "one active palette page" behavior.
  - Added two-way synchronization of menu checked-state with active palette:
    - menu trigger -> dock palette selection (`_select_palette`)
    - dock tab change -> checked menu action (`ModernPaletteDock._on_tab_changed`)
- Files updated:
  - `vis_layer/ui/main_window/build_actions.py`
  - `vis_layer/ui/main_window/qt_map_editor_palettes.py`
  - `vis_layer/ui/docks/modern_palette_dock.py`
- Regression update:
  - `tests/ui/test_toolbar_menu_sync.py` expanded with exclusive checked-state assertions.

## Incremental Update (2026-02-11 - Phase 15)
- Selection depth `select` menu hardening (`Selection > Selection Mode`):
  - Added centralized `_sync_selection_depth_actions(...)` in navigation mixin.
  - `build_actions` now delegates initial checked-state sync to the helper instead of local `if/elif` branching.
  - `_set_selection_depth_mode(...)` now reuses the same sync helper after session mode changes.
- Regression update:
  - `tests/ui/test_toolbar_menu_sync.py` expanded with depth-mode exclusivity and programmatic sync assertions.

## Incremental Update (2026-02-11 - Phase 16)
- Mirror axis `select` submenu hardening (`Mirror > Mirror Axis`):
  - Added explicit exclusive `QActionGroup` for `act_mirror_axis_x` and `act_mirror_axis_y`.
  - Kept runtime sync in `QtMapEditorMirrorMixin._sync_mirror_actions()` as source of truth.
- Regression update:
  - Added `tests/unit/vis_layer/ui/test_qt_map_editor_mirror.py` to validate axis exclusivity and invalid-axis fallback.

## Incremental Update (2026-02-11 - Phase 17)
- Brush shape selector hardening (`Sizes toolbar`):
  - Added explicit exclusive `QButtonGroup` for `shape_square` and `shape_circle`.
  - Initial checked-state now follows `editor.brush_shape` instead of hardcoded defaults.
- Regression update:
  - Added `tests/unit/vis_layer/ui/test_qt_map_editor_brushes_shape.py` to validate shape exclusivity and invalid-shape fallback.

## Incremental Update (2026-02-11 - Legacy Popup Parity Sweep)
- Varredura incremental no `remeres-map-editor-redux/source/ui/map_popup_menu.cpp` com foco em labels/fluxos de contexto.
- Paridade aplicada em `py_rme_canary`:
  - `Copy Position` agora usa formato Lua table (`{x=..., y=..., z=...}`) no clipboard (alinhado ao legado).
  - Menu de tile renomeado de `Browse Tile...` para `Browse Field` (label legado).
- Cobertura adicionada:
  - teste para formato de cópia de posição legado;
  - teste para presença do label `Browse Field` no `TileContextMenu`.

## Incremental Update (2026-02-11 - Window Menu parity: Tool Options)
- Gap encontrado na varredura de `menubar.xml`: faltava `Window > Tool Options` no Python.
- Implementado:
  - nova action `act_window_tool_options` em `build_actions.py`;
  - inclusão no menu `Window` em `build_menus.py`;
  - novo handler `open_tool_options(editor)` em `menubar/window/tools.py`;
  - novo método `_show_tool_options_panel()` em `qt_map_editor_docks.py` para exibir `dock_palette` e focar `tool_options`.
- Sincronização com arquitetura já existente:
  - reaproveita `ModernPaletteDock.tool_options` (sem criar dock paralelo redundante).

## Incremental Update (2026-02-11 - Context popup selection gating)
- Varredura do `map_popup_menu.cpp` indicou diferença no topo do menu de contexto:
  - no legado, `Copy Position` (atalho rápido de seleção) depende de seleção ativa.
- Ajuste aplicado no menu unificado Python (`ItemContextMenu`):
  - `Copy Position (x, y, z)` no bloco superior agora fica habilitado apenas quando há seleção.
  - cópia de posição no submenu `Copy Data` permanece disponível para contexto de item/tile.
- Regressão coberta com testes de estado `enabled` (sem seleção vs com seleção).

## Incremental Update (2026-02-11 - Window > Toolbars naming/order parity)
- Varredura do `menubar.xml` apontou divergência no submenu `Window > Toolbars`.
- Ajustes aplicados em `qt_map_editor_toolbars.py`:
  - ação `Brush ID` renomeada para `Brushes` (paridade de nomenclatura);
  - adicionada ação `Sizes` (paridade legada) apontando para o toolbar moderno de quick brush settings;
  - ordem do submenu alinhada ao legado: `Brushes`, `Position`, `Sizes`, `Standard`;
  - itens modernos (`Indicators`, `Tools`) mantidos após separador para preservar UX atual.
- Compatibilidade preservada:
  - `act_view_toolbar_brush_settings` mantida como alias para `act_view_toolbar_sizes`.

## Incremental Update (2026-02-11 - Copy Position format sync)
- Gap identificado entre UX/configuração e ação de menu:
  - `Preferences > Copy Position Format` existia, mas `_copy_position_to_clipboard` não aplicava o formato escolhido.
- Implementado em `qt_map_editor_edit.py`:
  - novo helper `format_position_for_copy(x, y, z, copy_format=...)`;
  - `_copy_position_to_clipboard` agora usa `UserSettings.get_copy_position_format()` e aplica o formato correto.
- Default alinhado ao legado: Lua table (`{x = X, y = Y, z = Z}`).

## Incremental Update (2026-02-11 - File menu Recent Files parity)
- `menubar.xml` revisitado: submenu `File > Recent Files` deve existir no builder principal (ordem legada).
- Ajustes aplicados:
  - `build_menus.py` agora cria `menu_recent_files` no `File` antes de `Preferences`.
  - `QtMapEditorModernUXMixin._setup_recent_files()` passa a reutilizar `menu_recent_files` quando já existe e só faz fallback para `menu_file.addMenu(...)` em builders customizados.
- Resultado: elimina risco de submenu duplicado e preserva ordem de menu alinhada ao legado.

## Incremental Update (2026-02-11 - Tile-only popup legacy select actions)
- Gap de paridade detectado no fluxo de tile sem item (menu unificado):
  - legado exibe `Select Creature` / `Select Spawn` / `Select House` quando contexto do tile suporta.
- Implementado:
  - `ContextMenuActionHandlers.get_tile_context_callbacks(...)` agora expõe callbacks condicionais:
    - `select_creature` quando tile possui monster/npc;
    - `select_spawn` quando tile possui spawn monster/npc;
    - `select_house` quando tile possui `house_id`.
  - `ItemContextMenu` (ramo `item is None`) agora renderiza essas ações quando disponíveis.

## Incremental Update (2026-02-11 - Top-level About menu label parity)
- Revisão do `menubar.xml` confirmou topo `About` no legado (não `Help`).
- Ajuste aplicado em `build_menus.py`:
  - menu superior renomeado para `About`, mantendo compatibilidade com atributo interno `menu_help`.

## Incremental Update (2026-02-11 - Navigate menu Zoom parity)
- Revisão incremental de `menubar.xml` confirmou submenu `Navigate > Zoom` no legado.
- Ajuste aplicado em `build_menus.py`:
  - adicionado submenu `Zoom` dentro de `Navigate` com ações já existentes:
    - `Zoom In`
    - `Zoom Out`
    - `Zoom Normal`
- Mantém o submenu `Editor > Zoom` já existente e adiciona o ponto de acesso legado em `Navigate`.

## Incremental Update (2026-02-11 - Navigate action labels parity)
- Ajuste de textos em `build_actions.py` para aproximar wording do legado em `Navigate`:
  - `Jump to Brush` -> `Jump to Brush...`
  - `Jump to Item` -> `Jump to Item...`
  - `Go To Previous Position` -> `Go to Previous Position`
  - `Go To Position` -> `Go to Position...`

## Incremental Update (2026-02-11 - Search labels and RAW naming parity)
- Ajuste textual de ações para refletir menu legado:
  - removidos sufixos `(Map)` e `(Selection)` das ações de busca (`Find Everything/Unique/Action/Container/Writeable`), já que o escopo é definido pelo menu onde aparecem.
  - label de palette `Raw` ajustado para `RAW`.
- Sem mudança de comportamento/handler, apenas paridade de nomenclatura e consistência de UI.

## Incremental Update (2026-02-11 - Browse Field enablement parity)
- Ajustado gating do `Browse Field` no menu de tile (sem item):
  - agora habilita quando há seleção ativa, mesmo sem ground/items no tile;
  - mantém habilitado também quando existem itens no tile.
- Objetivo: aproximar comportamento do popup legado orientado a seleção (`anything_selected`).

## Incremental Update (2026-02-11 - Selection Mode wording parity)
- Ajustados labels das ações de `Selection Mode` para corresponder ao legado:
  - `Compensate Selection`
  - `Current Floor`
  - `Lower Floors`
  - `Visible Floors`
- Mudança textual apenas (sem alteração de lógica dos modos).

## Incremental Update (2026-02-11 - Reload label parity)
- Ajuste textual da ação de recarga para refletir o legado (`Reload`):
  - `act_reload_data` em `build_actions.py` alterada de `Reload Data Files` para `Reload`.
- Sem alteração de comportamento/handler (`F5` permanece igual).

## Incremental Update (2026-02-11 - View/Show label casing parity)
- Ajustes de nomenclatura no `build_actions.py` para alinhamento textual com `remeres-map-editor-redux/data/menubar.xml`:
  - `Show all Floors`
  - `Show grid`
  - `Show tooltips`
  - `Show Light Strength`
  - `Show Technical Items`
  - `Highlight Items`
  - `Highlight Locked Doors`
  - `Show Wall Hooks`
- Escopo: somente labels/UX textual; sem alteração de handlers ou regras de negócio.

## Incremental Update (2026-02-11 - View/Show labels parity phase 2)
- Fechado bloco adicional de labels legados em `build_actions.py`:
  - `Show as Minimap`
  - `Only show Colors`
  - `Only show Modified`
  - `Show creatures`
  - `Show spawns`
- Escopo intencional: apenas paridade textual/UI, sem alterar os handlers já conectados ao backend.

## Incremental Update (2026-02-11 - Tile popup select parity phase 3)
- Fechada lacuna de paridade no popup de tile sem item selecionado (`ItemContextMenu` ramo `item is None`):
  - adicionadas ações legadas quando disponíveis:
    - `Select RAW`
    - `Select Wallbrush`
    - `Select Groundbrush`
    - `Select Collection`
- Backend (`ContextMenuActionHandlers.get_tile_context_callbacks`) passou a expor callbacks dessas ações com detecção de brush por contexto do tile (top item/ground + brush manager).
- Mantido comportamento de `Select Creature/Spawn/House` já existente.

## Incremental Update (2026-02-11 - TileContextMenu browse gating parity)
- Ajustado `TileContextMenu.show_for_tile(...)` para habilitar `Browse Field` quando há seleção ativa **mesmo sem itens/ground** no tile.
- Alinhamento com o comportamento legado baseado em `anything_selected`.
- Cobertura adicionada em `tests/unit/vis_layer/ui/test_context_menus_select_actions.py`.

## Incremental Update (2026-02-11 - TileContextMenu select actions sync)
- Sincronizado `TileContextMenu` com o menu unificado para exibir ações legadas `Select ...` quando callbacks existem:
  - `Select Creature`, `Select Spawn`, `Select RAW`, `Select Wallbrush`, `Select Groundbrush`, `Select Collection`, `Select House`.
- Objetivo: remover divergência de UX entre fluxos de popup de tile.

## Incremental Update (2026-02-11 - TileContextMenu capability gates)
- `TileContextMenu` passou a respeitar `can_*` para ações `Select ...`, alinhando com o comportamento do menu unificado.
- Exemplo coberto: `can_select_wall=False` mantém a ação visível porém desabilitada (paridade de UX de capacidade).

## Incremental Update (2026-02-11 - TileContextMenu browse capability gate)
- `TileContextMenu` passou a aplicar `can_browse_tile` (quando presente) para `Browse Field`.
- Mantido requisito de contexto (`has_selection` ou tile com itens/ground), agora combinado com capability gate para consistência com menu unificado.

## Incremental Update (2026-02-11 - Tile popup ordering parity)
- Ajustada a ordem no `TileContextMenu` para aproximar o legado:
  - ações `Select ...` vêm antes de `Properties...` e `Browse Field`.
  - `Browse Field` permanece no fechamento do bloco de tile.
- Objetivo: manter consistência visual/mental model com `map_popup_menu.cpp`.
