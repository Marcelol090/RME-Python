# Code Quality Checklist - py_rme_canary

Use this checklist **before committing** to maintain professional standards.

---

## ✅ Before Each Commit

- [ ] **No circular imports**
  ```bash
  python -c "import py_rme_canary.vis_layer.qt_app; print('OK')"
  ```
  
- [ ] **All tests pass**
  ```bash
  # Run from repo root
  python -m pytest
  ```

- [ ] **No import from data_layer/**
  ```bash
  grep -r "from py_rme_canary.data_layer" --include="*.py" | grep -v "test"
  # Should be empty (except tools/read_otbm_header.py)
  ```

- [ ] **Lint (optional)**
  ```bash
  # Optional (does not block the default workflow)
  python -m ruff check py_rme_canary/core py_rme_canary/logic_layer tests
  ```

- [ ] **Type-check (optional)**
  ```bash
  # Optional (incremental adoption)
  python -m mypy py_rme_canary/core py_rme_canary/logic_layer
  ```

- [ ] **Type hints on public functions**
  ```python
  # ✅ CORRECT
  def load_map(path: str) -> GameMap:
  
  # ❌ WRONG (no hints)
  def load_map(path):
  ```

- [ ] **Docstrings on public classes/modules**
  ```python
  # ✅ CORRECT
  """Module docstring explaining purpose."""
  
  class MyClass:
      """Class docstring."""
      def method(self):
          """Method docstring."""
  ```

---

## 🏗️ Architectural Rules

### Dependencies Flow (One Direction Only)

```
✅ Correct:  core/ ← logic_layer/ ← vis_layer/
❌ Wrong:    core/ → logic_layer/ (core depends on logic)
```

Check:
```bash
# core/ should NOT import from logic_layer/ or vis_layer/
grep -r "from py_rme_canary.logic_layer\|from py_rme_canary.vis_layer" \
  py_rme_canary/core/ --include="*.py"
# Should be empty
```

### No Qt/Tk in core/ or logic_layer/

```python
# ❌ WRONG - core/ should not have Qt
from PyQt6.QtWidgets import QWidget  # In core/ file

# ✅ CORRECT - only in vis_layer/
from PyQt6.QtWidgets import QWidget  # In vis_layer/ file
```

Check:
```bash
grep -r "from PyQt6\|from Tk\|import QtCore\|import tkinter" \
  py_rme_canary/core/ py_rme_canary/logic_layer/ --include="*.py"
# Should be empty
```

---

## 📦 Module Structure

### Each module should have clear responsibility

| Module | Should Have | Should NOT Have |
|--------|------------|-----------------|
| `core/data/` | Dataclasses, frozen objects | Business logic, I/O |
| `core/io/` | File operations, parsing | UI, editing logic |
| `logic_layer/` | Editing rules, algorithms | UI, I/O, core models |
| `vis_layer/` | UI widgets, rendering | Business logic, data models |

---

## 🧹 Code Cleanliness

### Naming Conventions

```python
# ✅ Classes: CamelCase
class MapCanvasWidget:
    pass

# ✅ Functions/vars: snake_case
def get_tile(x, y, z):
    pass

# ✅ Constants: SCREAMING_SNAKE_CASE
OTBM_MAGIC = b"OTBM"

# ✅ Private: _leading_underscore
def _internal_helper():
    pass
```

Check:
```bash
# Look for inconsistencies
grep -r "class [a-z]" py_rme_canary/ --include="*.py"  # Should find few
grep -r "def [A-Z]" py_rme_canary/ --include="*.py"    # Should find few
```

### No Dead Code

- [ ] No functions with only `pass` or `...`
- [ ] No files with only docstring (unless clearly marked as planned)
- [ ] No commented-out code (use git history instead)

```bash
# Find stub functions
grep -r "def.*:\s*$" py_rme_canary/ --include="*.py" | grep -A1 "def " | grep -B1 "pass\|..."
```

### No Magic Numbers

```python
# ❌ WRONG
if viewport.z > 15:
    print("Too deep")

# ✅ CORRECT
MAX_TIBIA_DEPTH = 16
if viewport.z >= MAX_TIBIA_DEPTH:
    print(f"Too deep (max={MAX_TIBIA_DEPTH})")
```

---

## 📚 Documentation

### Every public class/function needs docs

```python
# ✅ CORRECT
def set_tile(self, tile: Tile) -> None:
    """Store a tile at its (x, y, z) position.
    
    Args:
        tile: Tile object with x, y, z coordinates set.
        
    Returns:
        None (modifies internal state)
        
    Raises:
        ValueError: If tile has invalid coordinates.
    """
    self.tiles[(int(tile.x), int(tile.y), int(tile.z))] = tile

# ❌ WRONG (no docs)
def set_tile(self, tile):
    self.tiles[(tile.x, tile.y, tile.z)] = tile
```

### Module-level docstring required

```python
# ✅ CORRECT (at top of file)
"""Tile representation with ground + items."""

from dataclasses import dataclass

# ❌ WRONG (missing module docstring)
from dataclasses import dataclass
```

---

## 🧪 Testing

### Test File Naming

```
✅ CORRECT patterns:
  - tests/test_*.py
  - tests/**/test_*.py

