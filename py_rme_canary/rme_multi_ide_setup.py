#!/usr/bin/env python3
"""
py_rme_canary AI Environment Generator
Author: Senior Python Architect & OT Specialist
Target: Antigravity IDE (.agent) & Cursor IDE (.cursor)

Description:
Configura o ambiente para o desenvolvimento do 'py_rme_canary' (Python RME).
Injeta as regras estritas do PRD.md e PROJECT_STRUCTURE.md, definindo 
Workflows Lineares e Reflexivos para cada modelo (Opus, Sonnet, Gemini, GPT-5).
"""

from pathlib import Path
import json
import os

# ==========================================
# DEFINIÇÕES DE CONTEÚDO (Linear & Reflective Logic)
# ==========================================

# ------------------------------------------
# Workflows (.agents/workflows)
# ------------------------------------------

WORKFLOW_OPUS = """# Opus 4.5 Workflow - Architecture & Design Strategy
---
**Role:** Chief Python Architect
**Context:** High-Level Design for `py_rme_canary`
**Objective:** Create robust, scalable architecture adhering to strictly layered protocols (Core > Logic > Vis).

## Linear Reasoning Process

### Phase 1: Contextual Analysis & Deconstruction
1.  **Ingest Requirements:** Read `PRD.md` and specific feature requests.
2.  **Layer Mapping:** Identify which logical components belong to `core/` (Data), `logic_layer/` (Control), and `vis_layer/` (UI).
3.  **Dependency Check:** Verify that the proposed structure violates NO dependency rules (e.g., Core importing Vis).

### Phase 2: Structural Design (Zero Ambiguity)
1.  **Define Interfaces:** Draft Abstract Base Classes (ABCs) or Protocols.
2.  **Data Flow:** Map how data moves from Binary (OTBM) -> Memory -> UI.
3.  **Reflection Point:** *Does this design require a circular import? If yes, halt and redesign using Dependency Injection.*

### Phase 3: Task & Implementation Planning
1.  **Breakdown:** Split the feature into atomic, testable units.
2.  **Sequence:** Order tasks by dependency (Core first, then Logic, then UI).

##  Task List Template
- [ ] **Analysis:** Review Legacy C++ implementation of [Feature].
- [ ] **Design:** Define Data Structures in `core/`.
- [ ] **Design:** Define Logic Controllers in `logic_layer/`.
- [ ] **Design:** Define UI Components in `vis_layer/`.

## Implementation List Template
- [ ] `core/models/[feature].py`: Data dataclasses with `__slots__`.
- [ ] `logic_layer/controllers/[feature]_controller.py`: Business logic.
- [ ] `vis_layer/widgets/[feature]_widget.py`: PyQt6 implementation.
- [ ] `tests/core/test_[feature].py`: Strict unit tests.
"""

WORKFLOW_SONNET = """# Sonnet 4.5 Workflow - Strict Implementation & TDD
---
**Role:** Senior Python Developer
**Context:** Feature Implementation & Refactoring
**Objective:** Write production-grade code with 100% test coverage and NO fallbacks.

## Linear Reasoning Process

### Phase 1: Test-Driven Setup (Strict Mode)
1.  **Mocking:** Create mocks for external dependencies.
2.  **Fail First:** Write a test that asserts exact values (e.g., `assert result == 0xFE`).
    * *Constraint:* **NO** `try/except` blocks that swallow errors during tests.
    * *Constraint:* **NO** fuzzy matching. Exact types and values required.
3.  **Reflection Point:** *Does the test cover edge cases (0, None, MaxInt)?*

### Phase 2: Implementation (Atomic)
1.  **Type Definition:** Define strict types using `typing` (List, Optional, NewType).
2.  **Logic Coding:** Implement the minimum code to pass the strict test.
3.  **Style Enforcement:** Apply Snake_case and Docstrings immediately.

### Phase 3: Integration & Refinement
1.  **Layer Check:** Ensure no UI code leaked into Logic/Core.
2.  **Optimization:** Replace heavy loops with `struct` or `numpy` if dealing with map data.

## Task List Template
- [ ] **Test:** Create strict test case for [Functionality].
- [ ] **Code:** Implement Core data structures.
- [ ] **Code:** Implement Logic methods.
- [ ] **Verify:** Run `mypy --strict` on new files.

## Implementation List Template
- [ ] `tests/unit/test_[module].py`: Coverage > 90%.
- [ ] `src/module.py`: Implementation with Type Hints.
"""

