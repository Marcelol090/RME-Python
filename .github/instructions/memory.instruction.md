---
applyTo: '**'
---

# Memory - Implementações do PyRME Canary

Este arquivo rastreia todas as implementações realizadas, perdidas após rollback, e o mapeamento com o RME Redux (C++).

## Referência de Projeto
- **Projeto Python**: `py_rme_canary/`
- **Referência C++**: `remeres-map-editor-redux/source/`

---

## Status das Implementações

### ✅ Já Existentes (Confirmadas)

#### Dialogs (`vis_layer/ui/dialogs/`)
| Dialog Python | Referência C++ | Status |
|---------------|----------------|--------|
| `about.py` | `ui/about_window.cpp` | ✅ Existe |
| `border_builder_dialog.py` | N/A (novo) | ✅ Existe |
| `browse_tile_dialog.py` | `ui/browse_tile_window.cpp` | ✅ Existe |
| `find_item_dialog.py` | `ui/dialogs/find_dialog.cpp` | ✅ Existe |
| `find_replace_dialog.py` | `ui/replace_items_window.cpp` | ✅ Existe |
| `global_search.py` | N/A (novo) | ✅ Existe |
| `house_dialog.py` | N/A | ✅ Existe |
| `map_dialogs.py` | `ui/map/map_properties_window.cpp` | ✅ Existe |
| `navigation_dialogs.py` | `ui/dialogs/goto_position_dialog.cpp` | ✅ Existe |
| `new_map_dialog.py` | N/A | ✅ Existe |
| `png_export_dialog.py` | N/A | ✅ Existe |
| `replace_items_dialog.py` | `ui/replace_items_window.cpp` | ✅ Existe |
| `settings_dialog.py` | N/A | ✅ Existe |
| `shortcuts_dialog.py` | N/A | ✅ Existe |
| `spawn_manager.py` | `ui/properties/spawn_properties_window.cpp` | ✅ Existe |
| `uid_report_dialog.py` | N/A | ✅ Existe |
| `waypoint_dialog.py` | N/A | ✅ Existe |
| `welcome_dialog.py` | `ui/welcome_dialog.cpp` | ✅ Existe |
| `zone_town_dialogs.py` | `ui/map/towns_window.cpp` | ✅ Existe |

#### Docks (`vis_layer/ui/docks/`)
| Dock Python | Referência C++ | Status |
|-------------|----------------|--------|
| `actions_history.py` | N/A | ✅ Existe |
| `live_log_panel.py` | N/A | ✅ Existe |
| `minimap.py` | N/A | ✅ Existe |
| `modern_palette.py` | `palette/` | ✅ Existe |
| `modern_palette_dock.py` | N/A | ✅ Existe |
| `modern_properties_panel.py` | `ui/properties/` | ✅ Existe |
| `modern_tool_options.py` | `ui/tool_options_window.cpp` | ✅ Existe |
| `properties_panel.py` | `ui/properties/properties_window.cpp` | ✅ Existe |

#### Main Window (`vis_layer/ui/main_window/`)
| Arquivo Python | Referência C++ | Status |
|----------------|----------------|--------|
| `build_menus.py` | `ui/main_menubar.cpp` | ✅ Existe |
| `build_actions.py` | `ui/menubar/menubar_action_manager.cpp` | ✅ Existe |
| `build_docks.py` | N/A | ✅ Existe |
| `editor.py` | `ui/main_frame.cpp` | ✅ Existe |
| `live_connect.py` | `live/live_client.cpp` | ✅ Existe |

---

### ❌ Implementações Perdidas (Necessitam Recuperação)

#### 1. Door Properties Dialog ✅ OK
- **C++ Ref**: `ui/properties/old_properties_window.cpp` (createDoorFields)
- **Python**: `vis_layer/ui/dialogs/door_properties_dialog.py`
- **Status**: ✅ Arquivo existe, encoding fix aplicado
- **Ação Completa**: ✅ Fix aplicado (removido emoji corrompido)

