# Análise Comparativa: Funcionalidades Faltantes no py_rme_canary

> ⚠️ **Redundância removida:**
> The master checklist is now in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md). This file contains only deep-dive analysis and context for ambiguous or complex features. For actionable status, use the master checklist.

## 📋 Sumário Executivo

Este documento apresenta uma análise profunda comparando as funcionalidades implementadas no código C++ original (`source/`) com o que está disponível na implementação Python (`py_rme_canary/`). O objetivo é identificar todas as funcionalidades que ainda precisam ser implementadas ou estão incompletas.

**Data da Análise:** 2025-01-XX
**Versão C++ Analisada:** Remere's Map Editor (Canary)
**Versão Python:** py_rme_canary

---

## 🎯 Categorias de Funcionalidades

### 1. Sistema de Brushes (Pincéis)

#### ✅ Implementado no Python
- ✅ GroundBrush (Terreno) - `logic_layer/brush_definitions.py`
- ✅ WallBrush (Paredes) - `logic_layer/brush_definitions.py`
- ✅ Auto-border básico - `logic_layer/auto_border.py`
- ✅ BrushManager com carregamento de JSON - `logic_layer/brush_definitions.py`
- ✅ BrushFactory básico - `logic_layer/brush_definitions.py`

##### 1.1 Tipos de Brushes Especializados (Implementados)
- ✅ **TableBrush** - `TableBrushSpec` em `brush_definitions.py` + testes em `test_table_brush.py`
- ✅ **CarpetBrush** - `CarpetBrushSpec` em `brush_definitions.py` + testes em `test_carpet_brush.py`
- ✅ **DoorBrush** - `DoorBrush` em `door_brush.py` + `switch_door()` + testes em `test_door_brush.py`
- ✅ **DoodadBrush** - `DoodadBrushSpec` em `brush_definitions.py`
- ⚠️ **HouseBrush** - Virtual brush via paleta (metadata-only)
- ⚠️ **HouseExitBrush** - Virtual brush via paleta (metadata-only)
- ⚠️ **WaypointBrush** - Virtual brush via paleta + waypoint_virtual_id
- ✅ **MonsterBrush** - `MonsterBrush` em `monster_brush.py` + testes em `test_brushes.py`
- ✅ **NpcBrush** - `NpcBrush` em `npc_brush.py` + testes em `test_brushes.py`
- ⚠️ **SpawnMonsterBrush** - Via VIRTUAL_SPAWN_MONSTER_TOOL_ID na paleta
- ⚠️ **SpawnNpcBrush** - Via VIRTUAL_SPAWN_NPC_TOOL_ID na paleta
- ✅ **FlagBrush** - `FlagBrush` em `flag_brush.py` + testes em `test_brushes.py`
- ⚠️ **ZoneBrush** - Virtual brush via paleta (VIRTUAL_ZONE_BASE)
- ⚠️ **OptionalBorderBrush** - Via VIRTUAL_OPTIONAL_BORDER_ID na paleta
- ✅ **EraserBrush** - `EraserBrush` em `eraser_brush.py` + testes em `test_brushes.py`

##### 1.2 Funcionalidades Avançadas de Brushes
- ✅ **BrushShape** - `BrushShape` enum (SQUARE, CIRCLE) em `brush_settings.py`
- ✅ **Brush Size** - `BrushSettings.size` configurável em `brush_settings.py`
- ⚠️ **Brush Variation** - Parcialmente implementado via random selection
- ⚠️ **Brush Thickness** - Parcialmente implementado
- ✅ **Recent Brushes** - Palette "Recent" implementada em `palette.py`
- ⚠️ **Brush Drag** - Parcialmente implementado via gestures
- ⚠️ **Brush Smear** - Parcialmente implementado para alguns tools
- ✅ **apply_brush_with_size()** - Função em `brush_settings.py`
- ✅ **TransactionalBrushStroke** - Em `transactional_brush.py`
- ✅ **test_brush_footprint.py** - Testes de footprint implementados

##### 1.3 Sistema de Auto-Border Avançado
- ❌ **Border Builder Window** - Interface para construir bordas customizadas (pendente)
- ✅ **Border Groups** - Agrupamento de bordas relacionadas
- ✅ **Border Friends/Hate** - Sistema de compatibilidade entre brushes
- ✅ **Ground Equivalents** - Equivalências de terreno para bordas

---

### 2. Sistema de Editor e Sessão

#### ✅ Implementado no Python
- ✅ EditorSession básico
- ✅ Sistema de seleção (box selection)
- ✅ Clipboard (copy/cut/paste)
- ✅ Undo/Redo básico
- ✅ Gestos de mouse (down/move/up)
- ✅ Movimentação de seleção

#### ❌ Faltante no Python

##### 2.1 Operações de Seleção Avançadas
- ✅ **Selection Modes** (`logic_layer/session/selection_modes.py`):
  - ✅ SELECT_MODE_COMPENSATE - Compensar altura (default legacy behavior)
  - ✅ SELECT_MODE_CURRENT - Apenas andar atual
  - ✅ SELECT_MODE_LOWER - Andares inferiores
- ✅ **Search on Selection** (2026-01-28) - `search_items_in_selection()` em `logic_layer/operations/selection_operations.py`
- ✅ **Count Monsters in Selection** (2026-01-28) - `count_monsters_in_selection()` retorna totais e posições
- ✅ **Remove Duplicates in Selection** (2026-01-28) - `remove_duplicates_in_selection()` remove itens duplicados por ID
- ✅ **Remove on Selection** - Via `remove_items_in_map(selection_only=True)` já existente
- ✅ **Find Creature** (VERIFIED 2026-01-28) - `find_item.py::open_find_dialog()` com modo "creature" + `FindEntityDialog` em dialogs.py
  - ✅ SELECT_MODE_VISIBLE - Apenas visíveis (`get_floors_for_selection`)
- ✅ **Duplicate Selection** - `duplicate_selection()` → `_duplicate_selection()` implementado
- ✅ **Move Selection Up/Down** - `move_selection_z()` → `_move_selection_z(direction)` implementado
- ⚠️ **Clear Selection** - Parcialmente implementado via SelectionManager

##### 2.2 Operações de Mapa
- ✅ **Borderize Selection** - `borderize_selection()` implementado em editor.py
- ❌ **Borderize Map** - Aplicar bordas em todo o mapa (pendente)
- ✅ **Randomize Selection** - `randomize_selection()` implementado em editor.py
- ✅ **Randomize Map** - `randomize_map()` implementado em editor.py
- ✅ **Clear Invalid House Tiles** - `clear_invalid_tiles()` implementado em editor.py
- ✅ **Clear Modified Tile State** - `clear_modified_state()` implementado em editor.py