WORKFLOW_GEMINI = """# Gemini 3 Workflow - Deep Research & Prototyping
---
**Role:** Technical Researcher & Prototype Engineer
**Context:** Analyzing Legacy C++ (TFS/RME) and Python Libraries
**Objective:** Provide factual, verified technical paths for implementation.

## Linear Reasoning Process

### Phase 1: Information Retrieval & Verification
1.  **Source Parsing:** Read `legacy_source/` (C++) or Library Docs (PyQt6/NumPy).
2.  **Behavior Extraction:** Trace execution flow in C++ (e.g., `Map::readNode`).
3.  **Reflection Point:** *Is this C++ behavior a bug or a feature? verify against Tibia Client protocols.*

### Phase 2: Prototyping (Fail Fast)
1.  **Scripting:** Write isolated Python scripts to replicate behavior.
2.  **Benchmarking:** Measure performance (Time/Memory).
    * *Constraint:* **NO** estimated metrics. Use `timeit` or `cProfile`.
3.  **Comparison:** Compare Approaches (e.g., `QGraphicsScene` vs `OpenGL`).

### Phase 3: Synthesis
1.  **Recommendation:** Select the best approach based on `PRD.md` constraints (< 3s load time).
2.  **Documentation:** Document the "Why" and "How".

## Task List Template
- [ ] **Research:** Trace [C++ Class/Method].
- [ ] **Benchmark:** Test Option A (e.g., Pure Python).
- [ ] **Benchmark:** Test Option B (e.g., Cython/Struct).
- [ ] **Report:** Summarize findings.

## Implementation List Template
- [ ] `prototypes/bench_[feature].py`: Runnable benchmark script.
- [ ] `docs/technical/[feature]_analysis.md`: Implementation guide.
"""

WORKFLOW_GPT5 = """# GPT-5-2 Workflow - Advanced Optimization & Security
---
**Role:** Systems & Performance Engineer
**Context:** Binary Manipulation, Memory Management, Complex Algorithms
**Objective:** Optimize critical paths and ensure binary perfection.

## Linear Reasoning Process

### Phase 1: Algorithmic Analysis
1.  **Complexity Check:** Calculate Big-O for the proposed Logic.
2.  **Bottleneck Identification:** Predict where Python's GIL or GC will stall.
3.  **Reflection Point:** *Can this be vectorized with NumPy or does it need struct packing?*

### Phase 2: Advanced Implementation
1.  **Memory Layout:** Use `__slots__` and `int`-keyed dicts to reduce RAM.
2.  **Binary Integrity:** Ensure `struct.pack` produces byte-perfect OTBM output.
    * *Constraint:* **NO** heuristics. If a byte is unknown, mark it as `UNKNOWN`, do not guess.
3.  **Security:** Validate inputs against buffer overflows (malformed OTBMs).

### Phase 3: Stress Testing
1.  **Load Testing:** Simulate 100MB+ Map loads.
2.  **Leak Detection:** Verify `weakref` usage to prevent circular references in Map Nodes.

## Task List Template
- [ ] **Analyze:** Profiling of current implementation.
- [ ] **Optimize:** Refactor Data Models for memory.
- [ ] **Verify:** Binary diff against original RME output.

## Implementation List Template
- [ ] `core/optimization.py`: Specialized fast-path routines.
- [ ] `tests/perf/test_benchmark_[feature].py`: Performance regression tests.
"""