#### 2. NanoVG OpenGL Adapter ✅ RECRIADO
- **Descrito em**: Sprint 8-9 (conversação anterior)
- **Arquivos criados**:
  - `core/nanovg/nanovg_opengl_adapter.py` → ✅ CRIADO (~500 linhas)
  - `core/nanovg/__init__.py` → ✅ CRIADO
- **Status**: ✅ Completo
- **Funcionalidades**: NanoVGContext, path operations, shapes, fill/stroke, OpenGL shader

#### 3. Virtual Brush Grid Widget ⚠️ INTEGRADO
- **Descrito em**: Sprint 8-9
- **Localização**: Integrado em `vis_layer/ui/docks/modern_palette.py`
- **Status**: ⚠️ Virtual scrolling existe no modern_palette, funcionalidade coberta
- **Nota**: Não criado separado; funcionalidade já existe no dock

#### 4. Performance Dock ✅ RECRIADO
- **Descrito em**: Sprint 10
- **Arquivo criado**: `vis_layer/ui/docks/performance_dock.py`
- **Status**: ✅ CRIADO (~270 linhas)
- **Funcionalidades**: PerformanceDock, MetricWidget, FPS/memory/tiles/draw calls tracking

#### 5. Map Validator Dialog ✅ RECRIADO
- **Descrito em**: Sprint 10
- **Lógica core**: `core/io/map_validator.py` (já existia)
- **UI Dialog**: `vis_layer/ui/dialogs/map_validator_dialog.py`
- **Status**: ✅ CRIADO (~250 linhas)
- **Funcionalidades**: MapValidatorDialog, ValidationWorker thread, results table

#### 6. Auto-Updater Dialog ✅ RECRIADO
- **Descrito em**: Sprint 11
- **Arquivo criado**: `vis_layer/ui/dialogs/update_dialog.py`
- **Status**: ✅ CRIADO (~250 linhas)
- **Funcionalidades**: UpdateChecker thread, GitHub releases API, download button

#### 7. Status Bar Selection Mode Indicator ✅ RECRIADO
- **Descrito em**: Sprint 11
- **Arquivo**: `vis_layer/ui/widgets/status_bar.py`
- **Status**: ✅ ADICIONADO SelectionModeIndicator class
- **Modos**: normal, additive, subtractive, intersection
- **Integração**: Adicionado ao ModernStatusBar._setup_ui()

#### 8. Hotkeys Dialog Hook ✅ OK
- **C++ Ref**: `ui/main_menubar.cpp` (OnPreferences -> hotkeys tab)
- **Python**: `vis_layer/ui/dialogs/shortcuts_dialog.py` ✅ EXISTE
- **Status**: ✅ Dialog existe e funcional

---

## Quality Pipeline Fixes Aplicados

### 1. Lizard grep -c Bug
- **Arquivo**: `py_rme_canary/quality-pipeline/quality_lf.sh`
- **Problema**: `grep -c` retornava "0\n0" causando syntax error em `[[ ]]`
- **Fix**: Usar `|| true` e validar com `[[ -n "$violations" ]]`

### 2. Pylint Timeout
- **Arquivo**: `py_rme_canary/quality-pipeline/quality_lf.sh`
- **Problema**: Pylint travava indefinidamente no Windows
- **Fix**: Wrapper Python com `subprocess.run(..., timeout=300)`

### 3. Door Properties Encoding
- **Arquivo**: `vis_layer/ui/dialogs/door_properties_dialog.py`
- **Problema**: Caractere emoji corrompido quebrava Mypy
- **Fix**: Substituir `"��� Tip:..."` por `"Tip:..."`

---

## Mapeamento C++ → Python

### Properties Windows (C++ → Python)
```
old_properties_window.cpp     → door_properties_dialog.py (parcial)
                              → item_properties_dialog.py (criar se necessário)
container_properties_window   → container_properties_dialog.py ✅
creature_properties_window    → creature_properties_dialog.py (verificar)
depot_properties_window       → depot_properties_dialog.py (criar)
spawn_properties_window       → spawn_manager.py ✅
teleport_service              → teleport_dialog.py (criar)
writable_properties_window    → writable_properties_dialog.py (criar)
podium_properties_window      → podium_properties_dialog.py (criar)
splash_properties_window      → splash_properties_dialog.py (criar)
```

