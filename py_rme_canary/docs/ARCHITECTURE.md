# Architecture Guide - py_rme_canary

**Quick Reference** for understanding and importing from each layer.

---

## 🏗️ Layer Overview

```
py_rme_canary/
├── core/           ← Pure data + I/O (no UI dependencies)
├── logic_layer/    ← Editing rules (no UI dependencies)
├── vis_layer/      ← UI implementation (PyQt6 primary)
└── tools/          ← Utility scripts
```

---

## 📦 What to Import From Each Layer

### 🔷 **core/** - Safe for Everyone

Use when you need:
- **Data models** (GameMap, Tile, Item)
- **I/O operations** (load/save OTBM)
- **Database** (ItemsXML, ItemsOTB, IdMapper)
- **Configuration** (ProjectDefinitions, ConfigurationManager)

```python
# ✅ CORRECT: These are all safe, no UI dependencies
from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.io.otbm_loader import OTBMLoader
from py_rme_canary.core.database.items_xml import ItemsXML
```

**✅ Stable, tested, recommended for tests and tools**

---

### 🟢 **logic_layer/** - For Controllers & Tests

Use when you need:
- **EditorSession** (stateful controller for map editing)
- **Auto-border** (automatic border processing)
- **Undo/Redo** (HistoryManager, PaintAction)
- **Brush definitions** (BrushManager)

```python
# ✅ CORRECT: These have no UI dependencies
from py_rme_canary.logic_layer.editor_session import EditorSession
from py_rme_canary.logic_layer.auto_border import AutoBorderProcessor
from py_rme_canary.logic_layer.brush_definitions import BrushManager

# ❌ AVOID: These are deprecated
from py_rme_canary.logic_layer.brushes import Brush  # Use BrushManager instead
```

**✅ Stable, fully testable (no Qt/Tk required)**

---

### 🟠 **vis_layer/** - For UI Only

Main entry point:

```python
# ✅ RECOMMENDED: The main PyQt6 editor
from py_rme_canary.vis_layer.qt_app import QtMapEditor

# 🟡 EXPERIMENTAL (don't use for new code):
from py_rme_canary.vis_layer.tk_app import TkMapEditor  # Tkinter, unmaintained
```

Internal UI modules (used by qt_app.py):

```python
# ✅ Use only if extending qt_app.py
from py_rme_canary.vis_layer.ui.map_canvas import MapCanvasWidget
from py_rme_canary.vis_layer.ui.palette import PaletteManager
from py_rme_canary.vis_layer.ui.indicators import IndicatorService
```

**⚠️ Don't import from here in business logic; keep UI isolated**

---



## 📚 Common Patterns

### Loading a Map

```python
from py_rme_canary.core.io.otbm_loader import OTBMLoader
from py_rme_canary.core.database.items_xml import ItemsXML

# Load items database
items_db = ItemsXML.from_file("data/items/items.xml")

# Load map
loader = OTBMLoader(items_db=items_db)
game_map = loader.load("path/to/map.otbm")

# Access tiles
tile = game_map.get_tile(100, 100, 7)
if tile and tile.ground:
    print(f"Ground item: {tile.ground.id}")
```

### Creating an Editor Session

```python
from py_rme_canary.logic_layer.editor_session import EditorSession
from py_rme_canary.logic_layer.brush_definitions import BrushManager

# Create brush manager from JSON
brush_mgr = BrushManager.from_json_file("data/brushes.json")

# Create session (maps are edited through this)
session = EditorSession(game_map, brush_mgr)

# Select a brush and paint
session.set_selected_brush(4405)  # Mountain terrain

# Undo/Redo
session.history.undo(game_map)
session.history.redo(game_map)
```

### Launching the UI

```python
from PyQt6.QtWidgets import QApplication
from py_rme_canary.vis_layer.qt_app import QtMapEditor

app = QApplication([])
editor = QtMapEditor()
editor.show()
app.exec()
```

---

## 🚫 Anti-Patterns (Don't Do This)

```python
# ❌ DON'T: Import UI code in business logic
def apply_auto_border(game_map):
    from py_rme_canary.vis_layer.qt_app import QtMapEditor  # WRONG!
    editor = QtMapEditor()  # This needs Qt!

# ✅ DO: Keep logic separate, let UI call the logic
def apply_auto_border(game_map, brush_mgr):
    from py_rme_canary.logic_layer.auto_border import AutoBorderProcessor
    processor = AutoBorderProcessor(game_map, brush_mgr)
    return processor  # Return result, don't show UI
```

```python
# ✅ DO: Use core/
from py_rme_canary.core.io.otbm_loader import OTBMLoader
```

```python
# ❌ DON'T: Create circular dependencies
# logic_layer → core ✅
# vis_layer → logic_layer, core ✅
# core → logic_layer ❌ (would be circular!)
```

---

## 📈 Dependency Graph

```
┌─ core/          (no external deps except stdlib)
│  ├─ data/       (GameMap, Tile, Item, Position)
│  ├─ io/         (OTBM loader/saver, detection)
│  ├─ database/   (Items parsing, ID mapping)
│  ├─ config/     (Project, Configuration)
│  └─ assets/     (Sprite catalogs)
│
├─ logic_layer/   (depends on core/)
│  ├─ editor_session.py
│  ├─ auto_border.py
│  ├─ transactional_brush.py
│  └─ brush_definitions.py
│
└─ vis_layer/     (depends on core/ + logic_layer/)
   ├─ qt_app.py   (PyQt6, main UI)
   ├─ ui/         (modular widgets)
   └─ (deprecated: tk_app.py, PySide6 modules)
```

**Rule:** Arrow points down only. No backwards dependencies.

---

## 🧪 Testing Guidelines

```python
# For unit tests: Use only core/ + logic_layer/
import pytest
from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.logic_layer.editor_session import EditorSession
from py_rme_canary.logic_layer.brush_definitions import BrushManager

def test_auto_border():
    gm = GameMap(header=MapHeader(width=256, height=256, otbm_version=2))
    mgr = BrushManager.from_json_file("data/brushes.json")
    session = EditorSession(gm, mgr)
    # ... test without Qt/Tk
```

```python
# For integration tests: Use core/ + logic_layer/ + vis_layer/
def test_editor_loads_map():
    from py_rme_canary.core.io.otbm_loader import OTBMLoader
    from py_rme_canary.vis_layer.qt_app import QtMapEditor
    
    loader = OTBMLoader()
    game_map = loader.load("test_map.otbm")
    
    # Create editor (requires Qt)
    editor = QtMapEditor()
    # ... test with UI
```

---

## 📌 Quick Checklist

- [ ] Does your code need Qt/Tk? → Use `vis_layer/qt_app.py`
- [ ] Does your code need map editing logic? → Use `logic_layer/`
- [ ] Does your code just read/process data? → Use `core/`
- [ ] Are you importing from `data_layer/`? → Change to `core/`
- [ ] Does `core/` import from `logic_layer/`? → **BUG!** Fix it.
- [ ] Are your edits working? → Run smoke test in `qt_app.py`

---

**Last Updated:** 2026-01-05  
**Maintained By:** Code Quality Audit
