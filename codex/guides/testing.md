# Testing Standards & Guide

## Philosophy
We prioritize **testability**. Logic is decoupled from UI so it can be tested without a running GUI (headless).

## Tools
*   **pytest**: The runner.
*   **pytest-qt**: For UI interaction tests.
*   **mypy**: Static type checking.

## 1. Unit Testing (`tests/unit`)
Target: `core/`, `logic_layer/`.
*   **Do:** Mock `EditorSession` or `GameMap` if needed.
*   **Do:** Test edge cases (bounds, invalid inputs).
*   **Don't:** Import PyQt6 widgets here.

Example:
```python
def test_carpet_brush_logic():
    brush = CarpetBrushSpec(...)
    map = GameMap(width=10, height=10)
    # Apply brush logic
    assert map.get_tile(5, 5).item.id == EXPECTED_ID
```

## 2. UI Testing (`tests/ui`)
Target: `vis_layer/`.
*   **Usage:** Use the `qtbot` fixture to interact with widgets.
*   **Patterns:**
    *   `qtbot.addWidget(widget)`
    *   `qtbot.mouseClick(widget.button, Qt.LeftButton)`
    *   `assert widget.label.text() == "Result"`

## 3. Running Tests
*   Run all: `pytest`
*   Run specific: `pytest tests/unit/test_brushes.py`
*   With coverage: `pytest --cov=py_rme_canary`
