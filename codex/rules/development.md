# Development Rules (Beast Mode)

## 1. Governance & Ethics
## 1. Governance & Ethics
*   **Parity Prime Directive**: You are porting `RME` / `Remeres-map-editor-linux` to `py_rme_canary`.
    *   *Rule:* **NO LOGIC WITHOUT REFERENCE.** You must locate the equivalent C++ code in `RME` or `Remeres-map-editor-linux-4.0.0` before writing Python.
    *   *Violation:* Creating "new" brush logic without finding the C++ `Brush::draw`.
    *   *Correct:* `grep_search("Brush::draw", "RME")` -> Analyze -> Port to Python.
*   **Source of Truth**: The C++ code (`RME/source`) dictates the behavior. `PRD.md` dictates the requirements.

## 2. Coding Standards (The "Deep" Rules)
*   **Strict Typing**: `mypy` is not a suggestion. It is law.
    *   *Bad:* `def do_thing(item):`
    *   *Good:* `def do_thing(item: ItemType) -> bool:`
*   **UI/Logic Firewall**:
    *   `vis_layer` (PyQt6) files MUST NEVER import `logic_layer` internals directly. Use Signals/Slots or Data Classes.
    *   `core` code MUST NOT import `PyQt6`.

## 3. The "Don't" List
*   **DON'T** rewrite the entire file when a patch will do (Token waste).
*   **DON'T** leave `TODO` comments without adding them to `MASTER_TODO.md`.
*   **DON'T** execute `git commit` without user request (Agent Protocol).

## 4. Testing Protocols
*   **Zero Regression**: If you fix a bug, you add a test case.
*   **Smoke Checks**: When touching UI, run `pytest tests/ui` to ensure no segfaults.

## 5. Documentation & Research (Anti-Hallucination)
*   **Fetch First Protocol**: When the user provides a URL (especially for Codex/OpenAI docs) or when you need to verify a library version, you MUST use `fetch_webpage` or `read_url_content`.
    *   *Why:* Your training data is outdated. The web is source of truth.
*   **Continuous Improvement**: If fetched documentation reveals new features or deprecations, you MUST update the relevant guide in `codex/guides/`.
