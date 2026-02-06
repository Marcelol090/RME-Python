# Documento de Requisitos do Produto (PRD)

**Projeto:** py_rme_canary (Modern Remere's Map Editor)
**Versão:** 1.0 (Draft)
**Status:** Ativo
**Autor:** Gemini (Arquiteto Principal)

---

## 1. Visão do Produto
Portar e modernizar com sucesso o legado Remere's Map Editor (RME) em C++ para uma aplicação de alto desempenho baseada em Python usando PyQt6. O objetivo é duplo:
1.  **Paridade Absoluta:** Replicar 100% da funcionalidade do RME git-master (incluindo suporte a OTBM, edição Live e auto-bordering).
2.  **UX Premium:** Elevar a experiência do usuário com padrões de design modernos (Dark Mode, Glassmorphism, fluxos intuitivos) mantendo a familiaridade da ferramenta clássica.

## 2. Público-Alvo
*   **Mappers de Open Tibia:** Usuários criando mapas para servidores OT (7.4 a 13.x+).
*   **Administradores de Servidores:** Usuários gerenciando dados do servidor e compatibilidade de mapas.
*   **Criadores de Conteúdo:** Designers que requerem ferramentas de precisão para construção de mundos em larga escala.

---

## 3. Requisitos de UI/UX
A interface deve gritar "Moderno & Profissional".

### 3.1 Estilo Visual
*   **Tema:** Dark Mode Nativo (paleta Dracula ou Nord) por padrão. Sem widgets Qt "cinza padrão".
*   **Estilização:**
    *   Uso de `QSS` para estilização completa.
    *   "Glassmorphism" sutil em overlays/painéis (fundos semi-transparentes com desfoque).
    *   Cantos arredondados (4px-8px) em containers.
    *   Iconografia: Ícones vetoriais/SVG de alta DPI substituindo ícones de pixel art legados onde apropriado (ou pixel art redimensionado para nostalgia).

### 3.2 Layout & Interação
*   **Sistema de Docking:** Layout totalmente personalizável usando `QDockWidget`. Usuários podem reorganizar Palette, Minimap e Item List.
*   **Responsividade:** Transições suaves (ex: hover states, fading de menus).
*   **Feedback:** Feedback visual imediato para ações (ex: destacar bordas ao usar o pincel "Magic", mensagens claras na barra de status).
*   **Experiência de Inicialização:** Um diálogo de "Boas-vindas/Launcher" para selecionar Versão do Cliente e Caminho de Assets antes de carregar o editor principal.

---

## 4. Fluxos de Usuário

### 4.1 Inicialização & Configuração
1.  **Launch:** Usuário abre `py_rme_canary`.
2.  **Diálogo de Boas-vindas:**
    *   Usuário vê "Novo Mapa", "Abrir Mapa", "Arquivos Recentes".
    *   Usuário valida/navega pelos Dados do Cliente Tibia (SPR/DAT).
3.  **Carregamento:** Barra de progresso mostra status de carregamento de assets.
4.  **Interface Principal:** O grid renderizando o mapa aparece centralmente, com ferramentas na lateral.

### 4.2 Mapeamento Principal
1.  **Seleção:** Usuário seleciona um "Brush" da Palette (ex: "Ground Brush", "Wall Brush").
2.  **Edição:**
    *   **Clique-Esquerdo:** Coloca o item/tile. Lógica de auto-bordering roda instantaneamente.
    *   **Clique-Direito:** Apaga ou executa ação específica de contexto.
    *   **Shift + Arrastar:** Seleciona uma região (Retângulo ou Laço).
3.  **Navegação:**
    *   **Scroll:** Panorâmica do mapa.
    *   **Ctrl+Scroll:** Zoom in/out.
    *   **PageUp/Down:** Muda andar (Eixo Z).

### 4.3 Busca & Substituição (Produtividade)
1.  **Gatilho:** Usuário pressiona `Ctrl+F` (Buscar) ou `Ctrl+H` (Substituir).
2.  **Diálogo:** Um diálogo não-bloqueante aparece.
3.  **Ação:** Usuário seleciona "Find Item: Demon" -> Lista de resultados aparece. Clicar em um resultado salta a câmera para aquele local.

---

## 5. Requisitos Funcionais
Todas as funcionalidades devem corresponder ao comportamento do Legacy RME a menos que explicitamente melhoradas.

### 5.1 E/S de Mapa & Dados
*   **Formatos:** Carregar/Salvar OTBM (versões 1-6), Importar XML/OTBM.
*   **Exportar:** Exportar Minimap (PNG/OTMM), Exportar Seleção para Imagem.
*   **Suporte ao Cliente:** Suporte total para Tibia.dat/Tibia.spr das versões 7.4 até 13.x+.
*   **Gerenciamento de Perfis:** Salvar/Carregar caminhos para diferentes versões de cliente (Perfis de Cliente).

### 5.2 Ferramentas de Edição (Brushes)
*   **Terreno:** Grama, Água, Caverna, etc. (Auto-bordering).
*   **Parede:** Paredes com junção automática, diferentes orientações.
*   **Doodad:** Colocação aleatória de detalhes (pedras, flores).
*   **Item:** Itens genéricos únicos (paleta RAW).
*   **Criatura:** Colocar Monstros/NPCs (suporta configuração de tempo de Spawn).
*   **Casa:** Definir tiles de casa e coordenadas de saída.
*   **Borracha:** Apagar sensível ao contexto.
*   **Waypoint:** Adicionar waypoints para NPCs/monstros (suporte a recurso legado).

### 5.3 Ferramentas Avançadas
*   **Seleção:**
    *   Seleção Retangular.
    *   **[Novo]** Seleção Laço/Mão-livre (Polígono).
*   **Transformação:** Copiar, Recortar, Colar, Rotacionar Seleção.
*   **Automagic:** Borderizar Seleção, Randomizar Seleção.
*   **Edição Live:** Hospedar uma sessão, permitir que outros clientes entrem e editem simultaneamente.

### 5.4 Janelas & Diálogos
*   **Propriedades do Mapa:** Editar dimensões, descrição, autor.
*   **Cidades:** Gerenciar IDs de Cidades e Templos.
*   **Localizar/Substituir:** Filtros de busca detalhados (por item, ID, propriedade).
*   **Minimap:** Auxílio de navegação em tempo real.
*   **Estatísticas do Mapa:** Mostrar contagem de itens/criaturas.
*   **Gerenciador de Extensões:** Carregar/Descarregar extensões Python/Lua.

### 5.5 Menus
*   **Arquivo:** Novo, Abrir, Salvar, Importar (Mapa/Monstros/Minimap), Exportar (Minimap/Tilesets), Preferências.
*   **Editar:** Desfazer/Refazer, Recortar/Copiar/Colar, Ferramentas de Seleção.
*   **Mapa:** Propriedades, Estatísticas, Limpeza, Redimensionar, Remover Itens/Corpos.
*   **Exibir:** Zoom (In/Out/Normal), Grid, Mostrar sombras/ghosting, Tela Cheia.
*   **Live:** Hospedar/Entrar/Configurações.
*   **Janela:** Gerenciar painéis acoplados (Minimap, Palette, Opções de Ferramenta).

---

## 6. Restrições Técnicas
*   **Linguagem:** Python 3.10+
*   **Framework GUI:** PyQt6
*   **Desempenho:**
    *   Renderização deve lidar com 200x200 tiles visíveis a 60 FPS.
    *   Carregamentos de mapas grandes (100MB+ OTBM) não devem congelar a UI por > 5 segundos (usar threading).
*   **Compatibilidade:** Windows 10/11, Linux (Ubuntu/Debian).

## 7. Dicionário & Terminologia
*   **OTBM:** Formato Open Tibia Binary Map.
*   **Auto-border:** Lógica que coloca automaticamente tiles de borda com base nos vizinhos.
*   **Doodad:** Itens decorativos colocados sobre o chão.
*   **CID/SID:** Client ID (ID do sprite) vs Server ID (ID do tipo de item).
