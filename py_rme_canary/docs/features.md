# Features

## RME Py_Extended Edition v1.5
*   [x] **Monster & NPC Names:** Displayed on the map.
*   [x] **Duplicate Unique ID Warning:** Alerts for duplicate UIDs.
*   [x] **Client Profiles:** Support for multiple data profiles per client version.
*   [x] **Palette Icons:** Optional larger icons in the palette.
*   [x] **Dark Mode:** Configurable in Preferences.
*   [x] **Replace Items:** Available via right-click menu.
    *   Replace on visible screen or entire map.
*   [x] **Navigation:** Position highlight for "Go to Position".
*   [x] **Export:** Support for `minimap.otmm` export.
*   **Compatibility:** Client versions 7.4 to 15+.

## RME Py_Extended Edition v2.0
*   **Cross-Version Map Copy/Paste:** Copy/paste maps between different client versions.
*   **Sprite Hash Matching:** Automatic sprite hash matching using FNV-1a 64-bit.
*   **Auto-Correction:** Automatically finds and uses correct ServerID if sprites exist but on the wrong ID.
*   **Instance Transfer:** Creature & Spawn transfer between instances.
*   **Multiple Instances:** Run several editors with different SPR/DAT/OTB files.
*   **Compatibility:** Client versions 7.4 to 15+.

### Includes all features from v1.5:
*   Monster & NPC Names, Duplicate UID Warning
*   Client Profiles, Dark mode, Replace Items
*   Export to minimap.otmm

## RME Py_Extended Edition v2.5
*   [x] **Advanced Selection:** Lasso/Freehand Selection - Draw polygon shapes to select tiles.
*   [x] **Lua Monster Import:** Import TFS 1.x revscript monsters.
*   [x] **Monster Folder Import:** Recursive folder scanning for monsters.
*   [x] **Quick Replace:** Right-click items directly on the map to replace them.
*   [x] **Advanced Brushes:** Support for Table, Carpet, and Doodad brushes (from materials XML).
    *   *Note: Doodad "Erase Like" mode pending implementation.*

### Includes all features from v2.0:
*   Cross-Instance Clipboard with Sprite Hash Matching
*   Copy/paste maps between different client versions
*   Automatic sprite hash matching (FNV-1a 64-bit)
*   Creature & Spawn Transfer between instances
*   Multiple Instances with different SPR/DAT/OTB
*   Compatible with client 7.4-15+

### Includes all features from v1.5:
*   Monster & NPC Names, Duplicate UID Warning
*   Client Profiles, Dark mode, Replace Items
*   Export to minimap.otmm

### NEW in Version 3.0:
Version 3.7 - New Features
🎯 Lasso/Freehand Selection
Draw custom polygon shapes to select tiles instead of rectangular selection. Perfect for caves, coastlines, and organic shapes.

1. Click Lasso button in Indicators toolbar
2. Make sure you're in Selection Mode
3. Hold Shift + drag to draw shape
4. Release mouse → polygon closes automatically
5. All tiles inside are selected!
Shift + Drag Replace selection  |  Ctrl + Shift + Drag Add to selection

Floor Selection: Respects current floor settings (Current Floor / All Floors / Visible Floors)

Technical: Uses ray casting algorithm (point-in-polygon) for accurate selection

🐉 Lua Monster Import (Revscript)
Import monsters from TFS 1.x Lua/revscript format. Supports individual files and recursive folder import.

Individual files: File → Import → Import Monsters/NPC...
Entire folder: File → Import → Import Monster Folder...
Extracts: name lookType lookHead/Body/Legs/Feet lookMount lookAddons

Supported Format:
local mType = Game.createMonsterType("Monster Name") local monster = {} monster.outfit = { lookType = 130, lookHead = 0, lookBody = 0, lookLegs = 0, lookFeet = 0, lookAddons = 0, lookMount = 0 } mType:register(monster)
Notes: Files without valid definitions are skipped. Existing monsters are updated (not duplicated). NPCs use Game.createNpcType()

⚡ Quick Replace from Map
Skip the RAW palette! Right-click any item directly on the map to set it as Find or Replace target.

1. Right-click item on map → "Set as Find Item"
2. Right-click another item → "Set as Replace Item"
3. Press Ctrl+Shift+F → Replace Items dialog
4. Click Replace → Done!
Before: Select RAW palette → Search for item → Right-click → Set as Find/Replace