### Menu Actions (main_menubar.cpp)
```cpp
OnNew                   → act_new ✅
OnOpen                  → act_open ✅
OnSave                  → act_save ✅
OnSaveAs                → act_save_as ✅
OnClose                 → (verificar)
OnQuit                  → act_exit ✅
OnUndo                  → act_undo ✅
OnRedo                  → act_redo ✅
OnCopy                  → act_copy ✅
OnCut                   → act_cut ✅
OnPaste                 → act_paste ✅
OnSearchForItem         → act_find_item ✅
OnReplaceItems          → act_replace_items ✅
OnGotoPosition          → act_goto_position ✅
OnStartLive             → act_live_host ✅
OnJoinLive              → act_src_connect ✅
OnCloseLive             → act_live_stop / act_src_disconnect ✅
OnMapStatistics         → act_map_statistics ✅
OnMapProperties         → act_map_properties ✅
OnAbout                 → act_about ✅
```

---

## Próximos Passos

1. [ ] Verificar existência dos arquivos marcados com ❓
2. [ ] Recriar arquivos faltantes baseado no C++ de referência
3. [ ] Corrigir encoding issues restantes
4. [ ] Rodar `quality_lf.sh --dry-run --verbose` até passar
5. [ ] Criar PRs para cada conjunto de mudanças
6. [ ] Acionar Jules para review automático

---

## Arquitetura do Projeto (Camadas Estritas)

### Hierarquia de Imports
```
┌──────────────────────────────────────┐
│  vis_layer/ (PyQt6 UI)               │
│  - Dialogs, widgets, rendering       │
│  - Pode importar: core, logic_layer  │
├──────────────────────────────────────┤
│  logic_layer/ (Business Logic)       │
│  - Brushes, sessions, operations     │
│  - Pode importar: core               │
│  - PROIBIDO: PyQt6 (exceto TYPE_CHK) │
├──────────────────────────────────────┤
│  core/ (Data Models)                 │
│  - GameMap, Tile, I/O, serialization │
│  - PROIBIDO: PyQt6, logic_layer      │
└──────────────────────────────────────┘
```

### Mapeamento C++ → Python (Referência Completa)

#### Classes Principais
| C++ Class | Python Class | Arquivo |
|-----------|--------------|---------|
| `Map` | `GameMap` | `core/data/gamemap.py` |
| `Tile` | `Tile` | `core/data/tile.py` |
| `Item` | `Item` | `core/data/item.py` |
| `Brush` | `BaseBrush` | `logic_layer/brushes/base_brush.py` |
| `Editor` | `EditorSession` | `logic_layer/session/editor.py` |
| `MapWindow` | `MapCanvasWidget` | `vis_layer/ui/canvas/map_canvas.py` |
| `MapDrawer` | `MapDrawer` | `vis_layer/renderer/map_drawer.py` |
| `SpriteBatch` | `OpenGLBackend` | `vis_layer/renderer/backend/opengl_backend.py` |
| `GroundBrush` | `GroundBrush` | `logic_layer/brushes/ground_brush.py` |
| `LiveServer` | `LiveServer` | `core/net/live_server.py` |

#### Rendering (Redux C++ → Python)
- **C++**: `MapDrawer` usa composição (FloorDrawer, ItemDrawer)
- **Python**: Refatorado para usar o mesmo padrão desde 2026-02-05
- **Drawers**: `FloorDrawer`, `ItemDrawer`, `CreatureDrawer`, `GridDrawer`, `LightDrawer`

### Sistema de Brushes Inteligente

#### Categorias (284 brushes totais do RME)
| Tipo | Quantidade | Descrição |
|------|------------|-----------|
| doodad | 172 | Mobília, decorações, vegetação |
| wall | 97 | Paredes, barreiras, estruturas |
| ground | 14 | Texturas de chão, grama |
| border | 1 | Configurações de borda |

