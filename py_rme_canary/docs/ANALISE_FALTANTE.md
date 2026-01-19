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
- ✅ GroundBrush (Terreno)
- ✅ WallBrush (Paredes)
- ✅ Auto-border básico
- ✅ BrushManager com carregamento de JSON
- ✅ BrushFactory básico

#### ❌ Faltante no Python

##### 1.1 Tipos de Brushes Especializados
- ❌ **TableBrush** - Pincel para mesas com auto-alinhamento
- ❌ **CarpetBrush** - Pincel para carpetes com bordas automáticas
- ❌ **DoorBrush** - Pincel para portas (normal, locked, magic, quest, hatch, window)
- ❌ **DoodadBrush** - Pincel para decorações complexas
- ❌ **HouseBrush** - Pincel para casas (com gerenciamento de IDs)
- ❌ **HouseExitBrush** - Pincel para saídas de casas
- ❌ **WaypointBrush** - Pincel para waypoints
- ❌ **MonsterBrush** - Pincel para monstros
- ❌ **NpcBrush** - Pincel para NPCs
- ❌ **SpawnMonsterBrush** - Pincel para spawns de monstros
- ❌ **SpawnNpcBrush** - Pincel para spawns de NPCs
- ❌ **FlagBrush** - Pincel para flags (PZ, NoPVP, NoLogout, PVP)
- ❌ **ZoneBrush** - Pincel para zonas
- ❌ **OptionalBorderBrush** - Pincel para bordas opcionais (gravel ao redor de montanhas)
- ❌ **EraserBrush** - Pincel borracha com suporte a bordas

##### 1.2 Funcionalidades Avançadas de Brushes
- ❌ **Brush Shapes** - Formas circulares e retangulares
- ❌ **Brush Size** - Tamanho configurável do pincel
- ❌ **Brush Variation** - Variação aleatória de itens
- ❌ **Brush Thickness** - Espessura customizável
- ❌ **Recent Brushes** - Histórico de pincéis recentes (máx. 20)
- ❌ **Brush Drag** - Arrastar pincel para desenhar linhas
- ❌ **Brush Smear** - Funcionalidade de "esfregar" o pincel
- ❌ **One Size Fits All** - Alguns brushes não precisam de tamanho específico

##### 1.3 Sistema de Auto-Border Avançado
- ❌ **Border Builder Window** - Interface para construir bordas customizadas
- ❌ **Border Groups** - Agrupamento de bordas relacionadas
- ❌ **Border Friends/Hate** - Sistema de compatibilidade entre brushes
- ❌ **Ground Equivalents** - Equivalências de terreno para bordas

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
- ❌ **Selection Modes**:
  - ❌ SELECT_MODE_COMPENSATE - Compensar altura
  - ❌ SELECT_MODE_CURRENT - Apenas andar atual
  - ❌ SELECT_MODE_LOWER - Andares inferiores
  - ❌ SELECT_MODE_VISIBLE - Apenas visíveis
- ❌ **Duplicate Selection** - Duplicar seleção
- ❌ **Move Selection Up/Down** - Mover seleção para cima/baixo
- ❌ **Clear Selection** - Limpar seleção

##### 2.2 Operações de Mapa
- ❌ **Borderize Selection** - Aplicar bordas na seleção
- ❌ **Borderize Map** - Aplicar bordas em todo o mapa
- ❌ **Randomize Selection** - Randomizar terreno na seleção
- ❌ **Randomize Map** - Randomizar terreno em todo o mapa
- ❌ **Clear Invalid House Tiles** - Limpar tiles inválidos de casas
- ❌ **Clear Modified Tile State** - Limpar estado modificado

##### 2.3 Sistema de Ações (Actions)
- ❌ **ActionQueue** completo com:
  - ❌ Stacking delay (agrupamento automático de ações)
  - ❌ Batch actions (ações em lote)
  - ❌ Action labels (rótulos descritivos)
  - ❌ Action timer (reset de timer)
- ❌ **NetworkedActionQueue** - Para modo live
- ❌ **Action Types**:
  - ❌ ACTION_DRAW
  - ❌ ACTION_ERASE
  - ❌ ACTION_MOVE
  - ❌ ACTION_ROTATE
  - ❌ ACTION_REPLACE
  - ❌ E outros tipos específicos