##### 2.3 Sistema de Ações (Actions)
- ✅ **ActionQueue** (`logic_layer/session/action_queue.py`):
  - ✅ Stacking delay (agrupamento automático de ações)
  - ✅ Batch actions (CompositeAction para ações em lote)
  - ✅ Action labels (rótulos descritivos via `DEFAULT_LABELS`)
  - ✅ Action timer (reset de timer via `reset_timer()`)
- ❌ **NetworkedActionQueue** - Para modo live
- ✅ **ActionType enum** (41 tipos implementados em `action_queue.py`):
  - ✅ PAINT (= ACTION_DRAW)
  - ✅ DELETE_SELECTION (= ACTION_DELETE_TILES)
  - ✅ MOVE_SELECTION (= ACTION_MOVE)
  - ✅ BORDERIZE_SELECTION (= ACTION_BORDERIZE)
  - ✅ REPLACE_ITEMS (= ACTION_REPLACE_ITEMS)
  - ✅ RANDOMIZE_SELECTION, RANDOMIZE_MAP
  - ✅ SWITCH_DOOR (= ACTION_SWITCHDOOR)
  - ✅ + 30 outros tipos adicionais

---

### 3. Sistema de Renderização e Visualização

#### ✅ Implementado no Python
- ✅ MapCanvasWidget básico (PyQt6)
- ✅ Renderização básica de tiles
- ✅ Viewport com zoom
- ✅ Minimap básico

#### ✅ Recentemente Implementado

##### 3.1 Renderização OpenGL
- ✅ **OpenGL Context** - Contexto GL para renderização acelerada (`OpenGLCanvasWidget`)
- ✅ **MapDrawer** completo com:
  - ✅ Renderização de sprites com OpenGL e QPainter backends
  - ✅ Sistema de camadas (layers via `RenderFrame`)
  - ✅ Renderização de pisos superiores/inferiores
  - ✅ Sombreado (shade) de pisos inferiores (`draw_shade_overlay`)
  - ✅ Renderização de seleção (`draw_selection_rect`)
  - ✅ Renderização de brush preview
  - ✅ Renderização de grid (`draw_grid_rect`)
  - ✅ Renderização de "ingame box"
  - ✅ Renderização de tooltips (`draw_text`)
  - ❌ Renderização de cursors live (pendente)
  - ❌ Renderização de dragging shadow (pendente)

##### 3.2 Sistema de Sprites (✅ Implementado 2026-01-23)
- ✅ **Asset Profile System** (`core/assets/asset_profile.py`):
  - ✅ Auto-detecção de assets modern vs legacy
  - ✅ Detecção de conflito (modern + legacy no mesmo diretório)
- ✅ **Legacy DAT/SPR Loader** (`core/assets/legacy_dat_spr.py`):
  - ✅ Carregamento de sprites de arquivos Tibia.dat/Tibia.spr
  - ✅ Decode RLE de sprites 32x32
  - ✅ Cache LRU com integração MemoryGuard
- ✅ **Appearances DAT Parser** (`core/assets/appearances_dat.py`):
  - ✅ Carregamento de protobuf appearances.dat
  - ✅ `SpriteAnimation` com duração de fases e loop types
  - ✅ `phase_index_for_time()` para seleção de frame por tempo
  - ✅ Mapeamento appearance_id → sprite_id
- ✅ **SpriteAppearances** (`core/assets/sprite_appearances.py`):
  - ✅ Carregamento de catalog-content.json (modern client)
  - ✅ Sprite sheets PNG
  - ✅ Cache de sprites com MemoryGuard
- ✅ **Asset Loader Unificado** (`core/assets/loader.py`):
  - ✅ `load_assets_from_path()` com auto-detecção
  - ✅ `LoadedAssets` dataclass com sprite_assets + appearance_assets
- ✅ **Animation Clock** (`editor.py`):
  - ✅ `animation_time_ms()` para tempo de animação
  - ✅ `advance_animation_clock()` para avanço de animação
  - ✅ `_resolve_sprite_id_from_client_id()` com suporte a animação

#### ✅ Implementado (DrawingOptions Completo)

##### 3.3 Opções de Visualização (`logic_layer/drawing_options.py`)
- ✅ **DrawingOptions** completo:
  - ✅ `show_shade` - Mostrar sombra
  - ✅ `show_all_floors` - Mostrar todos os andares
  - ✅ `show_ingame_box` - Mostrar caixa in-game
  - ✅ `show_lights` - Mostrar iluminação
  - ✅ `show_grid` - Mostrar grade (0=off, 1=normal, 2=thick)
  - ✅ `show_monsters` - Mostrar monstros
  - ✅ `show_spawns_monster` - Mostrar spawns de monstros
  - ✅ `show_npcs` - Mostrar NPCs
  - ✅ `show_spawns_npc` - Mostrar spawns de NPCs
  - ✅ `show_special_tiles` - Mostrar tiles especiais
  - ✅ `show_as_minimap` - Mostrar como minimap
  - ✅ `show_only_colors` - Mostrar apenas cores
  - ✅ `show_only_modified` - Mostrar apenas modificados
  - ✅ `show_houses` - Mostrar casas
  - ✅ `show_pathing` - Mostrar pathfinding
  - ✅ `show_tooltips` - Mostrar tooltips
  - ✅ `show_preview` - Mostrar preview
  - ✅ `show_hooks` - Mostrar ganchos de parede
  - ✅ `show_pickupables` - Mostrar itens coletáveis
  - ✅ `show_moveables` - Mostrar itens móveis
  - ✅ `show_avoidables` - Mostrar itens evitáveis
  - ✅ `show_blocking` - Mostrar itens bloqueantes
  - ✅ `show_items` - Mostrar itens
  - ✅ `TransparencyMode` enum (NONE, FLOORS, ITEMS, BOTH)

##### 3.4 Sistema de Iluminação
- ✅ **LightDrawer** - `show_lights` agora ativa a renderização completa com overlay ambiente e brilhos por tile.
- ✅ **Cálculo de iluminação** baseado em heurísticas de itens/zones + `LightSettings`.
- ✅ **Visualização de intensidade** com labels numéricos quando `show_light_strength` está ligado.
- ✅ **Cores de luz customizáveis** expostas via `LightColor`/`LightSettings` preset (daylight/twilight/night/cave).

##### 3.5 Screenshots & Export
- ✅ **Minimap Export** - Export PNG via `tools/minimap_export.py`
- ✅ **Take Screenshot** - `_take_screenshot()` em qt_map_editor_view.py (F10 shortcut, PNG format)
- ❌ Suporte a BMP/JPEG (pendente)

