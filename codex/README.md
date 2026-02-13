# Codex Environment: The Navigation Map

> [!IMPORTANT]
> This Codex acts as the "Navigation Map" for the Agent. It defines *Structure*, *Limits*, and *Flow*.

## 🌟 Vision
The goal is to transform from a reactive executor into a **proactive collaborator** that plans, implements, acts, and reflects.

## 🗺️ Navigation Map (Linear Flow)

The Agent must follow this strict linear lifecycle for every complex task:

1.  **🔍 Planning (Orient)**
    *   **Goal**: Understand the detailed requirements.
    *   **Action**: Research, OODA (Orient Phase), Create/Update `implementation_plan.md`.
    *   **Reference**: [guide: Agent Workflow](guides/agent_workflow.md)

2.  **📋 Tasks (Decide)**
    *   **Goal**: Break down work into atomic units.
    *   **Action**: Create/Update `task.md`.
    *   **Reference**: [guide: Task Management](guides/agent_workflow.md#task-management)

3.  **⚡ Implementation (Act)**
    *   **Goal**: Execute the plan.
    *   **Action**: Write code, OODA (Act Phase).
    *   **Reference**: [skill: Port Feature](skills/port_feature.md)

4.  **🛡️ Verification (Observe/Reflect)**
    *   **Goal**: Ensure quality and completeness.
    *   **Action**: Run Tests, Manual Review, Reflexion Loop (Self-Correction).
    *   **Reference**: [guide: Testing](guides/testing.md)

## 📂 Structure

### 🧠 Intelligence (`codex/`)
*   **[AGENTS.md](agents.md)**: The Master System Prompt & Identity.
*   **[README.md](README.md)**: This map.

### 📜 The Laws (`codex/rules/`)
*   **[execution.rules](rules/execution.rules)**: Security policies (What can be run).
*   **[development.md](rules/development.md)**: Behavioral standards (How to behave).

### 🛠️ The Capabilities (`codex/skills/`)
*   **[port_feature.md](skills/port_feature.md)**: C++ to Python porting.
*   **[create_widget.md](skills/create_widget.md)**: UI Component creation.
*   **[verify_parity.md](skills/verify_parity.md)**: Legacy parity checking.

### 🗺️ The Guides (`codex/guides/`)
*   **[agent_workflow.md](guides/agent_workflow.md)**: **[NEW]** The Operating Manual.
*   **[knowledge_retrieval.md](guides/knowledge_retrieval.md)**: RAG & Search.
*   **[tool_usage.md](guides/tool_usage.md)**: MCP Tool protocols.
*   **[extending_codex.md](guides/extending_codex.md)**: **[NEW]** How to create Skills & Rules.
*   **[uixwidget_scope.md](guides/uixwidget_scope.md)**: Branch scope contract for `UixWidget` (UI/UX + Widget + Render only).

## ⚙️ Python + Rust Acceleration

Project strategy is PyQt6-first with selective Rust acceleration:

- Keep UI/session orchestration in Python.
- Migrate only profiled CPU hot paths to Rust.
- Preserve Python fallback behavior when Rust module is unavailable.
- Add parity tests for fallback and accelerated paths.

Current acceleration boundary:
- Python adapter: `py_rme_canary/logic_layer/rust_accel.py`
- Rust module: `py_rme_canary/rust/py_rme_canary_rust/`

## Branch Governance

- `UixWidget` must stay scoped to UI/UX, Widgets, and Render-facing behavior.
- Promotion path:
  - `UixWidget` -> `development` -> `main`
- Detailed policy:
  - `codex/guides/uixwidget_scope.md`
  - `py_rme_canary/docs/Reference/Guides/UIXWIDGET_BRANCH_POLICY.md`