---

### 3. Sistema de Renderização e Visualização

#### ✅ Implementado no Python
- ✅ MapCanvasWidget básico (PyQt6)
- ✅ Renderização básica de tiles
- ✅ Viewport com zoom
- ✅ Minimap básico

#### ❌ Faltante no Python

##### 3.1 Renderização OpenGL
- ❌ **OpenGL Context** - Contexto GL para renderização acelerada
- ❌ **MapDrawer** completo com:
  - ❌ Renderização de sprites com OpenGL
  - ❌ Sistema de camadas (layers)
  - ❌ Renderização de pisos superiores/inferiores
  - ❌ Sombreado (shade) de pisos inferiores
  - ❌ Renderização de seleção
  - ❌ Renderização de brush preview
  - ❌ Renderização de grid
  - ❌ Renderização de "ingame box"
  - ❌ Renderização de tooltips
  - ❌ Renderização de cursors live
  - ❌ Renderização de dragging shadow

##### 3.2 Sistema de Sprites
- ❌ **GraphicManager** completo:
  - ❌ Carregamento de sprites de arquivos DAT/SPR
  - ❌ Cache de sprites
  - ❌ Gerenciamento de memória (cleanup)
  - ❌ Suporte a múltiplos tamanhos (16x16, 32x32, 64x64)
  - ❌ Animações de sprites
  - ❌ Sprite sheets (folhas de sprites)
- ❌ **SpriteAppearances** completo:
  - ❌ Carregamento de protobuf appearances
  - ❌ Mapeamento de sprite IDs
  - ❌ Suporte a diferentes versões de cliente

##### 3.3 Opções de Visualização
- ❌ **DrawingOptions** completo:
  - ❌ SHOW_SHADE - Mostrar sombra
  - ❌ SHOW_ALL_FLOORS - Mostrar todos os andares
  - ❌ GHOST_ITEMS - Itens fantasmas
  - ❌ GHOST_HIGHER_FLOORS - Pisos superiores fantasmas
  - ❌ HIGHLIGHT_ITEMS - Destacar itens
  - ❌ SHOW_INGAME_BOX - Mostrar caixa in-game
  - ❌ SHOW_LIGHTS - Mostrar iluminação
  - ❌ SHOW_LIGHT_STRENGTH - Mostrar força da luz
  - ❌ SHOW_GRID - Mostrar grade
  - ❌ SHOW_EXTRA - Mostrar extras
  - ❌ SHOW_MONSTERS - Mostrar monstros
  - ❌ SHOW_SPAWNS_MONSTER - Mostrar spawns de monstros
  - ❌ SHOW_NPCS - Mostrar NPCs
  - ❌ SHOW_SPAWNS_NPC - Mostrar spawns de NPCs
  - ❌ SHOW_SPECIAL - Mostrar tiles especiais
  - ❌ SHOW_AS_MINIMAP - Mostrar como minimap
  - ❌ SHOW_ONLY_COLORS - Mostrar apenas cores
  - ❌ SHOW_ONLY_MODIFIED - Mostrar apenas modificados
  - ❌ SHOW_HOUSES - Mostrar casas
  - ❌ SHOW_PATHING - Mostrar pathfinding
  - ❌ SHOW_TOOLTIPS - Mostrar tooltips
  - ❌ SHOW_PREVIEW - Mostrar preview
  - ❌ SHOW_WALL_HOOKS - Mostrar ganchos de parede
  - ❌ SHOW_PICKUPABLES - Mostrar itens coletáveis
  - ❌ SHOW_MOVEABLES - Mostrar itens móveis
  - ❌ SHOW_AVOIDABLES - Mostrar itens evitáveis

##### 3.4 Sistema de Iluminação
- ❌ **LightDrawer** - Sistema completo de renderização de luzes
- ❌ Cálculo de iluminação baseado em sprites
- ❌ Visualização de intensidade de luz
- ❌ Cores de luz customizáveis

##### 3.5 Screenshots
- ❌ **Take Screenshot** - Captura de tela do mapa
- ❌ Suporte a múltiplos formatos (PNG, BMP, etc.)

