# Proposta de Reorganização Arquitetural - py_rme_canary

## 📋 Sumário Executivo

Este documento propõe uma reorganização profissional da estrutura de pastas e módulos do `py_rme_canary`, seguindo princípios de arquitetura de software como:

- **Single Responsibility Principle (SRP)**: Cada módulo tem uma única responsabilidade
- **Separation of Concerns (SoC)**: Separação clara entre camadas
- **Don't Repeat Yourself (DRY)**: Extração de código duplicado
- **Clean Architecture**: Dependências fluem de fora para dentro

---

## 🏗️ Estrutura Atual (Análise)

### Problemas Identificados

| Arquivo | Linhas | Problema |
|---------|--------|----------|
| `core/io/otbm_loader.py` | 1262 | Múltiplas responsabilidades: parsing, streaming, validação, carregamento externo |
| `logic_layer/editor_session.py` | 966 | Mistura seleção, clipboard, gestos, paste e borderize |
| `logic_layer/auto_border.py` | 891 | Cálculo de máscaras, seleção de alinhamento, processamento juntos |
| `vis_layer/qt_app.py` | 1290 | UI, sprites, operações de mapa, view controller misturados |
| `core/io/otbm_saver.py` | 554 | Aceitável, mas pode ser modularizado |

### Código Duplicado Identificado

- **Constantes OTBM**: Duplicadas em `otbm_loader.py` e `otbm_saver.py`
- **Node parsing**: Lógica similar para escape/unescape em loader/saver
- **Helpers de parsing XML**: Funções `_as_int`, `_as_bool` duplicadas em múltiplos arquivos

---

## 🎯 Estrutura Proposta