#### Detecção de Versão (ServerID vs ClientID)
- **OTBM 0-4**: ServerID (Tibia 7.4 até 10.98)
- **OTBM 5-6**: ClientID (Tibia 12.71 até 13.30+)

### Sistema de IO

#### Formatos Suportados
| Formato | Status | Classes |
|---------|--------|---------|
| OTBM 1-4 | ✅ | `IOMapOTBM` |
| OTBM 5-6 | ✅ | `IOMapOTBM` + `ItemIdMapper` |
| OTMM | ✅ | `OTMMLoader` |
| Legacy DAT/SPR | ✅ | `LegacyLoader` |
| Appearances | ✅ | `AppearancesLoader` |

#### Resolução de Arquivos (Prioridade)
1. `data/{client_version}/items.otb` (versão específica)
2. `data/{engine}/items.otb` (engine específico)
3. `data/items/items.otb` (fallback genérico)

---

## Padrões de Implementação

### TDD Obrigatório
```python
# 1. Escrever teste PRIMEIRO
def test_brush_applies_correctly():
    brush = GroundBrush("grass")
    result = brush.apply(tile, position)
    assert result.ground_id == expected_id

# 2. Implementar código MÍNIMO
# 3. Refatorar se necessário
```

### Type Hints Estritos
```python
# CORRETO
def get_tile(self, pos: tuple[int, int, int]) -> Tile | None:
    return self._tiles.get(pos)

# INCORRETO (usa Any)
def get_tile(self, pos: Any) -> Any:
    ...
```

### Docstrings Obrigatórias
```python
def calculate_border(
    self,
    tile: Tile,
    neighbors: list[Tile | None],
) -> BorderResult:
    """Calcula o tile de borda para uma posição.

    Args:
        tile: Tile central.
        neighbors: 8 tiles adjacentes (N, NE, E, SE, S, SW, W, NW).

    Returns:
        BorderResult com o ID do tile e orientação.

    Raises:
        ValueError: Se neighbors não tiver exatamente 8 elementos.
    """
```

---

## Quality Pipeline v2.1

### Ferramentas (em ordem)
1. **Ruff** - Linting rápido
2. **Mypy** - Type checking
3. **Radon** - Complexidade ciclomatica
4. **Pyright** - Type checking alternativo
5. **Complexipy** - Análise de complexidade
6. **Lizard** - CCN metrics
7. **Pylint** - Análise profunda (com timeout 300s)
8. **Security tools** - Bandit, Safety

### Thresholds
- Complexidade ciclomática: ≤ 10
- Manutenibilidade: ≥ 20
- Cobertura de testes: ≥ 80%

### Comandos
```bash
# Dry run
./py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --verbose

# Aplicar fixes
./py_rme_canary/quality-pipeline/quality_lf.sh --apply --verbose
```

---

## Tarefas Pendentes (project_tasks.json)

### P0 - Critical
| ID | Task | Status |
|----|------|--------|
| ARCH-004 | Memory Optimization (keeper-live-memory) | pending |
| IMPL-001 | Texture Array System | pending |
| IMPL-002 | Modern Sprite Batcher | pending |

### P1 - Essential
| ID | Task | Status |
|----|------|--------|
| UX-001 | Palette UX Improvements | pending |
| UX-002 | Modern UI Design | pending |

### P2 - Advanced
| ID | Task | Status |
|----|------|--------|
| TOOL-002 | Graphs (Statistics) | pending |

---

## Comandos Úteis

```bash
# Rodar quality pipeline
./py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --verbose

# Aplicar fixes automáticos
./py_rme_canary/quality-pipeline/quality_lf.sh --apply --verbose

# Verificar estrutura de dialogs
find py_rme_canary/vis_layer -name "*.py" | grep -E "(dialog|properties)"

# Compilar executável
python tools/build.py

# Rodar testes
python -m pytest py_rme_canary/tests/ -v