# ------------------------------------------
# Rules (.agents/rules & .cursor/rules)
# ------------------------------------------

RULES_COMMON = """# Common Project Rules

## 1. Zero Fallback Policy
- **Tests:** Assertions must be absolute. `assert x == 5`, never `assert x > 0` (unless logic dictates range).
- **Parsing:** If binary data is malformed, raise `CorruptDataError`. Do not attempt to "repair" silently.
- **Typing:** No `Any`. Use explicit types.

## 2. Linear Reasoning
- Do not jump to coding. **Plan -> Verify -> Code -> Refactor**.
- Always check `PROJECT_STRUCTURE.md` before importing a module.

## 3. Layered Architecture (Strict)
- **Core:** Data only.
- **Logic:** Business Logic.
- **Vis:** PyQt6 UI.
- *Violation:* Importing `PyQt6` in `Core` triggers an immediate halt.
"""

RULE_PROJECT_STRUCTURE = """---
description: STRICT Project Structure & Layering Rules
globs: py_rme_canary/**/*.py
---
# Project Structure Enforcement (PROJECT_STRUCTURE.md)

## Layer Boundaries (CRITICAL)
1.  **core/**:
    * CANNOT IMPORT: `vis_layer`, `logic_layer`, `PyQt6`
    * CAN IMPORT: `struct`, `pathlib`, `numpy`
2.  **logic_layer/**:
    * CANNOT IMPORT: `vis_layer`, `PyQt6` (except for signals/slots definitions)
    * CAN IMPORT: `core`
3.  **vis_layer/**:
    * CAN IMPORT: `core`, `logic_layer`, `PyQt6`

## File Naming
- Modules: `lowercase_with_underscores.py`
- Classes: `PascalCase`
- Tests: `test_modulename.py` in `tests/` folder matching source structure.

## Forbidden Patterns
- `from module import *` (Wildcard imports)
- Circular dependencies (use `TYPE_CHECKING` block for type hints).
"""

RULE_PYTHON_RME = """---
description: Python RME Implementation Patterns
globs: **/*.py
---
# Python RME Patterns

## Binary Data (OTBM/OTB)
- Use `struct` module for parsing.
- Always assume **Little Endian** (`<`) unless specified.
- Use `enum.IntEnum` for byte flags (Client versions, Node types).

## Qt Integration (PyQt6)
- **Signals:** Define signals in Logic layer classes to decouple UI.
- **Threading:** Heavy Map IO must run in `QThread` or `multiprocessing`.
- **Properties:** Use `@property` for getter/setters.

## Type Safety
- All public functions MUST have type hints.
- Use `typing.Optional`, `typing.List`, `typing.NewType`.
- **Coordinates:** Use `Position = NamedTuple('Position', [('x', int), ('y', int), ('z', int)])`.
"""

RULE_C_TO_PY = """---
description: C++ to Python Porting Guide
globs: **/*.py
---
# C++ to Python Translation Guide

## Pointers
- C++ `Item*` -> Python `Item` (Reference by default).
- C++ `std::shared_ptr` -> Python variable (automatic GC).
- C++ `nullptr` -> Python `None`.

## Data Structures
- C++ `std::map<Pos, Tile*>` -> Python `dict[Position, Tile]`.
- C++ `std::vector` -> Python `list`.

## Performance
- Avoid loops inside loops in Python for map iteration.
- Use `itertools` or generators.
"""

# ------------------------------------------
# Cursor Commands (.cursor/commands)
# ------------------------------------------

COMMANDS_JSON = {
    "py-new-core": {
        "description": "Create a Core Data Class (No UI)",
        "prompt": "Create a Python dataclass in `core/`. Use `__slots__` for optimization. Add docstrings. Ensure NO PyQt imports. Implement `serialize`/`deserialize` methods using `struct`."
    },
    "py-new-brush": {
        "description": "Port a Brush from C++ to Python",
        "prompt": "Read the Legacy C++ brush logic. Implement the logic class in `logic_layer/brushes/`. Inherit from `BaseBrush`. Ensure implementation of `draw` and `undraw`."
    },
    "py-parse-struct": {
        "description": "Generate struct.unpack string from C++ struct",
        "prompt": "Convert this C++ struct definition to a Python `struct.unpack` format string. Explain the byte offsets."
    },
    "py-test-gen": {
        "description": "Generate Pytest for Module",
        "prompt": "Create a pytest file for the selected module. Use `pytest.fixture` for setup. Mock any `vis_layer` dependencies if testing logic."
    }
}

