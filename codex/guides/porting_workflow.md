# Porting Workflow: C++ to Python

This guide details the standard process for porting a feature from legacy `RME` (C++) to `py_rme_canary` (Python).

## Phase 1: Analysis (Legacy)
1.  **Locate Source:** Find the relevant `.cpp` file in `RME/source/`.
    *   *Example:* `RME/source/brushes/doodad_brush.cpp`.
2.  **Understand Logic:** Identify the core algorithm (e.g., `draw()`, `undraw()`) & data structures.
3.  **Identify Dependencies:** What other systems does it touch? (e.g., `Item`, `Map`, `Spawn`).

## Phase 2: Design (Python)
1.  **Map to Architecture:**
    *   Data structures -> `core/` or `logic_layer/brush_definitions.py`.
    *   Logic/Algorithms -> `logic_layer/`.
    *   UI/Dialogs -> `vis_layer/ui/`.
2.  **Define Interface:** Create the Python class structure/dataclass matching the C++ intent.

## Phase 3: Implementation
1.  **Write Tests First (TDD):** Create a test in `tests/unit/` describing the expected C++ behavior.
2.  **Implement Logic:** Write the Python code in `logic_layer`. Use `mypy` strict types.
3.  **Verify Parity:** Run the test to ensure it matches legacy behavior.

## Phase 4: UI Integration
1.  **Create Widget:** Implement the UI in `vis_layer/ui` using PyQt6.
2.  **Bind Logic:** Connect UI signals to `logic_layer` methods.
3.  **Smoke Test:** Verify manually or with `pytest-qt` that the UI triggers the logic correctly.