Now: Right-click item on map → Set as Find/Replace. Skip the palette entirely!

Version 3.6 - Features
Feature	Description
Monster & NPC Names	Creature names are displayed above them on the map for easier identification
Dark Mode	Full dark mode support for the editor UI - easier on the eyes during long mapping sessions
Large Palette Icons	Option for larger icons in palettes - better visibility on high-resolution screens
Replace Items Dialog	"Only replace on visible map and current floor" checkbox to limit replacements
Palette Right-Click Menu	Right-click RAW items to quickly set them as "Find" or "Replace With" targets
Multiple Instances	Run multiple editor instances simultaneously with different SPR/DAT/OTB assets
Client Profiles	Create multiple data profiles per client version (e.g., "10.98", "10.98-alt") pointing to different asset folders
Client 11 Support	Added support for loading Client 11 SPR/DAT format
Cross-Instance Clipboard	Copy/paste between different client versions using sprite hash matching
Creature & Spawn Transfer	Creatures and spawns are included when copying between instances
OTMM Export for OTClient	Export map as OTMM format - OTClient gets full minimap support immediately
Duplicate Unique ID Warning	Automatic detection and warning when duplicate Unique IDs exist on the map
Position Highlight Box	Visual highlight when using Go to Position - precise coordinate placement for Action IDs, teleports, and map pasting
Key Advantage: Cross-Version Workflow
The combination of Multiple Instances, Client Profiles, and Cross-Instance Clipboard with Sprite Hash Matching creates a powerful workflow for map developers working with custom clients or migrating content between versions.

You can have one RME open with Client 13.x content and another with your custom 7.4 client, and seamlessly copy areas between them - the sprite matching handles the ID translation automatically.

*   ClientID Format Support - Open OTBM 5/6 maps
*   Auto ID Translation - ClientID ↔ ServerID via items.otb
*   Map Format Conversion - Convert between formats
*   Client 14 Support - Full OTBM 5/6 compatibility
*   Appearances Menu - Optional appearances.dat loading
    - 🗺️ ClientID Format Support (OTBM 5/6)
Open and edit maps created with ClientID-based map editors. This format uses ClientIDs directly instead of ServerIDs, commonly used by modern OT servers.

1. Load any client version (e.g., Client 14) with its items.otb
2. Open maps in OTBM 5/6 format → Auto-detected
3. IDs translated automatically via items.otb mappings
4. Edit normally → Save in original or converted format
Key Features:

Auto ID Translation - ClientID ↔ ServerID mapping built from items.otb
No appearances.dat Required - Works with just items.otb
Format Conversion - Convert maps between ServerID and ClientID formats
Show ClientIDs - Toggle View menu option to display ClientIDs in editor
[ ] Map Format Conversion
Convert entire maps between traditional ServerID format (OTBM 1-4) and ClientID format (OTBM 5/6).

1. Open map in either format
2. Menu: Map → Convert Map Format...
3. Confirm conversion direction
4. All item IDs translated → Save with new format
ServerID → ClientID Uses serverToClient mapping  |  ClientID → ServerID Uses clientToServer mapping

Note: Items without valid mappings are reported. Always backup before converting!

[ ] Appearances Support (Optional)
Optionally load appearances.dat for enhanced ClientID format support and sprite information.

Load: File → Appearances → Load Appearances...
Unload: File → Appearances → Unload Appearances
Auto-load: Enable in Preferences → Editor tab
Preferences option: "Auto-load appearances.dat (ClientID format)" - automatically loads if found in client folder.
[ ] Client 14 Support
Full support for Client 14 and OTBM versions 5/6. Compatible with maps from various modern OT server projects.

Supported OTBM versions: 2, 3, 4, 5, 6
Data directory: 1100
Data format: Format 11 (same as Client 11)

[ ] Technical: How ServerID vs ClientID Works
Open Tibia uses two different ID systems for items. Understanding these helps when working with maps from different sources.

[ ] ServerID (Traditional)
Defined in items.otb
Unique ID per item on server
Maps store ServerIDs
Server translates to ClientID
Used by: TFS, OTServ, OTBM 1-4


[ ] ClientID (Modern)
Defined in Tibia.dat / appearances.dat
ID used by client for sprites
Maps store ClientIDs directly
ClientID = ServerID (unified)
Used by: OTBM 5/6 maps