---

### 4. Sistema de Live Server/Client (Colaboração em Tempo Real)

#### ❌ Completamente Faltante

##### 4.1 Live Server
- ❌ **LiveServer** completo:
  - ❌ Bind em porta TCP
  - ❌ Aceitar conexões de clientes
  - ❌ Broadcast de mudanças para clientes
  - ❌ Gerenciamento de clientes conectados
  - ❌ Sistema de IDs de cliente
  - ❌ Chat entre clientes
  - ❌ Broadcast de cursors
  - ❌ Broadcast de operações (progress bars)
  - ❌ Kick de clientes
  - ❌ Log de atividades

##### 4.2 Live Client
- ❌ **LiveClient** completo:
  - ❌ Conectar a servidor
  - ❌ Enviar mudanças para servidor
  - ❌ Receber mudanças do servidor
  - ❌ Request de nodes (regiões do mapa)
  - ❌ Sincronização de estado
  - ❌ Chat com outros clientes
  - ❌ Visualização de cursors de outros clientes
  - ❌ Log de atividades

##### 4.3 Live Socket
- ❌ **LiveSocket** - Base para server/client
- ❌ Protocolo de comunicação
- ❌ Parsing de pacotes
- ❌ Envio de mensagens

##### 4.4 Live Peer
- ❌ **LivePeer** - Representação de cliente conectado no servidor
- ❌ Gerenciamento de conexão individual
- ❌ Envio/recebimento de dados

##### 4.5 Live Tab
- ❌ **LiveTab** - Interface para modo live
- ❌ Log de atividades
- ❌ Lista de clientes conectados
- ❌ Chat interface

---

### 5. Sistema de Importação/Exportação

#### ✅ Implementado no Python
- ✅ Carregamento OTBM básico
- ✅ Salvamento OTBM básico
- ✅ Carregamento de XML (houses, spawns, zones)

#### ❌ Faltante no Python

##### 5.1 Importação
- ❌ **Import Map** - Importar outro mapa com:
  - ❌ Offset X/Y/Z
  - ❌ Opções de importação de casas (MERGE, SMART_MERGE, INSERT, DONT)
  - ❌ Opções de importação de spawns (MERGE, DONT)
  - ❌ Opções de importação de NPCs (MERGE, DONT)
- ❌ **Import Monsters** - Importar arquivo XML de monstros
- ❌ **Import NPCs** - Importar arquivo XML de NPCs
- ❌ **Import Minimap** - Importar minimap com offset

##### 5.2 Exportação
- ❌ **Export Minimap** - Exportar minimap como imagem:
  - ❌ Formato BMP
  - ❌ Seleção de piso
  - ❌ Opções de visualização
- ❌ **Export Tilesets** - Exportar tilesets

##### 5.3 Formatos Suportados
- ❌ **OTMM** - Formato alternativo de mapa (IOMapOTMM)
- ❌ Conversão entre formatos OTBM v1/v2
- ❌ Detecção automática de versão

---

### 6. Sistema de Busca e Substituição

#### ✅ Implementado no Python
- ✅ Busca básica de itens
- ✅ Busca de waypoints
- ✅ Estatísticas básicas do mapa

#### ❌ Faltante no Python

##### 6.1 Busca Avançada
- ❌ **Search on Map**:
  - ❌ SEARCH_ON_MAP_EVERYTHING - Buscar tudo
  - ❌ SEARCH_ON_MAP_UNIQUE - Buscar únicos
  - ❌ SEARCH_ON_MAP_ACTION - Buscar com action
  - ❌ SEARCH_ON_MAP_CONTAINER - Buscar containers
  - ❌ SEARCH_ON_MAP_WRITEABLE - Buscar writeables
  - ❌ SEARCH_ON_MAP_DUPLICATED_ITEMS - Buscar itens duplicados
  - ❌ SEARCH_ON_MAP_WALLS_UPON_WALLS - Buscar paredes sobre paredes

