# Estratégia de Migração Estrutural: Strangler Fig Pattern
## py_rme_canary - Transição Ideal ↔ Realidade

---

## 🎯 **Objetivo**

Migrar gradualmente da estrutura atual para a estrutura ideal do `PROJECT_STRUCTURE.md` **sem quebrar código existente**.

---

## 📋 **Princípios de Migração**

### 1. **Coexistência Temporária**
```python
# Estrutura durante migração (ambos coexistem)
py_rme_canary/
├── core/
│   ├── data/
│   │   └── gamemap.py          # ✅ Novo (migrado)
│   └── gamemap.py              # ⚠️ Deprecated (alias)
│
├── logic_layer/
│   └── brushes/
│       └── ground_brush.py     # ✅ Novo
│
└── brushes.py                  # ⚠️ Deprecated (re-export)
```

### 2. **Deprecation Warnings**
```python
# brushes.py (arquivo antigo)
import warnings
from logic_layer.brushes.ground_brush import GroundBrush

warnings.warn(
    "Importing from 'brushes.py' is deprecated. "
    "Use 'from logic_layer.brushes import GroundBrush' instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['GroundBrush']
```

### 3. **Automated Import Rewriting**
```python
# tools/migrate_imports.py
import libcst as cst

class ImportRewriter(cst.CSTTransformer):
    """Reescreve imports antigos para nova estrutura"""

    def leave_ImportFrom(self, original: cst.ImportFrom, updated: cst.ImportFrom):
        # brushes.py → logic_layer.brushes.ground_brush
        if original.module and original.module.value == "brushes":
            return updated.with_changes(
                module=cst.Attribute(
                    value=cst.Attribute(
                        value=cst.Name("logic_layer"),
                        attr=cst.Name("brushes")
                    ),
                    attr=cst.Name("ground_brush")
                )
            )
        return updated
```

---

## 🗺️ **Roadmap de Migração (6 Sprints)**

### **Sprint 1: Core Data Models** (Semana 1-2)
**Objetivo:** Migrar modelos de dados para `core/data/`

**Arquivos a Migrar:**
```bash
# Origem → Destino
gamemap.py              → core/data/gamemap.py
tile.py                 → core/data/tile.py
item.py                 → core/data/item.py
houses.py               → core/data/houses.py
```

**Checklist:**
- [ ] Copiar arquivos para nova estrutura
- [ ] Adicionar deprecation warnings em arquivos antigos
- [ ] Atualizar imports em testes
- [ ] Rodar `pytest` - garantir 100% pass
- [ ] Adicionar alias `from core.data.gamemap import GameMap as GameMap` no __init__.py raiz

**Comando Automatizado:**
```bash
# Migrar + reescrever imports automaticamente
python tools/migrate_imports.py --target core/data --deprecated-path ./
pytest --tb=short  # Validar sem regressões
```

---

### **Sprint 2: I/O Reorganization** (Semana 3-4)
**Objetivo:** Separar OTBM/XML parsers em submódulos

**Estrutura Nova:**
```
core/io/
├── otbm/
│   ├── loader.py      # OTBMLoader
│   ├── saver.py       # OTBMSaver
│   └── streaming.py   # Byte streaming
└── xml/
    ├── houses_xml.py
    └── spawns_xml.py
```

**Refactoring Crítico:**
```python
# ANTES (tudo em otbm_loader.py, 1500 LOC)
class OTBMLoader:
    def load(self): ...
    def _parse_header(self): ...
    def _parse_tile(self): ...
    def _parse_item(self): ...
    # ... 50 métodos privados

# DEPOIS (separado em módulos)
# core/io/otbm/loader.py (300 LOC)
class OTBMLoader:
    def load(self):
        header = HeaderParser().parse(stream)
        tiles = TileParser().parse(stream, header)
        return GameMap(header, tiles)

# core/io/otbm/header_parser.py (150 LOC)
class HeaderParser:
    def parse(self, stream: ByteStream) -> OTBMHeader: ...

# core/io/otbm/tile_parser.py (200 LOC)
class TileParser:
    def parse(self, stream: ByteStream, header: OTBMHeader) -> list[Tile]: ...
```