```
py_rme_canary/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── constants/                    # 🆕 NOVO
│   │   ├── __init__.py
│   │   ├── otbm.py                   # Constantes OTBM (NODE_*, OTBM_ATTR_*, etc)
│   │   ├── item_attributes.py        # Constantes de atributos de item
│   │   └── magic.py                  # Magic bytes (OTBM, OTBI, etc)
│   │
│   ├── exceptions/                   # 🆕 NOVO
│   │   ├── __init__.py
│   │   ├── io.py                     # OTBMParseError, ItemsXMLError, etc
│   │   ├── config.py                 # ConfigurationError, ProjectError
│   │   └── mapping.py                # IdMappingError
│   │
│   ├── protocols/                    # 🆕 NOVO (typing/interfaces)
│   │   ├── __init__.py
│   │   └── tile_recorder.py          # TileChangeRecorder protocol
│   │
│   ├── assets/
│   │   ├── __init__.py
│   │   └── sprite_appearances.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── configuration_manager.py
│   │   └── project.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── models/                   # 🆕 Subpasta para modelos
│   │   │   ├── __init__.py
│   │   │   ├── position.py           # Extraído de item.py
│   │   │   ├── item.py               # Item, ItemAttribute
│   │   │   ├── tile.py
│   │   │   ├── house.py
│   │   │   ├── spawn.py              # Renomeado de spawns.py
│   │   │   └── zone.py               # Renomeado de zones.py
│   │   │
│   │   └── gamemap.py                # GameMap, MapHeader, LoadReport
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── id_mapper.py
│   │   ├── items_otb.py
│   │   └── items_xml.py
│   │
│   └── io/
│       ├── __init__.py
│       ├── atomic_io.py
│       ├── map_detection.py
│       │
│       ├── otbm/                     # 🆕 Subpasta para OTBM
│       │   ├── __init__.py
│       │   ├── streaming.py          # EscapedPayloadReader, node stream
│       │   ├── node_parser.py        # Parsing de nós genéricos
│       │   ├── item_parser.py        # Parsing de items OTBM
│       │   ├── tile_parser.py        # Parsing de tiles
│       │   ├── header_parser.py      # Parsing de headers/root
│       │   ├── loader.py             # OTBMLoader (orquestra tudo)
│       │   └── saver.py              # OTBMSaver (renomeado)
│       │
│       └── xml/                      # 🆕 Subpasta para XML
│           ├── __init__.py
│           ├── base.py               # Helpers compartilhados (_as_int, _as_bool)
│           ├── houses.py
│           ├── spawns.py
│           └── zones.py
│
├── logic_layer/
│   ├── __init__.py
│   │
│   ├── brushes/                      # 🆕 Subpasta para brushes
│   │   ├── __init__.py
│   │   ├── base.py                   # Brush, AutoBorderBrush
│   │   ├── definitions.py            # BrushDefinition
│   │   ├── manager.py                # BrushManager
│   │   └── factory.py                # BrushFactory
│   │
│   ├── borders/                      # 🆕 Subpasta para auto-border
│   │   ├── __init__.py
│   │   ├── neighbor_mask.py          # Cálculo de máscaras de vizinhos
│   │   ├── alignment.py              # Seleção de alinhamento
│   │   ├── transitions.py            # Bordas de transição
│   │   └── processor.py              # AutoBorderProcessor
│   │
│   ├── session/                      # 🆕 Subpasta para editor session
│   │   ├── __init__.py
│   │   ├── editor.py                 # EditorSession principal (slim)
│   │   ├── selection.py              # Lógica de seleção
│   │   ├── clipboard.py              # Copy/Cut/Paste buffer
│   │   ├── gestures.py               # Mouse down/move/up handling
│   │   └── move.py                   # Operações de movimentação
│   │
│   ├── history/                      # 🆕 Subpasta para undo/redo
│   │   ├── __init__.py
│   │   ├── action.py                 # PaintAction
│   │   ├── manager.py                # HistoryManager
│   │   └── stroke.py                 # TransactionalBrushStroke
│   │
│   ├── operations/                   # 🆕 Subpasta para operações
│   │   ├── __init__.py
│   │   ├── replace.py                # replace_items_in_map
│   │   ├── remove.py                 # remove_items_in_map
│   │   ├── search.py                 # find_item_positions, find_waypoints
│   │   └── statistics.py             # compute_map_statistics
│   │
│   ├── geometry.py                   # Mantido (pequeno)
│   └── mirroring.py                  # Mantido (pequeno)
│
├── vis_layer/
│   ├── __init__.py
│   │
│   ├── sprites/                      # 🆕 Subpasta para sprites
│   │   ├── __init__.py
│   │   ├── cache.py                  # Sprite cache
│   │   └── renderer.py               # Renderização de sprites
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   ├── indicators.py
│   │   │
│   │   ├── canvas/                   # 🆕 Subpasta para canvas
│   │   │   ├── __init__.py
│   │   │   ├── widget.py             # MapCanvasWidget
│   │   │   ├── painter.py            # Lógica de pintura
│   │   │   └── events.py             # Handlers de eventos
│   │   │
│   │   ├── docks/                    # 🆕 Subpasta para docks
│   │   │   ├── __init__.py
│   │   │   ├── minimap.py
│   │   │   ├── palette.py
│   │   │   └── actions_history.py
│   │   │
│   │   └── main_window/              # Mantida e expandida
│   │       ├── __init__.py
│   │       ├── window.py             # 🆕 Classe principal extraída
│   │       ├── build_actions.py
│   │       ├── build_docks.py
│   │       ├── build_menus.py
│   │       ├── dialogs.py
│   │       ├── find_item.py
│   │       ├── find_on_map.py
│   │       ├── view_controller.py    # 🆕 Controle de visualização
│   │       └── map_operations.py     # 🆕 Open/Save/New
│   │
│   └── qt_app.py                     # Simplificado (entry point)
│
└── tools/
    ├── __init__.py
    ├── export_brushes_json.py
    └── read_otbm_header.py
```

---

## 📦 Detalhamento das Mudanças

### 1. `core/constants/` (NOVO)

**Objetivo**: Centralizar todas as constantes mágicas

```python
# core/constants/otbm.py
NODE_START = 0xFE
NODE_END = 0xFF
ESCAPE_CHAR = 0xFD

# Node types
OTBM_ROOTV1 = 0x01
OTBM_MAP_DATA = 0x02
OTBM_TILE_AREA = 0x04
# ... etc

# Attributes
OTBM_ATTR_DESCRIPTION = 1
OTBM_ATTR_EXT_SPAWN_MONSTER_FILE = 11
# ... etc
```