##### 3.6 Preferences/Settings Window & Dialogs (✅ Implementado 2026-01-23)
- ✅ **Preferences Window** - Dialog de configurações com abas (`preferences_dialog.py` → 337 linhas):
  - ✅ General tab (welcome dialog, backups, updates, single instance, undo settings, worker threads)
  - ✅ Editor tab (placeholder for editor-specific settings)
  - ✅ Graphics tab (placeholder for rendering options)
  - ✅ Interface tab (placeholder for UI customization)
  - ✅ Client Folder tab (asset folder selection with directory picker)
  - ✅ Position format radio buttons (5 formats: Lua table, JSON, x/y/z, (x,y,z), Position())
  - ✅ Apply/OK/Cancel buttons with settings persistence
- ✅ **Add Item Window** - Dialog para adicionar itens a tilesets (`add_item_dialog.py` → 127 linhas):
  - ✅ Item selection by server ID (spinbox 100-100000)
  - ✅ Item info display (ID + name from database)
  - ✅ Tileset integration (item addition to material groups)
- ✅ **Browse Tile Window** - Dialog para navegar items em tile (`browse_tile_dialog.py` → 175 linhas):
  - ✅ List all items on tile (ground + items in reverse order)
  - ✅ Select/deselect items (extended selection mode)
  - ✅ Remove selected items from tile
  - ✅ Show item properties (double-click or button)
  - ✅ Tile position display
- ✅ **Container Properties Window** - Dialog para editar containers (`container_properties_dialog.py` → 120 linhas):
  - ✅ Container items list widget
  - ✅ Add items to container (button with placeholder)
  - ✅ Remove items from container
  - ✅ Item name display from database
- ✅ **Import Map Dialog** - Dialog para importar mapa com offset (`import_map_dialog.py` → 177 linhas):
  - ✅ File selection with OTBM filter
  - ✅ X/Y/Z offset spinboxes (ranges: X/Y: ±32768, Z: ±8)
  - ✅ Import options checkboxes (tiles, houses, spawns, zones)
  - ✅ Merge mode radio buttons (Merge/Replace/Skip for items/creatures)
  - ✅ Settings export method for backend integration
- **Nota:** Python usa arquivos de configuração (.toml) + estes dialogs para configuração completa

---

### 4. Sistema de Live Server/Client (Colaboração em Tempo Real)

#### ⚠️ Parcialmente Implementado (`core/protocols/`)

##### 4.1 Live Server (`live_server.py`)
- ✅ **LiveServer** classe:
  - ✅ Bind em porta TCP (`start()`)
  - ✅ Aceitar conexões de clientes (`_accept_loop()`)
  - ✅ Broadcast de mudanças para clientes (`broadcast()`)
  - ✅ Gerenciamento de clientes conectados (`_peers` dict)
  - ✅ Sistema de IDs de cliente (`client_id`)
  - ✅ Disconnect handler (`_disconnect_client()`)
  - ✅ Login payload decode (`_decode_login_payload()`)
  - ❌ Chat entre clientes (pendente)
  - ❌ Broadcast de cursors (pendente)
  - ❌ Broadcast de operações/progress bars (pendente)
  - ❌ Kick de clientes (pendente)

##### 4.2 Live Client (`live_client.py`)
- ✅ **LiveClient** classe (extends LiveSocket):
  - ✅ Conectar a servidor (`connect()`)
  - ✅ Enviar pacotes (`send_packet()`)
  - ✅ Receber pacotes (`_receive_loop()`, `pop_packet()`)
  - ✅ Login payload encode (`_encode_login_payload()`)
  - ✅ Disconnect (`disconnect()`)
  - ❌ Request de nodes/regiões (pendente)
  - ❌ Sincronização de estado completa (pendente)
  - ❌ Chat com outros clientes (pendente)
  - ❌ Visualização de cursors (pendente)

##### 4.3 Live Socket (`live_socket.py`)
- ✅ **LiveSocket** - Base para server/client
- ✅ **PacketType** enum (LOGIN, TILE_UPDATE, etc.)
- ✅ Protocolo de comunicação (`send_packet()`, `recv_packet()`)
- ✅ Parsing de pacotes (header + payload)
- ✅ Envio de mensagens

##### 4.4 Live Peer
- ✅ **Peer tracking** em `_peers` dict no LiveServer
- ✅ Gerenciamento de conexão individual
- ✅ Envio/recebimento de dados
- ❌ LivePeer como classe dedicada (pendente)

##### 4.5 Live Tab
- ⚠️ **ConnectDialog** - Interface básica para conexão (vis_layer/ui/main_window/live_connect.py)
- ❌ Log de atividades (pendente)
- ❌ Lista de clientes conectados (pendente)
- ❌ Chat interface (pendente)

---

### 5. Sistema de Importação/Exportação

#### ✅ Implementado no Python
- ✅ **OTBM Load** (`core/io/otbm/`) - Carregamento OTBM v1/v2 com streaming parser
- ✅ **OTBM Save** (`core/io/otbm/`) - Salvamento OTBM com atomic writes
- ✅ **OTMM Load** (`core/io/otmm.py`) - `load_otmm()` com suporte completo:
  - ✅ Tiles, items, houses, spawns, towns
  - ✅ Monster/NPC spawn areas
  - ✅ House data e tile flags
- ✅ **OTMM Save** (`core/io/otmm_saver.py`) - `save_otmm_atomic()` com roundtrip tests
- ✅ Carregamento de XML (houses.xml, spawns.xml, zones.xml)
- ✅ Detecção automática de formato (OTBM vs OTMM via magic bytes)

#### ⚠️ Parcialmente Implementado

##### 5.1 Importação
- ✅ **Import Map** - Importar mapa com offset (`import_map_dialog.py`)
- ✅ **Import Monsters/NPCs** - Importar monstros LUA (`lua_creature_import.py`)
  - ✅ Importação de arquivo único
  - ✅ Importação de pasta recursiva (`qt_map_editor_file.py`)
- ❌ **Import Minimap** - Importar minimap com offset (pendente)

##### 5.2 Exportação
- ✅ **Export Minimap** - `tools/minimap_export.py`:
  - ✅ PNG format
  - ✅ Seleção de floor
  - ❌ Formato BMP (pendente)
- ❌ **Export Tilesets** - Exportar tilesets (pendente)

##### 5.3 Formatos Suportados
- ✅ **OTBM v1/v2** - Loader + Saver completo
- ✅ **OTMM** - Loader + Saver + roundtrip tests
- ✅ **XML** - Houses, Spawns, Zones
- ❌ Conversão automática entre formatos (pendente)

---

### 6. Sistema de Busca e Substituição