**Métricas de Sucesso:**
- ✅ Complexidade ciclomática < 10 por função
- ✅ Cada arquivo < 300 LOC
- ✅ Zero dependências circulares (verificar com `pydeps`)

---

### **Sprint 3: Logic Layer Brushes** (Semana 5-6)
**Objetivo:** Criar estrutura `logic_layer/brushes/`

**Hierarquia de Brushes:**
```python
# logic_layer/brushes/base_brush.py
from abc import ABC, abstractmethod
from typing import Protocol

class BrushProtocol(Protocol):
    """Interface para dependency injection"""
    def apply(self, map: GameMap, pos: Position) -> list[TileDelta]: ...

class BaseBrush(ABC):
    """Classe base com comportamento compartilhado"""

    @abstractmethod
    def apply(self, map: GameMap, pos: Position) -> list[TileDelta]:
        """Aplicar brush - deve ser implementado"""
        ...

    def _create_delta(self, pos: Position, old: Tile, new: Tile) -> TileDelta:
        """Helper compartilhado por todos os brushes"""
        return TileDelta(position=pos, before=old.serialize(), after=new.serialize())
```

**Implementação Exemplo - Door Brush:**
```python
# logic_layer/brushes/door_brush.py
from dataclasses import dataclass
from .base_brush import BaseBrush

@dataclass(frozen=True, slots=True)
class DoorBrush(BaseBrush):
    """Smart door placement with orientation detection"""

    door_id: int
    auto_orient: bool = True

    def apply(self, map: GameMap, pos: Position) -> list[TileDelta]:
        tile = map.get_or_create_tile(pos)

        # Detectar orientação baseado em paredes vizinhas
        orientation = self._detect_orientation(map, pos) if self.auto_orient else 'N'

        # Criar item de porta com rotação correta
        door_item = Item(
            id=self.door_id,
            attributes={'rotation': orientation}
        )

        old_tile = tile.copy()
        tile.add_item(door_item)

        return [self._create_delta(pos, old_tile, tile)]

    def _detect_orientation(self, map: GameMap, pos: Position) -> str:
        """Detecta orientação baseado em vizinhos"""
        # Norte/Sul tem paredes → porta horizontal (E/W)
        has_north = map.has_wall(pos.north())
        has_south = map.has_wall(pos.south())

        if has_north or has_south:
            return 'E'  # Horizontal

        return 'N'  # Vertical
```

**Testes TDD (escrever ANTES da implementação):**
```python
# tests/unit/logic_layer/brushes/test_door_brush.py
def test_door_orientation_with_walls():
    """Door should be horizontal when walls in N/S"""
    map = MockGameMap()
    map.set_tile(0, -1, 0, Tile(items=[wall_item]))  # North wall

    brush = DoorBrush(door_id=1234, auto_orient=True)
    deltas = brush.apply(map, Position(0, 0, 0))

    door = map.get_tile(0, 0, 0).items[0]
    assert door.attributes['rotation'] == 'E'  # Horizontal

def test_door_orientation_without_walls():
    """Door should be vertical when no adjacent walls"""
    map = MockGameMap()  # Empty map

    brush = DoorBrush(door_id=1234, auto_orient=True)
    deltas = brush.apply(map, Position(0, 0, 0))

    door = map.get_tile(0, 0, 0).items[0]
    assert door.attributes['rotation'] == 'N'  # Vertical
```

---

### **Sprint 4: UI Docks Consolidation** (Semana 7-8)
**Objetivo:** Organizar docks em `vis_layer/ui/docks/`

**Problema Atual:**
```python
# Provável estado atual (espalhado)
palette.py              # Raiz do projeto?
minimap_widget.py       # Em vis_layer/?
properties_panel.py     # Em algum lugar?
```

**Estrutura Consolidada:**
```
vis_layer/ui/docks/
├── __init__.py
├── palette.py          # Brush palette
├── minimap.py          # Minimap overview
├── properties.py       # Tile/Item inspector
├── history.py          # Undo/Redo visual
└── base_dock.py        # Shared dock behavior
```