❌ WRONG patterns:
  - _minimal_test.py (unclear / nonstandard for pytest)
```

Tip:
```bash
python -m pytest -q
```

### Smoke Test Before Release

Run the offscreen Qt test:
```bash
export QT_QPA_PLATFORM=offscreen
python py_rme_canary/vis_layer/qt_app.py  # If it has __main__

# OR create a smoke test:
python << 'PY'
from PyQt6.QtWidgets import QApplication
from py_rme_canary.vis_layer.qt_app import QtMapEditor

app = QApplication([])
win = QtMapEditor()
win.close()
print("✅ Smoke test passed")
PY
```

---

## 🔍 Code Review Checklist (For Reviewers)

- [ ] No circular dependencies
- [ ] No Qt imports outside vis_layer/
- [ ] All public APIs have type hints
- [ ] No dead code or stubs
- [ ] Follows naming conventions
- [ ] No magic numbers (use constants)
- [ ] Has docstrings
- [ ] Tests pass
- [ ] No uncommitted debug code

---

## 📈 Metrics to Track

### Import Hierarchy
```bash
# Should show: core → logic_layer → vis_layer (only forward)
python << 'PY'
import ast
import os

files = {}
for root, dirs, filenames in os.walk("py_rme_canary"):
    for f in filenames:
        if f.endswith(".py") and not f.startswith("_"):
            path = os.path.join(root, f)
            with open(path) as fh:
                try:
                    tree = ast.parse(fh.read())
                    imports = [node for node in ast.walk(tree) 
                              if isinstance(node, (ast.Import, ast.ImportFrom))]
                    files[path] = len(imports)
                except:
                    pass

print(f"Total importable modules: {len(files)}")
print(f"Avg imports per file: {sum(files.values()) / len(files) if files else 0:.1f}")
PY
```

### Code Size per Layer
```bash
wc -l py_rme_canary/{core,logic_layer,vis_layer}/**/*.py | tail -1
```

### Test Coverage
```bash
# If using pytest-cov:
python -m pytest --cov=py_rme_canary py_rme_canary/
```

---

## 🚀 Before Release

- [ ] All critical TODO items resolved
- [ ] No temporary files left
- [ ] IMPLEMENTATION_TODO.md updated
- [ ] ARCHITECTURE.md reflects current structure
- [ ] data_layer/ either cleaned or marked deprecated
- [ ] mirroring.py implemented or moved to _planned/
- [ ] brushes.py removed or refactored
- [ ] All smoke tests pass
- [ ] Changelog updated (if applicable)

---

## 🔧 Useful Commands

```bash
# Find all stubs
grep -r "pass\s*$\|NotImplementedError\|TODO\|FIXME\|XXX" py_rme_canary/ --include="*.py"

# Find large files (consider splitting if > 1000 lines)
find py_rme_canary -name "*.py" -type f -exec wc -l {} \; | sort -rn | head -10

# Check import depth
python -c "import py_rme_canary; print('✅ Imports work')"

# Validate syntax
python -m py_compile py_rme_canary/vis_layer/qt_app.py

# Count lines by layer
for d in core logic_layer vis_layer data_layer; do
  echo "$d: $(find py_rme_canary/$d -name '*.py' -exec wc -l {} \; | awk '{s+=$1} END {print s}') lines"
done
```

---

**Last Updated:** 2026-01-05  
**Compliance:** Maintain A- (88+/100) professional standard