#### ✅ Implementado no Python
- ✅ Busca básica de itens (`map_search.py`)
- ✅ **FindItemDialog** - Diálogo de busca em dialogs.py
- ✅ **FindEntityDialog** - Busca avançada (Item/Creature/House tabs)
- ✅ **ReplaceItemsDialog** - Diálogo de substituição em dialogs.py
- ✅ Busca de waypoints
- ✅ Estatísticas básicas do mapa
- ✅ **Replace Items** (`replace_items.py`):
  - ✅ `replace_items_in_tile()` - Substituição em tile individual
  - ✅ `replace_items_in_map()` - Substituição em todo o mapa
- ✅ **Remove Items** (`remove_items.py`):
  - ✅ `remove_items_in_tile()` - Remoção em tile individual
  - ✅ `remove_items_in_map()` - Remoção em todo o mapa
  - ✅ `find_items_in_map()` - Busca de itens no mapa
- ✅ **Editor Methods** (`session/editor.py`):
  - ✅ `replace_items()` - Método de alto nível
  - ✅ `remove_items()` - Método de alto nível
- ✅ **Find Item Positions** (`map_search.py`):
  - ✅ `find_item_positions()` - Busca posições de item

#### ⚠️ Parcialmente Faltante no Python

##### 6.1 Busca Avançada
- ⚠️ **Search on Map** - Implementado parcialmente:
  - ❌ SEARCH_ON_MAP_EVERYTHING - Buscar tudo
  - ❌ SEARCH_ON_MAP_UNIQUE - Buscar únicos
  - ❌ SEARCH_ON_MAP_ACTION - Buscar com action
  - ❌ SEARCH_ON_MAP_CONTAINER - Buscar containers
  - ❌ SEARCH_ON_MAP_WRITEABLE - Buscar writeables
  - ❌ SEARCH_ON_MAP_DUPLICATED_ITEMS - Buscar itens duplicados
  - ❌ SEARCH_ON_MAP_WALLS_UPON_WALLS - Buscar paredes sobre paredes

##### 6.2 Busca em Seleção
- ❌ **Search on Selection** (pendente)

##### 6.3 Substituição (Parcialmente Implementado)
- ✅ **Replace Items** - Substituir itens no mapa
- ❌ **Replace on Selection** - Substituir itens na seleção (pendente)
- ✅ **Remove Items** - Remover itens específicos
- ❌ **Remove on Selection** - Remover itens da seleção (pendente)
- ❌ **Remove Monsters** - Remover monstros da seleção (pendente)
- ❌ **Count Monsters** - Contar monstros na seleção (pendente)
- ❌ **Remove Duplicates** - Remover duplicados (pendente)

##### 6.4 Busca de Criaturas
- ❌ **Find Creature** - Buscar criaturas (monstros/NPCs) no mapa (pendente)

---

### 7. Sistema de Limpeza e Manutenção do Mapa

#### ❌ Completamente Faltante

- ❌ **Map Cleanup** - Limpeza geral do mapa
- ❌ **Map Remove Items** - Remover itens específicos do mapa
- ❌ **Map Remove Corpses** - Remover corpos do mapa
- ❌ **Map Remove Unreachable Tiles** - Remover tiles inacessíveis
- ❌ **Map Remove Empty Monster Spawns** - Remover spawns vazios de monstros
- ❌ **Map Remove Empty NPC Spawns** - Remover spawns vazios de NPCs
- ❌ **Map Clean House Items** - Limpar itens de casas

---

### 8. Sistema de Propriedades e Edição

#### ✅ Implementado no Python
- ✅ Estruturas básicas de dados (Tile, Item, House, etc.)

#### ❌ Faltante no Python

##### 8.1 Janelas de Propriedades
- ⚠️ **Properties Window** - Janela completa de propriedades:
  - ✅ Edição de propriedades de tile
  - ✅ Edição de propriedades de item
  - ✅ Edição de propriedades de casa
  - ⚠️ Visualização de propriedades de spawn (read-only)
  - ⚠️ Visualização de propriedades de waypoint (read-only)
  - ⚠️ Visualização de propriedades de zona (read-only)
  - ❌ Edição completa de spawn/waypoint/zona
- ❌ **Container Properties Window** - Propriedades de containers
- ❌ **Old Properties Window** - Janela legada de propriedades

##### 8.2 Edição de Entidades
- ❌ **Edit Towns** - Editor de cidades
- ❌ **Edit Items** - Editor de itens (database)
- ❌ **Edit Monsters** - Editor de monstros (database)
- ❌ **Map Properties** - Propriedades do mapa

##### 8.3 Operações de Item
- ❌ **Rotate Item** - Rotacionar item (pendente)
- ✅ **Switch Door** - `switch_door()` e `switch_door_at()` implementados em door_brush.py/editor.py
- ❌ **Copy Item ID** - Copiar ID do item (pendente)
- ❌ **Copy Name** - Copiar nome do item (pendente)
- ❌ **Browse Tile** - Navegar tile (pendente)

---

### 9. Sistema de Paleta (Palette)

#### ✅ Implementado no Python
- ✅ **PaletteManager** (`vis_layer/ui/docks/palette.py`):
  - ✅ `PaletteDock` dataclass (dock, tabs, filter_edit, list_widget)
  - ✅ `build_primary()` - Cria paleta principal
  - ✅ `create_additional()` - Cria paletas adicionais
  - ✅ `refresh_list()` - Atualiza lista de brushes
  - ✅ `select_palette()` - Seleciona paleta por nome
  - ✅ `palette_keys()` - Lista de paletas disponíveis

##### 9.1 Tipos de Paleta (Implementados)
- ✅ **Terrain Palette** - Paleta de terrenos (ground brushes + Optional Border Tool + Door Tools)
- ✅ **Doodad Palette** - Paleta de decorações (doodad brushes from materials XML)
- ✅ **Item Palette** - Paleta de itens (carpet, table brushes)
- ✅ **Recent Palette** - Paleta de brushes recentes
- ✅ **House Palette** - Paleta de casas (virtual house brushes)
- ✅ **Creature Palette** - Paleta de monstros:
  - ✅ Monster Spawn Area Tool
  - ✅ Lista de monstros (load_monster_names from creatures.xml)
  - ✅ Virtual IDs para cada monstro
- ✅ **NPC Palette** - Paleta de NPCs:
  - ✅ NPC Spawn Area Tool
  - ✅ Lista de NPCs (load_npc_names from creatures.xml)
  - ✅ Virtual IDs para cada NPC
- ✅ **Waypoint Palette** - Paleta de waypoints:
  - ✅ Lista de waypoints do mapa
  - ✅ Exibe posição (nome @ x,y,z)
  - ✅ Virtual IDs para navegação