### 2. `core/io/otbm/` (NOVO)

**Objetivo**: Dividir 1262 linhas em módulos coesos

| Módulo | Responsabilidade | ~Linhas |
|--------|-----------------|---------|
| `streaming.py` | `EscapedPayloadReader`, leitura de bytes | ~100 |
| `node_parser.py` | Parsing genérico de nós | ~150 |
| `item_parser.py` | Parsing de items e atributos | ~200 |
| `tile_parser.py` | Parsing de tiles e tile areas | ~150 |
| `header_parser.py` | Parsing de root/header/waypoints | ~150 |
| `loader.py` | `OTBMLoader` (orquestra) | ~300 |
| `saver.py` | `OTBMSaver` | ~250 |

### 3. `logic_layer/session/` (NOVO)

**Objetivo**: Dividir 966 linhas em módulos focados

| Módulo | Responsabilidade | ~Linhas |
|--------|-----------------|---------|
| `editor.py` | `EditorSession` core | ~200 |
| `selection.py` | Box selection, selection tiles | ~150 |
| `clipboard.py` | Copy buffer, cut/paste state | ~150 |
| `gestures.py` | Mouse handling | ~150 |
| `move.py` | Move selection operations | ~200 |

### 4. `logic_layer/borders/` (NOVO)

**Objetivo**: Dividir 891 linhas em módulos especializados

| Módulo | Responsabilidade | ~Linhas |
|--------|-----------------|---------|
| `neighbor_mask.py` | Cálculo de máscaras | ~100 |
| `alignment.py` | `select_border_alignment` | ~150 |
| `transitions.py` | Bordas de transição | ~200 |
| `processor.py` | `AutoBorderProcessor` | ~350 |

### 5. `vis_layer/ui/canvas/` (NOVO)

**Objetivo**: Separar widget de renderização de lógica de eventos

| Módulo | Responsabilidade |
|--------|-----------------|
| `widget.py` | Classe `MapCanvasWidget` |
| `painter.py` | Métodos de pintura |
| `events.py` | Handlers de mouse/teclado |

---

## 🔄 Compatibilidade Retroativa

Para manter compatibilidade com código existente, todos os `__init__.py` exportarão os símbolos públicos:

```python
# core/io/__init__.py
from .otbm.loader import OTBMLoader
from .otbm.saver import save_game_map_bundle_atomic

# logic_layer/__init__.py
from .session.editor import EditorSession
from .borders.processor import AutoBorderProcessor
from .brushes.manager import BrushManager
```

---

## 📊 Métricas de Qualidade

### Antes

| Métrica | Valor |
|---------|-------|
| Maior arquivo | 1290 linhas |
| Arquivos > 500 linhas | 4 |
| Constantes duplicadas | ~30 |
| Profundidade máxima | 3 níveis |

### Depois (Estimado)

| Métrica | Valor |
|---------|-------|
| Maior arquivo | ~350 linhas |
| Arquivos > 500 linhas | 0 |
| Constantes duplicadas | 0 |
| Profundidade máxima | 4 níveis |

---

## 📝 Ordem de Implementação

1. **Fase 1**: Criar `core/constants/` e mover constantes
2. **Fase 2**: Criar `core/exceptions/` e consolidar exceções
3. **Fase 3**: Reorganizar `core/io/` em subpastas
4. **Fase 4**: Reorganizar `logic_layer/` em subpastas
5. **Fase 5**: Reorganizar `vis_layer/` em subpastas
6. **Fase 6**: Atualizar todos os imports
7. **Fase 7**: Validar testes e corrigir imports quebrados

---

## ✅ Critérios de Aceitação

- [ ] Nenhum arquivo com mais de 400 linhas
- [ ] Zero constantes duplicadas
- [ ] Todos os testes passando
- [ ] Imports públicos mantidos em `__init__.py`
- [ ] Documentação atualizada

---

## 🚀 Próximos Passos

Confirme se deseja que eu implemente esta reorganização. Posso:

1. **Implementar completo**: Todas as fases de uma vez
2. **Implementar incremental**: Uma fase por vez com validação
3. **Ajustar proposta**: Modificar baseado em feedback

Aguardo sua confirmação para prosseguir.