Traditional System Example:
// items.otb defines the mapping: ServerID 2160 (Crystal Coin) → ClientID 3043 // Map stores ServerID, server translates for client: Map: item 2160 → Server sends 3043 → Client shows sprite
Modern System Example:
// ClientID = ServerID (unified, no translation): Map: item 3043 → Server sends 3043 → Client shows sprite
How RME Handles Both
Loading OTBM 5/6: Translates ClientID → ServerID using items.otb
Editing: Always works with ServerIDs internally
Saving OTBM 5/6: Translates ServerID → ClientID
No appearances.dat needed: Mappings come from items.otb
The ID Mapper:
// Built automatically from items.otb: serverToClient[2160] = 3043 // For saving to OTBM 5/6 clientToServer[3043] = 2160 // For loading OTBM 5/6
OTBM 1-4 ServerID format  |  OTBM 5-6 ClientID format

🏗️ System Architecture
Overview of how the ClientID format support is implemented in RME.

Components:
┌─────────────────────────────────────────────────────────────────┐ │ RME Architecture │ ├─────────────────────────────────────────────────────────────────┤ │ │ │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │ │ │ items.otb │─────▶│ ItemDatabase │─────▶│ ItemIdMapper │ │ │ │ (required) │ │ (g_items) │ │ │ │ │ └──────────────┘ └──────────────┘ └──────┬───────┘ │ │ │ │ │ ┌──────────────┐ ┌──────────────┐ │ │ │ │appearances.dat│─────▶│ Appearances │ │ │ │ │ (optional) │ │ Database │ │ │ │ └──────────────┘ └──────────────┘ │ │ │ ▼ │ │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │ │ │ Map File │◀────▶│ IOMapOTBM │◀────▶│ Editor │ │ │ │ (OTBM 1-6) │ │ (load/save) │ │ (internal) │ │ │ └──────────────┘ └──────────────┘ └──────────────┘ │ │ │ └─────────────────────────────────────────────────────────────────┘