##### 6.2 Busca em Seleção
- ❌ **Search on Selection**:
  - ❌ SEARCH_ON_SELECTION_EVERYTHING
  - ❌ SEARCH_ON_SELECTION_UNIQUE
  - ❌ SEARCH_ON_SELECTION_ACTION
  - ❌ SEARCH_ON_SELECTION_CONTAINER
  - ❌ SEARCH_ON_SELECTION_WRITEABLE
  - ❌ SEARCH_ON_SELECTION_ITEM
  - ❌ SEARCH_ON_SELECTION_DUPLICATED_ITEMS

##### 6.3 Substituição
- ❌ **Replace Items** - Substituir itens no mapa
- ❌ **Replace on Selection** - Substituir itens na seleção
- ❌ **Remove Items** - Remover itens específicos
- ❌ **Remove on Selection** - Remover itens da seleção
- ❌ **Remove Monsters** - Remover monstros da seleção
- ❌ **Count Monsters** - Contar monstros na seleção
- ❌ **Remove Duplicates** - Remover duplicados

##### 6.4 Busca de Criaturas
- ❌ **Find Creature** - Buscar criaturas (monstros/NPCs) no mapa

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
- ❌ **Properties Window** - Janela completa de propriedades:
  - ❌ Edição de propriedades de tile
  - ❌ Edição de propriedades de item
  - ❌ Edição de propriedades de casa
  - ❌ Edição de propriedades de spawn
  - ❌ Edição de propriedades de waypoint
  - ❌ Edição de propriedades de zona
- ❌ **Container Properties Window** - Propriedades de containers
- ❌ **Old Properties Window** - Janela legada de propriedades

##### 8.2 Edição de Entidades
- ❌ **Edit Towns** - Editor de cidades
- ❌ **Edit Items** - Editor de itens (database)
- ❌ **Edit Monsters** - Editor de monstros (database)
- ❌ **Map Properties** - Propriedades do mapa

##### 8.3 Operações de Item
- ❌ **Rotate Item** - Rotacionar item
- ❌ **Switch Door** - Alternar estado de porta
- ❌ **Copy Item ID** - Copiar ID do item
- ❌ **Copy Name** - Copiar nome do item
- ❌ **Browse Tile** - Navegar tile

---

### 9. Sistema de Paleta (Palette)

#### ✅ Implementado no Python
- ✅ PaletteManager básico
- ✅ Carregamento de brushes do JSON

#### ❌ Faltante no Python

##### 9.1 Tipos de Paleta
- ❌ **Terrain Palette** - Paleta de terrenos
- ❌ **Doodad Palette** - Paleta de decorações
- ❌ **Item Palette** - Paleta de itens
- ❌ **House Palette** - Paleta de casas:
  - ❌ Lista de casas
  - ❌ Adicionar/editar/remover casas
  - ❌ Seleção de cidade
  - ❌ Seleção de saída
- ❌ **Monster Palette** - Paleta de monstros
- ❌ **NPC Palette** - Paleta de NPCs
- ❌ **Waypoint Palette** - Paleta de waypoints:
  - ❌ Lista de waypoints
  - ❌ Gerenciamento de waypoints
- ❌ **Zones Palette** - Paleta de zonas
- ❌ **Raw Palette** - Paleta raw (itens diretos)

##### 9.2 Funcionalidades de Paleta
- ❌ **Multiple Palettes** - Múltiplas paletas abertas
- ❌ **Palette Actions** - Ações na paleta:
  - ❌ Action ID enable/disable
  - ❌ Action ID value
- ❌ **Palette Refresh** - Atualização de conteúdo
- ❌ **Palette Rebuild** - Reconstrução completa

---

### 10. Sistema de Navegação e Posicionamento

#### ✅ Implementado no Python
- ✅ Viewport básico
- ✅ Zoom básico

#### ❌ Faltante no Python

##### 10.1 Navegação
- ❌ **Goto Position** - Ir para posição específica
- ❌ **Goto Previous Position** - Voltar para posição anterior
- ❌ **Position History** - Histórico de posições
- ❌ **Copy Position** - Copiar posição atual
- ❌ **Jump to Brush** - Pular para posição de um brush
- ❌ **Jump to Item Brush** - Pular para item brush

##### 10.2 Mirror Drawing (Desenho Espelhado)
- ❌ **Toggle Mirror Drawing** - Ativar/desativar desenho espelhado
- ❌ **Mirror Axis X** - Eixo X de espelhamento
- ❌ **Mirror Axis Y** - Eixo Y de espelhamento
- ❌ **Set Mirror Axis from Cursor** - Definir eixo a partir do cursor