- ✅ **Zones Palette** - Paleta de zonas (zones do mapa com virtual IDs)
- ✅ **RAW Palette** - Paleta raw (itens por ID direto)

##### 9.2 Funcionalidades de Paleta
- ✅ **Multiple Palettes** - `create_additional()` cria paletas adicionais
- ✅ **Filter Search** - Campo de busca com filtragem em tempo real
- ✅ **Palette Refresh** - `refresh_list()` e `refresh_primary_list()`
- ⚠️ **Palette Actions** - Ações básicas implementadas:
  - ❌ Action ID enable/disable (pendente)
  - ❌ Action ID value (pendente)
- ❌ **Palette Rebuild** - Reconstrução completa (pendente)

---

### 10. Sistema de Navegação e Posicionamento

#### ✅ Implementado no Python
- ✅ Viewport básico
- ✅ Zoom básico

#### ✅ Implementado no Python

##### 10.1 Navegação
- ✅ **Goto Position** - `goto_position()` → `_goto_position_from_fields()`
- ✅ **Goto Previous Position** - `goto_previous_position()` → `_goto_previous_position()`
- ⚠️ **Position History** - Histórico básico via previous position
- ✅ **Copy Position** - `copy_position()` → `_copy_position_to_clipboard()`
- ✅ **Jump to Brush** - `jump_to_brush()` → `_jump_to_brush()`
- ✅ **Jump to Item Brush** - `jump_to_item()` → `_jump_to_item()`

##### 10.2 Mirror Drawing (Desenho Espelhado)
- ✅ **Mirror Drawing** - Implementado em logic_layer (ver CHANGELOG "mirror drawing behavior")
- ✅ **Mirror Axis** - Axis + dedupe + bounds centralizado em logic layer
- ⚠️ **Set Mirror Axis from Cursor** - Parcialmente implementado

##### 10.3 Visualização
- ❌ **Fit View to Map** - Ajustar visualização ao mapa (pendente)
- ❌ **New View** - Nova visualização (janela) (pendente)
- ✅ **Toggle Fullscreen** - `toggle_fullscreen()` implementado
- ⚠️ **Zoom In/Out/Normal** - Zoom básico implementado, controles de menu pendentes

---

### 11. Sistema de Hotkeys (Atalhos)

#### ⚠️ Parcialmente Implementado

- ⚠️ **Hotkey System** - Atalhos via Qt:
  - ✅ Atalhos padrão Qt (Ctrl+Z, Ctrl+Y, Ctrl+C, etc.)
  - ✅ Atalhos de menu (F1-F12 para ferramentas)
  - ❌ 10 hotkeys configuráveis pelo usuário (pendente)
  - ❌ Hotkeys para posições (pendente)
  - ❌ Interface de configuração (pendente)

---

### 12. Sistema de Preferências e Configurações

#### ✅ Implementado no Python
- ✅ ConfigurationManager básico
- ✅ Project definitions

#### ❌ Faltante no Python

##### 12.1 Preferences Window
- ❌ **Preferences Window** completa com:
  - ❌ Configurações gerais
  - ❌ Configurações de visualização
  - ❌ Configurações de editor
  - ❌ Configurações de cliente/assets
  - ❌ Configurações de atalhos
  - ❌ Configurações de live server

##### 12.2 Configurações Específicas
- ❌ **Cursor Colors** - Cores do cursor
- ❌ **Grid Settings** - Configurações de grade
- ❌ **Light Settings** - Configurações de iluminação
- ❌ **Transparent Floors** - Pisos transparentes
- ❌ **Transparent Items** - Itens transparentes
- ❌ **Perspective** - Salvar/carregar perspectiva de janelas

---

### 13. Sistema de Estatísticas

#### ✅ Implementado no Python
- ✅ `MapStatistics` dataclass (`logic_layer/map_statistics.py`):
  - ✅ `total_tiles` - Contagem total de tiles
  - ✅ `total_items` - Contagem total de itens
  - ✅ `unique_items` - Contagem de itens únicos
  - ✅ `total_monsters` - Contagem de monstros
  - ✅ `unique_monsters` - Monstros únicos
  - ✅ `total_npcs` - Contagem de NPCs
  - ✅ `unique_npcs` - NPCs únicos
  - ✅ `total_spawns` - Contagem de spawns
  - ✅ `total_houses` - Contagem de casas
  - ✅ `items_with_action_id` - Itens com action ID
  - ✅ `items_with_unique_id` - Itens com unique ID
  - ✅ `teleport_count` - Contagem de teleports
  - ✅ `container_count` - Contagem de containers
  - ✅ `depot_count` - Contagem de depots
  - ✅ `door_count` - Contagem de portas
  - ✅ `waypoint_count` - Contagem de waypoints
  - ✅ `tiles_per_floor` - Tiles por andar (tuple len 16)
- ✅ `compute_map_statistics()` - Função de cálculo
- ✅ `MapStatisticsDialog` (`vis_layer/ui/main_window/dialogs.py`) - Interface gráfica
- ✅ `format_map_statistics()` - Formatação textual

#### ⚠️ Parcialmente Faltante no Python

##### 13.1 Estatísticas Avançadas
- ❌ **Export para XML** - Exportar estatísticas para arquivo XML
- ❌ **Detalhamento por categoria** - Estatísticas agrupadas por tipo de item
- ❌ **Gráficos visuais** - Visualização gráfica de estatísticas

---

### 14. Sistema de Templates

#### ❌ Completamente Faltante

- ❌ **Templates System** - Sistema de templates de mapa:
  - ❌ Template para versão 7.6-7.4
  - ❌ Template para versão 8.1
  - ❌ Template para versão 8.54
  - ❌ Template clássico
  - ❌ Generate Map - Gerar mapa a partir de template

---

### 15. Sistema de Tilesets

#### ❌ Completamente Faltante

- ❌ **Tileset Window** - Janela de tilesets:
  - ❌ Criar tileset
  - ❌ Editar tileset
  - ❌ Gerenciar tilesets
  - ❌ Exportar tilesets
- ❌ **Add Tileset Window** - Adicionar tileset
- ❌ **Move to Tileset** - Mover seleção para tileset

---

### 16. Sistema de Resultados de Busca

#### ✅ Implementado no Python
- ✅ Busca básica com resultados

#### ❌ Faltante no Python

##### 16.1 Search Result Window
- ❌ **Search Result Window** completa:
  - ❌ Lista de resultados
  - ❌ Navegação entre resultados
  - ❌ Filtros de resultados
  - ❌ Export de resultados

---

### 17. Sistema de Welcome Dialog

#### ❌ Completamente Faltante

- ❌ **Welcome Dialog** - Diálogo de boas-vindas:
  - ❌ Opções de criar novo mapa
  - ❌ Opções de abrir mapa existente
  - ❌ Lista de mapas recentes
  - ❌ Configurações iniciais