**Base Dock (DRY principle):**
```python
# vis_layer/ui/docks/base_dock.py
from PyQt6.QtWidgets import QDockWidget

class BaseDock(QDockWidget):
    """Base class for all dock widgets"""

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setObjectName(f"dock_{title.lower().replace(' ', '_')}")
        self._setup_ui()

    @abstractmethod
    def _setup_ui(self):
        """Setup dock UI - must be implemented"""
        ...

    def save_state(self) -> dict:
        """Save dock state for session persistence"""
        return {
            'visible': self.isVisible(),
            'floating': self.isFloating(),
            'geometry': self.geometry().getRect()
        }

    def restore_state(self, state: dict):
        """Restore dock state from session"""
        self.setVisible(state.get('visible', True))
        self.setFloating(state.get('floating', False))
        # ... restore geometry
```

**Palette Refatorado:**
```python
# vis_layer/ui/docks/palette.py
from .base_dock import BaseDock
from logic_layer.brush_definitions import BRUSHES

class PaletteDock(BaseDock):
    """Brush selection palette"""

    def __init__(self, parent=None):
        super().__init__("Palette", parent)
        self._brushes = BRUSHES  # Importa do logic_layer (correto!)

    def _setup_ui(self):
        # QListWidget com brush icons
        self.brush_list = QListWidget()

        for brush_name, brush in self._brushes.items():
            item = QListWidgetItem(brush.name)
            item.setData(Qt.UserRole, brush)
            self.brush_list.addItem(item)

        layout = QVBoxLayout()
        layout.addWidget(self.brush_list)

        container = QWidget()
        container.setLayout(layout)
        self.setWidget(container)
```

---

### **Sprint 5: Renderer Abstraction** (Semana 9-10)
**Objetivo:** Separar OpenGL/QPainter em módulos independentes

**Arquitetura de Renderização:**
```python
# vis_layer/renderer/render_model.py (UI-agnostic!)
@dataclass(frozen=True)
class DrawCommand:
    """Qt-free draw command"""
    sprite_id: int
    position: tuple[int, int]
    layer: int
    opacity: float = 1.0

class RenderModel:
    """Converts GameMap to draw commands (no Qt dependency!)"""

    def generate_commands(
        self,
        map: GameMap,
        viewport: ViewportState
    ) -> list[DrawCommand]:
        """Generate draw commands for visible tiles"""
        commands = []

        for tile in map.get_tiles_in_bounds(viewport.bounds):
            for item in tile.items:
                sprite_id = self._get_sprite_for_item(item)
                screen_pos = viewport.world_to_screen(tile.position)

                commands.append(DrawCommand(
                    sprite_id=sprite_id,
                    position=screen_pos,
                    layer=item.layer,
                    opacity=1.0
                ))

        return sorted(commands, key=lambda c: c.layer)

# vis_layer/renderer/opengl_canvas.py (Qt-dependent)
class OpenGLCanvas(QOpenGLWidget):
    """OpenGL renderer using draw commands"""

    def __init__(self, render_model: RenderModel):
        super().__init__()
        self._render_model = render_model
        self._sprite_cache: dict[int, GLuint] = {}

    def paintGL(self):
        commands = self._render_model.generate_commands(
            self.map,
            self.viewport
        )

        for cmd in commands:
            texture = self._sprite_cache.get(cmd.sprite_id)
            if texture:
                self._draw_sprite(texture, cmd.position, cmd.opacity)
```

**Vantagens desta Arquitetura:**
1. ✅ **Testável**: `RenderModel` pode ser testado sem Qt
2. ✅ **Portável**: Trocar OpenGL → Vulkan = só mudar canvas
3. ✅ **Reusável**: Mesmos commands para minimap/export PNG

---

### **Sprint 6: Cleanup & Documentation** (Semana 11-12)
**Objetivo:** Remover código deprecated e atualizar docs

**Arquivos a Remover:**
```bash
# Lista de deprecated (após migração completa)
brushes.py                  # → logic_layer/brushes/
auto_border.py              # → logic_layer/borders/
data_layer/                 # → core/
tk_app.py                   # Legacy Tkinter
tempCodeRunnerFile.py       # Debug temporário
```