##### 10.3 Visualização
- ❌ **Fit View to Map** - Ajustar visualização ao mapa
- ❌ **New View** - Nova visualização (janela)
- ❌ **Toggle Fullscreen** - Tela cheia
- ❌ **Zoom In/Out/Normal** - Controles de zoom

---

### 11. Sistema de Hotkeys (Atalhos)

#### ❌ Completamente Faltante

- ❌ **Hotkey System** - Sistema completo de atalhos:
  - ❌ 10 hotkeys configuráveis
  - ❌ Hotkeys para posições
  - ❌ Hotkeys para brushes
  - ❌ Salvamento/carregamento de hotkeys
  - ❌ Interface de configuração

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
- ✅ Estatísticas básicas do mapa

#### ❌ Faltante no Python

##### 13.1 Estatísticas Avançadas
- ❌ **Map Statistics Window** completa:
  - ❌ Contagem de tiles
  - ❌ Contagem de itens por tipo
  - ❌ Contagem de casas
  - ❌ Contagem de spawns
  - ❌ Contagem de waypoints
  - ❌ Contagem de zonas
  - ❌ Export para XML
  - ❌ Estatísticas detalhadas por categoria

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

#### ❌ Completamente Faltante

- ❌ **About Window** - Janela "Sobre":
  - ❌ Informações da versão
  - ❌ Créditos
  - ❌ Licença
  - ❌ Links úteis

---

### 19. Sistema de Toolbars

#### ❌ Completamente Faltante

- ❌ **Main Toolbar** - Barra de ferramentas principal:
  - ❌ Toolbar de brushes
  - ❌ Toolbar de posição
  - ❌ Toolbar de tamanhos
  - ❌ Toolbar de indicadores
  - ❌ Toolbar padrão
- ❌ **Toggle Toolbars** - Mostrar/ocultar toolbars

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
- ✅ ActionsHistoryDock básico

#### ❌ Faltante no Python

- ❌ **Actions History Window** completa:
  - ❌ Lista completa de ações
  - ❌ Navegação no histórico
  - ❌ Labels descritivos
  - ❌ Filtros

---

### 24. Sistema de Minimap

#### ✅ Implementado no Python
- ✅ MinimapWidget básico

#### ❌ Faltante no Python

- ❌ **Minimap Window** completa:
  - ❌ Renderização completa do minimap
  - ❌ Navegação pelo minimap
  - ❌ Indicador de posição atual
  - ❌ Zoom do minimap
  - ❌ Atualização em tempo real

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

#### ❌ Completamente Faltante

- ❌ **Map Conversion** - Conversão entre versões:
  - ❌ Conversão OTBM v1 para v2
  - ❌ Conversão v2 para v1
  - ❌ ConversionMap - Mapeamento de conversão
  - ❌ Validação de conversão

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

### Funcionalidades por Categoria

| Categoria | Implementado | Faltante | % Completo |
|-----------|--------------|----------|------------|
| Brushes | 4 | 20+ | ~15% |
| Editor/Sessão | 6 | 15+ | ~30% |
| Renderização | 3 | 25+ | ~10% |
| Live Server/Client | 0 | 20+ | 0% |
| Import/Export | 3 | 10+ | ~25% |
| Busca/Substituição | 3 | 15+ | ~15% |
| Limpeza/Manutenção | 0 | 7 | 0% |
| Propriedades | 1 | 10+ | ~10% |
| Paleta | 1 | 10+ | ~10% |
| Navegação | 2 | 10+ | ~15% |
| Hotkeys | 0 | 5+ | 0% |
| Preferências | 2 | 10+ | ~15% |
| Estatísticas | 1 | 5+ | ~15% |
| Templates | 0 | 5+ | 0% |
| Tilesets | 0 | 5+ | 0% |
| Menus | 3 | 20+ | ~15% |
| Popup Menus | 0 | 10+ | 0% |
| Toolbars | 0 | 5+ | 0% |
| **TOTAL** | **~30** | **~200+** | **~13%** |

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