[ ] Key Classes:
Class	File	Purpose
ItemIdMapper	id_mapper.cpp/h	Builds and stores ServerID ↔ ClientID mappings from items.otb
MapVersion	client_version.h	Extended with usesClientIdAsServerId flag and isCanaryFormat()
IOMapOTBM	iomap_otbm.cpp	Detects OTBM version, translates IDs on load/save
AppearancesDatabase	appearances_database.cpp/h	Optional protobuf loader for appearances.dat (extra sprite info)
Data Flow - Loading OTBM 5/6 Map:
1. IOMapOTBM::loadMap() reads OTBM header, detects version 5/6
2. Sets mapVersion.usesClientIdAsServerId = true
3. For each item: reads ClientID from file
4. Calls ItemIdMapper::clientToServer(clientId) to get ServerID
5. Creates item with ServerID → Editor works with ServerIDs internally
Data Flow - Saving to OTBM 5/6:
1. IOMapOTBM::saveMap() checks mapVersion.isCanaryFormat()
2. For each item: gets ServerID from internal representation
3. Calls ItemIdMapper::serverToClient(serverId) to get ClientID
4. Writes ClientID to file
ItemIdMapper - Build Process:
void ItemIdMapper::buildMappingsFromOtb(const ItemDatabase& otbDb) { // Iterate all items in items.otb for (serverId = otbDb.getMinID(); serverId <= otbDb.getMaxID(); ++serverId) { ItemType& item = otbDb.getItemType(serverId); clientId = item.clientID; // Already stored in OTB! // Build bidirectional mappings m_serverToClient[serverId] = clientId; m_clientToServer[clientId] = serverId; } }
Why No Protobuf Required?
items.otb already contains ClientIDs - Each OTB entry has both ServerID and ClientID
appearances.dat is optional - Only needed for extra sprite metadata
Protobuf library included - For future use or if user wants to load appearances.dat
Mappings built at startup - When client version loads, mappings are ready
OTBM Version Detection:
// In client_version.h: enum MapVersionID { MAP_OTBM_1 = 0, // 7.4 - Traditional MAP_OTBM_2 = 1, // 8.0 - Traditional MAP_OTBM_3 = 2, // 8.4+ - Traditional MAP_OTBM_4 = 3, // 8.7+ - Traditional MAP_OTBM_5 = 4, // ClientID format MAP_OTBM_6 = 5, // ClientID format extended }; // MapVersion struct: bool usesClientIdAsServerId; // Flag for ClientID maps bool isCanaryFormat() { return usesClientIdAsServerId || otbm >= MAP_OTBM_5; }


[ ] Screenshots
Enabling Cross-Version Paste
Navigate to Edit → Preferences → Editing and enable "Sprite Match on Paste":

[ ] Sprite Match on Paste setting location
Client Profile Management
Create and manage multiple data profiles for different client versions:

[ ] Client profile management
Position Highlight Box
When using Go to Position, a highlight box shows the exact coordinate location. Useful for:

[ ]Precise placement when copy/pasting map areas
Setting Action IDs and Unique IDs at exact positions
Configuring teleport destination coordinates
Position highlight box
Duplicate Unique ID Warning
The editor automatically detects and warns when you try to use a Unique ID that already exists on the map:

[ ] Duplicate Unique ID warning
Export Minimap (OTMM)
Export your map as OTMM format for OTClient minimap support, or as PNG/BMP image:

Export Minimap dialog

## RME Py_Extended Edition v4.0 Preview In-game

## 📋 Fase 1: Preparação e Estrutura Base

### 1.1 Arquivos do Cliente Tibia

- [ ] Obter arquivo .spr do cliente Tibia (contém todos os sprites)
- [ ] Obter arquivo .dat do cliente Tibia (contém metadados dos items)
- [ ] Criar pasta `client_files/` no projeto para armazenar esses arquivos
- [ ] Documentar a versão do cliente sendo usada (ex: 12.85, 13.00, etc)

### 1.2 Pesquisa sobre Formatos

- [ ] Estudar estrutura do arquivo .dat (flags, dimensões, sprite IDs)
- [ ] Estudar estrutura do arquivo .spr (header, ponteiros, compressão de pixels)
- [ ] Pesquisar documentação existente sobre formato Tibia (OTClient wiki, fóruns)
- [ ] Entender como sprites são indexados e organizados
- [ ] Entender sistema de animações (pattern_z, frames)

### 1.3 Estrutura de Diretórios

- [ ] Criar pasta `logic_layer/sprite_system/`
- [ ] Criar pasta `vis_layer/preview/`
- [ ] Criar pasta `tests/preview_tests/`
- [ ] Organizar onde ficará cache de sprites carregados

---

## 🔧 Fase 2: Carregador de Sprites (.spr e .dat)

### 2.1 Leitura do Arquivo .dat

- [ ] Implementar leitura do header (signature, contadores)
- [ ] Implementar leitura de flags de items (ground, container, stackable, etc)
- [ ] Implementar leitura de dimensões (width, height, layers)
- [ ] Implementar leitura de padrões (pattern_x, pattern_y, pattern_z)
- [ ] Implementar leitura de sprite IDs
- [ ] Criar dicionário de metadados: {item_id: metadata}
- [ ] Testar com items conhecidos (ground, walls, doors)

### 2.2 Leitura do Arquivo .spr

- [ ] Implementar leitura do header (signature, sprite count)
- [ ] Implementar leitura da tabela de ponteiros (onde cada sprite está)
- [ ] Implementar decodificação de pixels comprimidos
- [ ] Converter pixels para formato pygame/PIL (RGBA)
- [ ] Lidar com transparência corretamente
- [ ] Testar carregamento de sprite individual

### 2.3 Sistema de Cache

- [ ] Implementar cache em memória para sprites carregados
- [ ] Implementar limite de cache (ex: 1000 sprites)
- [ ] Implementar política LRU (Least Recently Used) para limpar cache
- [ ] Adicionar contador de uso para cada sprite
- [ ] Testar performance com cache vs sem cache

### 2.4 Validação

- [ ] Carregar 10 items diferentes e verificar sprites
- [ ] Comparar sprites carregados com cliente original
- [ ] Verificar se transparência está correta
- [ ] Verificar items multi-tile (2x2, 3x3)
- [ ] Verificar items animados

---

## 🎨 Fase 3: Renderizador In-Game

### 3.1 Ordem de Renderização

- [ ] Entender ordem correta de layers no Tibia (ground → items → creatures)
- [ ] Implementar renderização de ground tiles
- [ ] Implementar renderização de items "bottom" (no chão)
- [ ] Implementar renderização de items "top" (em cima)
- [ ] Implementar elevação de items (items que ficam mais altos)
- [ ] Testar sobreposição correta de layers

### 3.2 Perspectiva Isométrica

- [ ] Definir tamanho de tile (32x32 pixels)
- [ ] Calcular offset de perspectiva (items ficam levemente deslocados)
- [ ] Implementar conversão de coordenadas mundo → tela
- [ ] Testar renderização de área 5x5 tiles
- [ ] Verificar se perspectiva está correta visualmente

### 3.3 Items Multi-Sprite

- [ ] Implementar renderização de items 2x2 (ex: camas)
- [ ] Implementar renderização de items 3x3 ou maiores
- [ ] Calcular offsets corretos para cada parte do item
- [ ] Verificar que todas as partes aparecem na posição correta
- [ ] Testar com items conhecidos (trees, buildings)

### 3.4 Animações

- [ ] Criar sistema de contagem de frames
- [ ] Implementar atualização baseada em tempo (delta_time)
- [ ] Calcular qual frame mostrar baseado no tempo
- [ ] Aplicar frame correto ao renderizar item animado
- [ ] Testar com water, fire, torch
- [ ] Ajustar velocidade de animação (200ms por frame é padrão)

### 3.5 Items Stackable

- [ ] Detectar quando item é stackable (metadata)
- [ ] Renderizar número de items no canto do tile
- [ ] Adicionar sombra no texto para legibilidade
- [ ] Posicionar número corretamente (canto inferior direito)
- [ ] Testar com diferentes quantidades (1, 50, 100)

---

## 🪟 Fase 4: Janela de Preview

### 4.1 Criação da Janela

- [ ] Criar janela pygame separada
- [ ] Definir tamanho inicial (640x480 ou maior)
- [ ] Adicionar título "In-Game Preview - RME"
- [ ] Permitir redimensionamento da janela
- [ ] Implementar fechamento correto da janela

### 4.2 Loop de Renderização

- [ ] Criar loop principal da janela (thread separada ou processo)
- [ ] Implementar controle de FPS (60 FPS recomendado)
- [ ] Processar eventos de pygame (resize, close, keyboard)
- [ ] Limpar tela a cada frame (fundo preto)
- [ ] Atualizar display após renderizar

### 4.3 Sincronização com Editor

- [ ] Conectar câmera do preview com câmera do editor
- [ ] Atualizar preview quando câmera do editor move
- [ ] Atualizar preview quando mapa é editado
- [ ] Implementar modo de sincronia on/off
- [ ] Permitir navegação independente no preview (opcional)

### 4.4 Viewport

- [ ] Calcular quais tiles estão visíveis na tela
- [ ] Renderizar apenas tiles visíveis (otimização)
- [ ] Implementar scroll/pan (se navegação independente)
- [ ] Calcular limites do viewport baseado em zoom
- [ ] Testar com diferentes tamanhos de janela

---

## ⚙️ Fase 5: Recursos Avançados

### 5.1 Grid Opcional

- [ ] Implementar toggle de grid (tecla G)
- [ ] Desenhar linhas de grid sobre preview
- [ ] Usar cor sutil para não poluir (cinza escuro, transparente)
- [ ] Alinhar grid com tiles do mapa
- [ ] Testar visibilidade em diferentes backgrounds

### 5.2 Informações na Tela

- [ ] Mostrar FPS atual no canto
- [ ] Mostrar posição da câmera (x, y, z)
- [ ] Mostrar modo de sincronia (on/off)
- [ ] Adicionar fonte pequena mas legível
- [ ] Posicionar texto sem atrapalhar visualização

### 5.3 Sistema de Lighting (Opcional - Avançado)

- [ ] Pesquisar como Tibia calcula iluminação
- [ ] Identificar items que emitem luz (torch, lamp)
- [ ] Calcular intensidade de luz por tile
- [ ] Aplicar overlay escuro em áreas sem luz
- [ ] Implementar luz ambiente (dia/noite)
- [ ] Testar performance do sistema de luz

### 5.4 Criaturas (Opcional - Avançado)

- [ ] Entender sistema de outfits do Tibia
- [ ] Carregar sprites de criaturas do .dat/.spr
- [ ] Renderizar creatures em tiles
- [ ] Implementar direções (N, S, E, W)
- [ ] Adicionar animação de walking (se aplicável)

---

## 🔗 Fase 6: Integração com Editor

### 6.1 Ações e Atalhos

- [ ] Criar ação toggle_preview no build_actions.py
- [ ] Definir atalho F5 para abrir/fechar preview
- [ ] Implementar feedback visual (status bar)
- [ ] Verificar que atalho não conflita com outros
- [ ] Testar abertura e fechamento múltiplas vezes

### 6.2 Menu

- [ ] Adicionar item "In-Game Preview" no menu View
- [ ] Adicionar separador antes do item
- [ ] Mostrar atalho (F5) ao lado do item
- [ ] Adicionar checkbox mostrando se está aberto
- [ ] Testar navegação do menu

### 6.3 Threading/Processing

- [ ] Decidir: thread separada ou processo separado?
- [ ] Implementar thread daemon para preview
- [ ] Garantir que preview fecha ao fechar editor
- [ ] Evitar travamentos entre janelas
- [ ] Testar estabilidade com janelas múltiplas

### 6.4 Comunicação entre Janelas

- [ ] Estabelecer comunicação editor → preview
- [ ] Enviar atualizações quando mapa muda
- [ ] Enviar posição de câmera quando move
- [ ] Implementar fila de mensagens (se necessário)
- [ ] Evitar overhead de comunicação constante

---

## 🧪 Fase 7: Testes e Validação

### 7.1 Testes Unitários

- [ ] Testar carregamento de .dat
- [ ] Testar carregamento de .spr
- [ ] Testar cálculo de posições espelhadas
- [ ] Testar cache de sprites
- [ ] Testar conversão mundo → tela

### 7.2 Testes de Integração

- [ ] Abrir preview e verificar renderização
- [ ] Mover câmera e verificar sincronia
- [ ] Adicionar item no editor e ver atualização no preview
- [ ] Remover item e verificar remoção no preview
- [ ] Testar com diferentes floors (andares)

### 7.3 Testes de Performance

- [ ] Medir FPS com viewport pequeno (10x10 tiles)
- [ ] Medir FPS com viewport grande (30x30 tiles)
- [ ] Verificar uso de memória com cache cheio
- [ ] Testar com muitos items animados
- [ ] Identificar gargalos de performance

### 7.4 Testes Visuais

- [ ] Comparar preview com cliente real lado a lado
- [ ] Verificar ground tiles (grass, stone, etc)
- [ ] Verificar walls e bordas
- [ ] Verificar items de decoração
- [ ] Verificar animações (velocidade correta?)
- [ ] Verificar transparência e sobreposição

### 7.5 Testes de Edge Cases

- [ ] Testar com mapa vazio
- [ ] Testar com item ID inválido
- [ ] Testar redimensionar janela durante renderização
- [ ] Testar fechar preview durante animação
- [ ] Testar com sprite corrompido/ausente

---

## 🐛 Fase 8: Debugging e Refinamento

### 8.1 Logs e Debug

- [ ] Adicionar logging para carregamento de sprites
- [ ] Adicionar logging para erros de renderização
- [ ] Criar modo debug com informações extras
- [ ] Mostrar estatísticas de cache (hit/miss rate)
- [ ] Adicionar opção de salvar screenshot do preview

### 8.2 Tratamento de Erros

- [ ] Tratar .spr/.dat não encontrados
- [ ] Tratar sprite ID fora do range
- [ ] Tratar item metadata ausente
- [ ] Mostrar placeholder para sprites faltantes
- [ ] Não crashar se houver erro em um tile

### 8.3 Otimizações

- [ ] Profile de código (identificar funções lentas)
- [ ] Otimizar loop de renderização
- [ ] Implementar dirty rectangles (renderizar só o que mudou)
- [ ] Cachear tiles inteiros se possível
- [ ] Usar sprite batching se disponível

### 8.4 Polimento

- [ ] Adicionar transições suaves ao abrir/fechar
- [ ] Melhorar feedback visual de loading
- [ ] Adicionar opções de qualidade (low/medium/high)
- [ ] Permitir zoom in/out no preview
- [ ] Adicionar minimap no preview (opcional)

## 🔮 Roadmap / Planned Features (Parity Gaps)

These features exist in the legacy RME C++ codebase and are planned for future releases:

*   **In-Game Preview Window:** A separate window to preview the map as it would appear in the Tibia client (rendering with actual game perspective and lighting).
    *   *Status:* Planned (P4).
    *   *Legacy Reference:* `RME/source/ingame_preview/`
*   **Doodad "Erase Like":** Ability to erase only items belonging to a specific doodad brush.
    *   *Status:* Pending Implementation.
    *   *Legacy Reference:* `RME/source/brushes/doodad/doodad_brush.cpp`