# ==========================================
# INSTALLATION LOGIC
# ==========================================

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_step(msg):
    print(f"{Colors.CYAN}[INFO]{Colors.RESET} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print_success(f"Generated: {path}")

def main():
    root = Path.cwd()
    print(f"{Colors.YELLOW}=== py_rme_canary AI Environment Setup ==={Colors.RESET}")
    print(f"Target Directory: {root}")
    print(f"Focus: Python Reimplementation (PRD v2.1.0)\n")
    print(f"Mode: Linear & Reflective Reasoning (Zero Fallback)\n")

    # 1. Antigravity Workflows
    print_step("Installing Antigravity Workflows (.agent/workflows)...")
    write_file(root / ".agent/workflows/opus_workflow.md", WORKFLOW_OPUS)
    write_file(root / ".agent/workflows/sonnet_workflow.md", WORKFLOW_SONNET)
    write_file(root / ".agent/workflows/gemini_workflow.md", WORKFLOW_GEMINI)
    write_file(root / ".agent/workflows/gpt5_workflow.md", WORKFLOW_GPT5)

    # 2. Antigravity Rules
    print_step("Installing Antigravity Rules (.agent/rules)...")
    # Injetando as regras comuns + específicas
    write_file(root / ".agent/rules/opus_rules.md", RULES_COMMON + "\n" + RULE_PROJECT_STRUCTURE)
    write_file(root / ".agent/rules/sonnet_rules.md", RULES_COMMON + "\n" + RULE_PYTHON_RME)
    write_file(root / ".agent/rules/gemini_rules.md", RULES_COMMON)
    write_file(root / ".agent/rules/gpt5_rules.md", RULES_COMMON + "\n" + RULE_C_TO_PY)
    
    # 3. Cursor Rules
    print_step("Installing Cursor Rules (.cursor/rules)...")
    write_file(root / ".cursor/rules/project_structure.mdc", RULE_PROJECT_STRUCTURE)
    write_file(root / ".cursor/rules/python_rme.mdc", RULE_PYTHON_RME)
    write_file(root / ".cursor/rules/c_to_py.mdc", RULE_C_TO_PY)
    
    # 4. Cursor Commands
    print_step("Installing Cursor Commands (.cursor/commands)...")
    cmd_path = root / ".cursor/commands/rme_commands.json"
    cmd_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cmd_path, 'w', encoding='utf-8') as f:
        json.dump(COMMANDS_JSON, f, indent=2)
    print_success(f"Generated: {cmd_path}")

    # 5. README
    print_step("Generating Environment Readme...")
    readme = """# py_rme_canary Development Environment

## Context
Development of RME in Python, following `PRD.md` and `PROJECT_STRUCTURE.md`.

## Workflow Methodology (Linear & Reflective)
All agents follow a 3-Phase process: **Analysis -> Implementation -> Reflection**.
- **No Fallbacks:** Tests and Parsers fail loudly on error.
- **Strict Layering:** Core -> Logic -> Vis boundaries are absolute.

## AI Commands
- `/py-new-core`: Generate clean data structures.
- `/py-new-brush`: Port C++ brush to Python.
- `/py-parse-struct`: Helper for reading binary maps.
"""
    write_file(root / "PY_RME_ENV.md", readme)

    print(f"\n{Colors.GREEN}Setup Complete! AI agents configured with Linear Reasoning & Zero Fallback policies.{Colors.RESET}")

if __name__ == "__main__":
    main()