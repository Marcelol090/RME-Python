# Documentação do Sistema - Remere's Map Editor (RME)

## Visão Geral
O Remere's Map Editor (RME) é uma ferramenta de código aberto projetada para a criação e edição de mapas para servidores de OpenTibia. Ele permite que desenvolvedores de jogos e mapeadores criem mundos complexos, posicionando itens, criaturas, definindo áreas de casas, cidades e zonas especiais.

## Principais Componentes e Suas Funções

### 1. Interface Gráfica (GUI)
- **Arquivos principais:** `gui.cpp`, `main_menubar.cpp`, `main_toolbar.cpp`, `palette_window.cpp`.
- **Função:** Utiliza a biblioteca **wxWidgets** para fornecer uma interface amigável. Gerencia janelas de ferramentas, paletas de itens, menus de contexto e diálogos de propriedades.

### 2. Motor de Mapa (Map Engine)
- **Arquivos principais:** `map.cpp`, `tile.cpp`, `item.cpp`, `map_region.cpp`.
- **Função:** Gerencia a estrutura de dados do mapa. Organiza os tiles (pisos) e itens em camadas e posições tridimensionais (X, Y, Z). Utiliza regiões para otimizar o carregamento e a renderização de grandes áreas.

### 3. Sistema de Brushes (Pincéis)
- **Arquivos principais:** `brush.cpp`, `ground_brush.cpp`, `wall_brush.cpp`, `doodad_brush.cpp`.
- **Função:** É o "coração" da edição produtiva. Os brushes automatizam a colocação de bordas, cantos e transições entre diferentes tipos de terreno ou paredes, poupando o trabalho manual do mapeador.

### 4. Sistema de I/O (Entrada e Saída)
- **Arquivos principais:** `iomap_otbm.cpp`, `iomap_otmm.cpp`, `iominimap.cpp`.
- **Função:** Responsável por ler e gravar arquivos no formato **OTBM** (OpenTibia Binary Map). Também gerencia a exportação/importação de minimapas e arquivos de spawns (monstros e NPCs) em XML.

### 5. Edição em Tempo Real (Live Editing)
- **Arquivos principais:** `live_server.cpp`, `live_client.cpp`, `live_socket.cpp`.
- **Função:** Permite que múltiplos usuários se conectem a uma sessão e editem o mesmo mapa simultaneamente, com sincronização de ações via rede.

### 6. Gerenciamento de Assets
- **Arquivos principais:** `client_assets.cpp`, `sprites.h`, `items.cpp`.
- **Função:** Carrega os arquivos do cliente do Tibia (`.spr`, `.dat` ou versões mais recentes) e os arquivos de definição de itens (`items.otb`, `items.xml`) para garantir que o que é visto no editor corresponda ao que será visto no jogo.

---

## Possíveis Melhorias

### 1. Desempenho e Otimização
- **Renderização:** O uso de OpenGL pode ser otimizado para lidar melhor com mapas extremamente grandes e muitos efeitos de luz simultâneos.
- **Consumo de Memória:** O sistema de Undo/Redo (`action.cpp`) pode consumir muita memória em operações em massa. Implementar um sistema de compressão para o histórico de ações seria benéfico.

### 2. Modernização da Interface (UI/UX)
- **Temas:** Suporte nativo a "Dark Mode" e personalização de cores da interface.
- **UX:** Melhorar a busca de itens com filtros mais avançados (por ID, por versão, por propriedades como "atravessável").

### 3. Automação e Scripting
- **Engine de Script:** Integrar uma linguagem como **Lua** ou **Python** para permitir que usuários criem seus próprios scripts de automação ou brushes customizados sem precisar recompilar o editor.

### 4. Melhorias Técnicas (Baseadas no Código)
- **Compressão Zlib:** Implementar a flag de compressão zlib no minimapa (conforme indicado em `iominimap.cpp`).
- **Tratamento de Erros em Rede:** Refinar o tratamento de exceções e falhas de conexão no sistema de Live Editing para evitar crashes quando a conexão é instável.
- **Refatoração de Código Antigo:** Algumas partes do código ainda utilizam padrões de C++ mais antigos. A migração para C++17/20 em mais áreas pode melhorar a legibilidade e segurança.

### 5. Suporte a Novas Versões
- Manter o suporte atualizado para os protocolos mais recentes do cliente oficial, incluindo novos sistemas de montarias, outfits e efeitos de partículas.
