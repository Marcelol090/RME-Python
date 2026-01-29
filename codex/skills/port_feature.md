---
name: Port Legacy Feature
description: A guided skill to transport a feature from RME C++ to py_rme_canary.
---

# Skill: Port Legacy Feature

## Context
You are tasked with porting a specific feature (e.g., "Magic Wall Logic", "Spawn Brush") from the legacy C++ codebase to Python.

## Procedure

### 1. 🕵️ Investigation (The Dig)
*   **Search C++:** Use `grep_search` to find the feature name in `RME/source`.
    *   *Target:* Look for `.cpp` files with logic and `.h` files with data structures.
*   **Identify Logic:** Read the `draw`, `undraw`, or `action` methods.
*   **Identify Dependencies:** Does it need `Item`, `Map`, `Client`, or `QTree`?

### 2. 📝 Design & Interface
*   **Check Python Data:** Does `py_rme_canary/core` already have the necessary data structures?
*   **Plan the Class:** Define the Python class signature in a scratchpad or plan.
    *   *Goal:* Match the C++ method signatures where possible for parity (e.g., `setTile(Position, Item)`).

### 3. 🧪 Test-Driven Development (The Guard)
*   **Create Test:** Create `tests/unit/test_[feature].py`.
*   **Mock Context:** Use `MagicMock` for `GameMap` or `EditorSession` if they aren't needed for the logic itself.
*   **Assert Behavior:** Write an assertion that mimics the C++ logic you found in Step 1.

### 4. 🚀 Implementation
*   **Write Code:** Implement the class in `py_rme_canary/logic_layer/`.
*   **Strict Types:** Use `mypy` compatible type hints (`def foo(x: int) -> None:`).
*   **Parity Check:** Ensure the logic flow (if/else branches) matches the C++ source.

### 5. 🔗 Integration (Visuals)
*   **Bind UI:** If this feature has a widget, connect it in `vis_layer`.
*   **Execute:** Run the test. Fix. Repeat.

## Definition of Done
1.  [ ] C++ Source identified and read.
2.  [ ] Python implementation exists in `logic_layer`.
3.  [ ] Unit tests pass.
4.  [ ] `IMPLEMENTATION_STATUS.md` updated.