---

### 18. Sistema de About Window

#### ⚠️ Parcialmente Implementado

- ⚠️ **AboutDialog** (`vis_layer/ui/_experimental/dialogs.py`) - PySide6, deprecado:
  - ✅ Informações da versão (Python, Qt, OS)
  - ✅ Créditos (tab com desenvolvedores)
  - ✅ Licença (tab com MIT/GPL)
  - ❌ Links úteis

> **Nota:** Existe implementação funcional em PySide6 (_experimental), mas precisa ser portada para PyQt6 canônico.

---

### 19. Sistema de Toolbars

#### ✅ Implementado no Python
- ✅ **QtMapEditorToolbarsMixin** (`vis_layer/ui/main_window/qt_map_editor_toolbars.py`):
  - ✅ `tb_standard` (QToolBar) - New, Open, Save, Undo, Redo, Cut, Copy, Paste, Zoom
  - ✅ `tb_brushes` (QToolBar) - Brush ID spinner, brush label, selection mode, mirror toggle
  - ✅ `tb_sizes` (QToolBar) - Size spinner, size buttons (0-11), shape buttons (square/circle), automagic checkbox
  - ✅ `tb_position` (QToolBar) - Coordenadas X, Y, Z do cursor
  - ✅ `tb_indicators` (QToolBar) - Indicadores de estado
- ✅ **Toggle Toolbars** - `toggleViewAction()` para cada toolbar no menu View → Toolbars

#### ⚠️ Parcialmente Faltante
- ⚠️ Ícones customizados para algumas ações

---

### 20. Sistema de Menus

#### ✅ Implementado no Python
- ✅ Menus básicos (File, Edit, View, etc.)

#### ❌ Faltante no Python

##### 20.1 Menus Completos
- ❌ **File Menu** completo:
  - ❌ Recent Files - Arquivos recentes
  - ❌ Reload Data - Recarregar dados
- ❌ **Edit Menu** completo com todas as operações
- ❌ **View Menu** completo com todas as opções de visualização
- ❌ **Map Menu** completo
- ❌ **Network Menu** - Menu de rede (live)
- ❌ **Window Menu** completo
- ❌ **Help Menu** - Menu de ajuda

---

### 21. Sistema de Popup Menus

#### ❌ Completamente Faltante

- ❌ **Map Popup Menu** - Menu de contexto no mapa:
  - ❌ Cut/Copy/Paste
  - ❌ Delete
  - ❌ Copy Position
  - ❌ Copy Item ID
  - ❌ Copy Name
  - ❌ Browse Tile
  - ❌ Goto Destination
  - ❌ Copy Destination
  - ❌ Rotate Item
  - ❌ Switch Door
  - ❌ Seleção de brushes
  - ❌ Properties
  - ❌ Move to Tileset
- ❌ **Container Popup Menu** - Menu de contexto em containers

---

### 22. Sistema de Indicadores

#### ✅ Implementado no Python
- ✅ IndicatorService básico

#### ❌ Faltante no Python

- ❌ **Position Indicator** - Indicador de posição
- ❌ **Brush Indicator** - Indicador de brush atual
- ❌ **Status Bar** completa com:
  - ❌ Posição atual
  - ❌ Zoom atual
  - ❌ Brush atual
  - ❌ Modo atual

---

### 23. Sistema de Actions History

#### ✅ Implementado no Python
- ✅ `ActionsHistoryDock` - Dock completo em `vis_layer/ui/docks/actions_history.py` (86 linhas)
- ✅ Lista de ações com undo stack
- ✅ Labels descritivos via `_format_action()`
- ✅ Contador de redo disponível
- ✅ `refresh()` para atualização dinâmica

#### ❌ Faltante no Python (funcionalidades avançadas)
- ❌ Filtros por tipo de ação
- ❌ Ícones por tipo (como no C++ `HistoryListBox`)
- ❌ Navegação interativa (clicar para ir ao estado)

---

### 24. Sistema de Minimap

#### ✅ Implementado no Python
- ✅ MinimapWidget básico

#### ❌ Faltante no Python

- ⚠️ **Minimap Window** completa:
  - ✅ Renderização básica do minimap
  - ✅ Navegação pelo minimap
  - ✅ Indicador de posição atual
  - ❌ Zoom do minimap
  - ✅ Atualização em tempo real (update em `_on_tiles_changed` quando dock visível)

---

### 25. Sistema de Reload Data

#### ❌ Completamente Faltante

- ❌ **Reload Data Files** - Recarregar arquivos de dados:
  - ❌ Recarregar items.xml
  - ❌ Recarregar monsters.xml
  - ❌ Recarregar npcs.xml
  - ❌ Recarregar brushes
  - ❌ Recarregar sprites

---

### 26. Sistema de Backup

#### ❌ Completamente Faltante

- ❌ **Backup System** - Sistema de backup automático:
  - ❌ Criar diretório de backup
  - ❌ Deletar backups antigos
  - ❌ Configuração de intervalo de backup
  - ❌ Configuração de número de backups

---

### 27. Sistema de Conversão de Mapas

#### ✅ Implementado no Python
- ✅ **Map Format Conversion** (`logic_layer/map_format_conversion.py`):
  - ✅ Conversão OTBM v2 (ServerID) ↔ v5/v6 (ClientID)
  - ✅ `analyze_map_format_conversion()` - Validador de conversão
  - ✅ `apply_map_format_version()` - Aplicador de versão
  - ✅ UI Dialog ("Convert Map Format") com validação de ID mappings
  - ✅ Integração com Item Database e IdMapper para tradução de IDs

---

### 28. Sistema de Complex Items

#### ❌ Completamente Faltante

- ❌ **ComplexItem** - Itens complexos:
  - ❌ Containers
  - ❌ Teleports
  - ❌ Doors
  - ❌ Beds
  - ❌ E outros tipos especiais

---

### 29. Sistema de Client Assets

#### ✅ Implementado no Python
- ✅ SpriteAppearances básico
- ✅ Detecção de diretório de assets

#### ❌ Faltante no Python

##### 29.1 Client Assets Completo
- ❌ **ClientAssets** completo:
  - ❌ Carregamento de DAT/SPR
  - ❌ Carregamento de XML de items
  - ❌ Carregamento de XML de monsters
  - ❌ Carregamento de XML de NPCs
  - ❌ Validação de versão
  - ❌ Descoberta automática de diretório

---

### 30. Sistema de Database

#### ✅ Implementado no Python
- ✅ ItemsXML básico
- ✅ ItemsOTB básico
- ✅ IdMapper básico

#### ❌ Faltante no Python