**Script de Limpeza Automatizado:**
```bash
#!/bin/bash
# tools/cleanup_deprecated.sh

echo "🧹 Removendo arquivos deprecated..."

# Verificar se ainda há imports para arquivos antigos
echo "🔍 Verificando dependências..."
grep -r "from brushes import" py_rme_canary/ && {
    echo "❌ Ainda há imports para brushes.py! Abortar."
    exit 1
}

# Se passou, remover
rm -v brushes.py auto_border.py
rm -rv data_layer/
rm -v tempCodeRunnerFile.py

echo "✅ Cleanup concluído!"
```

**Atualizar Documentação:**
```markdown
# PROJECT_STRUCTURE.md (adicionar seção)

## 📜 Migration History

### v2.1.0 (2026-01-18) - Structure Overhaul
**Breaking Changes:**
- `brushes.py` → `logic_layer/brushes/` (use deprecation warnings até v3.0)
- `auto_border.py` → `logic_layer/borders/`
- `data_layer/` → `core/` (removido completamente)

**Migration Guide:**
```python
# ANTES (v2.0)
from brushes import GroundBrush

# DEPOIS (v2.1+)
from logic_layer.brushes import GroundBrush
```
```

---

## 🎯 **Métricas de Sucesso**

### **KPIs por Sprint**

| Sprint | Métrica | Target | Ferramenta |
|--------|---------|--------|------------|
| 1 | Imports migrados | 100% | `grep -r "from gamemap"` |
| 2 | CC médio OTBM | < 8 | `radon cc core/io/` |
| 3 | Brushes implementados | 5/15 | Manual count |
| 4 | Docks consolidados | 6/6 | Manual count |
| 5 | Render tests pass | 95%+ | `pytest vis_layer/renderer/` |
| 6 | Deprecated files | 0 | `find . -name "*deprecated*"` |

### **Quality Gates (Cada Sprint)**
```bash
# Rodar ANTES de merge
black . && isort .
mypy . --strict
pytest --cov=. --cov-fail-under=90
pydeps py_rme_canary --show-cycles  # Zero cycles!
```

---

## 🚨 **Riscos & Mitigação**

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Imports quebrados** | Alta | Crítico | Deprecation warnings + automated rewriting |
| **Performance regression** | Média | Alto | Benchmarks antes/depois de cada sprint |
| **Circular dependencies** | Baixa | Médio | `pydeps` no CI pipeline |
| **Testes flaky** | Média | Baixo | Aumentar timeouts em UI tests |

---

## ✅ **Próximos Passos Imediatos**

### **Esta Semana (Sprint 0 - Preparação)**
```bash
# 1. Criar branch de migração
git checkout -b feature/structure-migration

# 2. Gerar relatório de estado atual
python tools/structure_audit.py > reports/pre_migration_state.json

# 3. Criar ferramentas de migração
mkdir -p tools/migration/
touch tools/migration/import_rewriter.py
touch tools/migration/deprecation_injector.py

# 4. Definir ordem de migração
# Priorizar módulos com menos dependentes (leaf nodes)
pydeps py_rme_canary --show-deps > reports/dependency_graph.txt
```

### **Próxima Semana (Sprint 1 - Início)**
1. ✅ Migrar `gamemap.py` → `core/data/gamemap.py`
2. ✅ Adicionar deprecation warning em `gamemap.py` antigo
3. ✅ Reescrever imports em `tests/`
4. ✅ Rodar `pytest` - garantir 100% pass
5. 📊 Benchmark load time antes/depois

---

## 📊 **Dashboard de Progresso**

```yaml
# .migration_status.yaml (atualizar após cada sprint)
migration_progress:
  total_files: 150
  migrated_files: 0
  deprecated_files: 0
  removed_files: 0

sprints:
  sprint_1:
    status: not_started
    target_files: ["gamemap.py", "tile.py", "item.py"]

  sprint_2:
    status: not_started
    target_files: ["otbm_loader.py", "otbm_saver.py"]

  # ... outros sprints
```

---

**Versão:** 1.0
**Última Atualização:** 2026-01-18
**Autor:** Architecture Team
**Status:** Proposta Aguardando Aprovação
