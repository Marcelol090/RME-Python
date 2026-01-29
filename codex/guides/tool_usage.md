# Tool Usage Guide (MCP Protocols)

(Concept source: Model Context Protocol)

## Philosophy
Treat the `py_rme_canary` environment as a **Server** that provides Resources (Code), Tools (Pytest, Mypy), and Prompts (Tasks). You are the **Client** orchestrating these primitives.

## 1. Primitives: Tools
Your "MCP Tools" are the executable functions provided by the environment.
*   **`pytest`**: The Validator Tool.
    *   *Usage:* checking correctness.
    *   *Protocol:* Run `pytest tests/unit/test_feature.py` -> Parse Output -> Fix -> Retry.
*   **`mypy`**: The Static Analysis Tool.
    *   *Usage:* ensuring type safety (Project Rule #1).
    *   *Protocol:* Run `mypy py_rme_canary/logic_layer/feature.py` -> Fix Errors.

## 2. Primitives: Resources
Your "MCP Resources" are the files you manipulate.
*   **Read-Only Resources:** `RME/source/` (Legacy Codebases). You consume these to generate Prompt Context.
*   **Writable Resources:** `py_rme_canary/` (The Application). You modify these to achieve state changes (Task Completion).

## 3. Workflow: Client-Server Interaction
1.  **Connect:** Initialize context by reading `AGENTS.md` (The Handshake).
2.  **Sample:** Read `PRD.md` and `IMPLEMENTATION_STATUS.md` (Resource Discovery).
3.  **Execute:** Use Tools (`edit_file`, `run_command`) to modify Writable Resources.
4.  **Disconnect:** Update `IMPLEMENTATION_STATUS.md` (State Synchronization) before finishing the turn.