##### 30.1 Database Completo
- ❌ **Items Database** completo:
  - ❌ Carregamento completo de items.xml
  - ❌ Atributos de itens
  - ❌ Tipos de itens
  - ❌ Flags de itens
- ❌ **Monsters Database** completo
- ❌ **NPCs Database** completo

---

## 📊 Resumo Estatístico

> **Nota:** Tabela atualizada em 2025-01-23 após auditoria completa de código.

### Funcionalidades por Categoria

| Categoria | Implementado | Parcial | Faltante | % Completo |
|-----------|--------------|---------|----------|------------|
| Brushes | 10 | 5 | 3 | ~80% |
| Editor/Sessão | 12 | 2 | 3 | ~80% |
| Renderização (DrawingOptions) | 24 | 0 | 3 | ~90% |
| Live Server/Client | 3 | 2 | 5 | ~40% |
| Import/Export (OTBM/OTMM) | 6 | 0 | 1 | ~90% |
| Busca/Substituição | 6 | 1 | 3 | ~70% |
| Limpeza/Manutenção | 0 | 0 | 7 | 0% |
| Propriedades | 4 | 3 | 3 | ~60% |
| Paleta | 10 | 0 | 2 | ~85% |
| Navegação | 6 | 0 | 2 | ~75% |
| Hotkeys | 8 | 2 | 3 | ~70% |
| Preferências | 2 | 0 | 10 | ~15% |
| Estatísticas | 17 | 0 | 3 | ~85% |
| Templates | 0 | 0 | 5 | 0% |
| Tilesets | 0 | 0 | 5 | 0% |
| Menus | 8 | 3 | 10 | ~55% |
| Popup Menus | 1 | 1 | 8 | ~15% |
| Toolbars | 5 | 1 | 0 | ~95% |
| About Window | 0 | 1 | 0 | ~50% |
| **TOTAL** | **~122** | **~21** | **~76** | **~65%** |

---

## 🎯 Prioridades de Implementação

### Alta Prioridade (Core Functionality)
1. **Sistema de Brushes Completo** - Essencial para edição
2. **Sistema de Renderização OpenGL** - Performance e visualização
3. **Sistema de Ações Completo** - Undo/Redo robusto
4. **Sistema de Busca/Substituição** - Funcionalidade básica
5. **Sistema de Propriedades** - Edição de entidades

### Média Prioridade (Important Features)
6. **Sistema de Importação/Exportação** - Interoperabilidade
7. **Sistema de Paleta Completo** - UX melhorada
8. **Sistema de Preferências** - Customização
9. **Sistema de Navegação** - Produtividade
10. **Sistema de Limpeza** - Manutenção

### Baixa Prioridade (Nice to Have)
11. **Live Server/Client** - Colaboração
12. **Templates** - Conveniência
13. **Tilesets** - Organização
14. **Welcome Dialog** - UX
15. **About Window** - Informação

---

## 🔍 Análise de Qualidade de Código: Mypy e Ruff

### Configuração Atual

#### ✅ Configuração do Ruff (`pyproject.toml`)
```toml
[tool.ruff]
target-version = "py312"
line-length = 120
extend-exclude = [
  "py_rme_canary/vis_layer/**",
  "py_rme_canary/tools/**",
]

[tool.ruff.lint]
select = [
  "F",  # pyflakes (unused imports, undefined names, etc.)
]
```

**Status:** ✅ Configuração básica adequada, mas limitada

**Problemas Identificados:**
- ❌ Apenas regras `F` (pyflakes) estão habilitadas
- ❌ Muitas regras úteis não estão habilitadas (E, W, I, N, etc.)
- ❌ `vis_layer/` e `tools/` estão completamente excluídos
- ❌ Não há configuração de formatação (ruff format)

#### ✅ Configuração do Mypy (`pyproject.toml`)
```toml
[tool.mypy]
python_version = "3.12"
warn_unused_ignores = true
warn_redundant_casts = true
warn_unreachable = true
no_implicit_optional = true
check_untyped_defs = false
ignore_missing_imports = true
exclude = [
  "py_rme_canary/vis_layer/",
  "py_rme_canary/tools/",
]
disallow_untyped_defs = false
```

**Status:** ⚠️ Configuração muito permissiva

**Problemas Identificados:**
- ❌ `disallow_untyped_defs = false` - Permite funções sem type hints
- ❌ `check_untyped_defs = false` - Não verifica código não tipado
- ❌ `ignore_missing_imports = true` - Ignora imports faltantes (pode esconder erros)
- ❌ `vis_layer/` e `tools/` completamente excluídos
- ⚠️ Configuração muito relaxada para um projeto em desenvolvimento

### Análise do Uso de Type Hints

#### ✅ Pontos Positivos

1. **Uso Consistente de `from __future__ import annotations`**
   - ✅ Presente na maioria dos arquivos principais
   - ✅ Permite usar tipos forward references sem aspas
   - ✅ Melhora performance do parsing

2. **Type Hints em Estruturas de Dados**
   - ✅ `@dataclass` com type hints completos
   - ✅ `TypedDict` usado corretamente (`LoadReport`)
   - ✅ Type hints em métodos públicos

3. **Uso de Tipos Modernos**
   - ✅ `list[T]` e `dict[K, V]` (Python 3.12)
   - ✅ `Optional[T]` e `| None` (ambos usados)
   - ✅ `Protocol` para interfaces (`TileChangeRecorder`)

4. **Type Aliases**
   - ✅ `TileKey = Tuple[int, int, int]` bem definido
   - ✅ `TilesChangedCallback = Callable[[Set[TileKey]], None]`

#### ❌ Problemas Encontrados

1. **Funções Sem Type Hints**
   - ❌ Algumas funções internas sem type hints
   - ❌ Métodos privados (`_method`) muitas vezes sem hints
   - ❌ Funções de utilidade sem hints

2. **Type Hints Incompletos**
   - ⚠️ Alguns parâmetros `*args` e `**kwargs` sem hints
   - ⚠️ Retornos `Any` em alguns lugares
   - ⚠️ Uso de `Dict` e `List` em vez de `dict` e `list` (inconsistente)

3. **Exclusões Excessivas**
   - ❌ `vis_layer/` completamente excluído do mypy
   - ❌ `tools/` completamente excluído
   - ⚠️ Isso pode esconder problemas de tipo em código importante

4. **Imports de Tipo**
   - ⚠️ Uso misto de `from typing import` e tipos built-in
   - ⚠️ Alguns arquivos ainda usam `typing.List` em vez de `list`

### Análise do Uso do Ruff

#### ✅ Pontos Positivos

