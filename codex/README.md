# Codex Environment

This directory (`codex/`) contains the **intelligence configuration** for the "Beast Mode" agent working on `py_rme_canary`.

## Structure

### 🧠 The Brain
*   **`AGENTS.md`**: The Master System Prompt. Defines "Who am I?" and "What is the mission?".

### 📜 The Laws (`rules/`)
*   **`execution.rules`**: Starlark policies defining *what commands* can be run (Security).
*   **`development.md`**: Behavioral guidelines defining *how to behave* (Ethics/Standards).

### 🛠️ The Capabilities (`skills/`)
*   **`port_feature.md`**: Guide for C++ -> Python logic porting.
*   **`create_widget.md`**: Guide for creating clean PyQt6 UI components.
*   **`verify_parity.md`**: QA protocol for Legacy Parity checks.

### 🗺️ The Maps (`guides/`)
*   **`knowledge_retrieval.md`**: How to find information (Manual RAG).
*   **`tool_usage.md`**: How to use the environment as an MCP Server.
*   **`workflows.md`**: Standard operating procedures.
*   **`testing.md`**: Testing patterns.

## Usage
When initializing an agent session, ensure `AGENTS.md` is loaded into the context. The agent will then reference the internal documentation in this directory to self-regulate and execute tasks with high precision.
