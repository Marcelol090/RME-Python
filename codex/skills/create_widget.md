---
name: Create PyQt6 Widget
description: A guided skill to create a UI component in `vis_layer` that strictly respects MVC separation.
---

# Skill: Create PyQt6 Widget

## Context
You need to create a new UI element (Dialog, Panel, or Widget) for RME.

## Procedure

### 1. 🏗️ Architecture Design
*   **Identify Logic Controller:** Which class in `logic_layer` will handle the data? (e.g., `BrushController`, `MapAction`).
*   **Define Signals:** What user actions trigger updates? (e.g., `clicked`, `valueChanged`).
*   **Define Slots:** What logical updates change the UI? (e.g., `on_selection_changed`).

### 2. 🎨 Layout Strategy
*   **Grid vs Form:** Use `QGridLayout` for complex forms, `QVBoxLayout` for stacks.
*   **Native Widgets:** Prefer standard `QWidget` over custom painting unless necessary (performance).

### 3. 🛡️ The "Dumb Widget" Check
*   *Before writing code, verify:*
    *   [ ] Does this widget calculate anything? (If YES -> Move to Logic).
    *   [ ] Does it import `GameMap` directly? (If YES -> Stop. Use a DTO or Signal).

### 4. 🔨 Implementation
*   **File Location:** `py_rme_canary/vis_layer/ui/`.
*   **Class Structure:**
    ```python
    class MyWidget(QWidget):
        # Signals allow decoupling
        submitted = pyqtSignal(ValidationDTO)
        
        def __init__(self):
            super().__init__()
            self._setup_ui()
            
        def _setup_ui(self):
            # Layouts and Sub-widgets
            pass
    ```

### 5. 🧪 Smoke Test
*   **Interactive:** Run the app and open the widget.
*   **Automated:** Create `tests/ui/test_my_widget.py` using `qtbot`.
    ```python
    def test_widget_emits_signal(qtbot):
        widget = MyWidget()
        qtbot.addWidget(widget)
        with qtbot.waitSignal(widget.submitted):
            qtbot.mouseClick(widget.submit_btn, Qt.LeftButton)
    ```

## Definition of Done
1.  [ ] Widget created in `vis_layer`.
2.  [ ] No business logic imports found in the file.
3.  [ ] Smoke test passes.