1. **Uso de `# noqa`**
   - ✅ Uso apropriado em imports de compatibilidade:
     ```python
     from py_rme_canary.logic_layer.borders import *  # noqa: F403
     ```

2. **Estrutura de Código**
   - ✅ Código geralmente bem formatado
   - ✅ Imports organizados
   - ✅ Sem problemas óbvios de pyflakes

#### ❌ Problemas e Oportunidades

1. **Regras Não Habilitadas**
   - ❌ **E (pycodestyle)** - Estilo de código PEP 8
   - ❌ **W (pycodestyle warnings)** - Avisos de estilo
   - ❌ **I (isort)** - Organização de imports
   - ❌ **N (pep8-naming)** - Convenções de nomenclatura
   - ❌ **UP (pyupgrade)** - Modernização de código
   - ❌ **B (flake8-bugbear)** - Detecção de bugs comuns
   - ❌ **C4 (flake8-comprehensions)** - Comprehensions otimizadas
   - ❌ **SIM (flake8-simplify)** - Simplificações

2. **Formatação**
   - ❌ Ruff format não configurado
   - ⚠️ Dependência de formatação manual ou outro tool

3. **Exclusões**
   - ⚠️ `vis_layer/` e `tools/` excluídos podem ter problemas não detectados

### Recomendações de Melhoria

#### 🔴 Alta Prioridade

1. **Habilitar Mais Regras do Ruff**
   ```toml
   [tool.ruff.lint]
   select = [
     "F",    # pyflakes
     "E",    # pycodestyle errors
     "W",    # pycodestyle warnings
     "I",    # isort
     "N",    # pep8-naming
     "UP",   # pyupgrade
     "B",    # flake8-bugbear
     "C4",   # flake8-comprehensions
     "SIM",  # flake8-simplify
   ]
   ```

2. **Adicionar Ruff Format**
   ```toml
   [tool.ruff.format]
   quote-style = "double"
   indent-style = "space"
   line-ending = "auto"
   ```

3. **Tornar Mypy Mais Restritivo Gradualmente**
   ```toml
   [tool.mypy]
   # Começar com:
   disallow_untyped_defs = true  # Para novos arquivos
   check_untyped_defs = true     # Verificar código existente
   ignore_missing_imports = false  # Apenas para bibliotecas específicas
   ```

4. **Adicionar Type Hints Faltantes**
   - Adicionar type hints em todas as funções públicas
   - Adicionar type hints em métodos privados importantes
   - Usar `typing.overload` onde apropriado

#### 🟡 Média Prioridade

5. **Configurar Mypy por Módulo**
   ```toml
   [tool.mypy-py_rme_canary.vis_layer]
   # Configuração específica para vis_layer
   ignore_errors = false
   disallow_untyped_defs = false  # Temporariamente
   ```

6. **Adicionar Type Stubs**
   - Criar stubs para bibliotecas sem type hints (se necessário)
   - Usar `types-*` packages quando disponíveis

7. **Habilitar Verificações Adicionais**
   ```toml
   [tool.mypy]
   strict_optional = true
   strict_equality = true
   warn_return_any = true
   warn_unused_configs = true
   ```

#### 🟢 Baixa Prioridade

8. **CI/CD Integration**
   - Adicionar verificação de mypy e ruff no CI/CD
   - Falhar build se houver erros de tipo
   - Falhar build se houver violações de estilo

9. **Pre-commit Hooks**
   - Configurar pre-commit hooks com ruff e mypy
   - Formatação automática antes do commit

10. **Documentação de Type Hints**
    - Documentar padrões de type hints do projeto
    - Criar guia de estilo para type hints

### Exemplos de Problemas Encontrados

#### Exemplo 1: Função Sem Type Hints
```python
# ❌ Problema
def process_tiles(tiles):
    # Sem type hints
    pass

# ✅ Solução
def process_tiles(tiles: list[Tile]) -> None:
    pass
```

#### Exemplo 2: Uso Inconsistente de Tipos
```python
# ❌ Problema - Mistura de typing.List e list
from typing import List, Dict
def func(items: List[int]) -> Dict[str, int]:
    pass

# ✅ Solução - Usar tipos built-in (Python 3.9+)
def func(items: list[int]) -> dict[str, int]:
    pass
```

#### Exemplo 3: Exclusão Excessiva
```python
# ❌ Problema - vis_layer completamente excluído
# Pode esconder problemas importantes

# ✅ Solução - Configuração específica
[tool.mypy-py_rme_canary.vis_layer]
ignore_errors = false
disallow_untyped_defs = false  # Gradualmente aumentar
```

### Métricas de Qualidade

| Métrica | Atual | Recomendado | Status |
|---------|-------|-------------|--------|
| **Ruff Rules Enabled** | 1 (F) | 8+ | ❌ |
| **Mypy Strictness** | Baixa | Média-Alta | ⚠️ |
| **Type Coverage** | ~70% | ~95% | ⚠️ |
| **Files with Type Hints** | ~80% | ~100% | ⚠️ |
| **Excluded Modules** | 2 | 0-1 | ❌ |

### Checklist de Implementação

- [ ] Habilitar regras adicionais do Ruff
- [ ] Configurar Ruff format
- [ ] Aumentar strictness do Mypy gradualmente
- [ ] Adicionar type hints faltantes
- [ ] Reduzir exclusões de módulos
- [ ] Configurar CI/CD com verificações
- [ ] Adicionar pre-commit hooks
- [ ] Documentar padrões de type hints

---

## 📝 Notas Finais

### Arquitetura
A arquitetura Python (`py_rme_canary/`) está bem estruturada com separação clara entre:
- `core/` - Dados e I/O
- `logic_layer/` - Lógica de edição
- `vis_layer/` - Interface visual

Isso facilita a implementação incremental das funcionalidades faltantes.

### Compatibilidade
O código Python já implementa as estruturas de dados básicas compatíveis com o formato OTBM, o que facilita a implementação das funcionalidades restantes.

### Qualidade de Código
O projeto tem uma base sólida de type hints, mas há oportunidades de melhoria:
- Configuração de ferramentas de qualidade (mypy/ruff) pode ser mais rigorosa
- Cobertura de type hints pode ser aumentada
- Mais regras de linting podem ser habilitadas

### Recomendações
1. Implementar funcionalidades em ordem de prioridade
2. Manter compatibilidade com formato OTBM
3. Seguir a arquitetura existente (core/logic_layer/vis_layer)
4. Adicionar testes para cada funcionalidade implementada
5. Documentar cada nova funcionalidade
6. **Melhorar configuração de mypy e ruff gradualmente**
7. **Aumentar cobertura de type hints em código novo**

---

**Última Atualização:** 2025-01-XX
**Próxima Revisão:** Após implementação de funcionalidades prioritárias
