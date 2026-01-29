# Guide: Configuring AGENTS.md for RME Parity

(Scope: `py_rme_canary`)

## Purpose
The `AGENTS.md` file is the "operating system" for any agent working on this project. It is not just a list of tips—it is a strict contract.

## Mandated Sections

### 1. The Prime Directive (Parity)
Every agent MUST understand that `RME` (Legacy C++) is the master blueprint.
*   **Required Text:**
    > "You are porting Remere's Map Editor. Your decisions must match the logic in `RME/source` or `Remeres-map-editor-linux-4.0.0`."

### 2. The Protocols (Behavior)
*   **Fetch First:** Prevent hallucinations by mandating web search for docs.
*   **Beast Mode:** Enforce "don't stop until done" autonomy.

### 3. The Reference Map (Context)
The agent must know *where* to look.
*   **Legacy:** `C:\Users\Marcelo Henrique\Desktop\projec_rme\RME` & `...\Remeres-map-editor-linux-4.0.0`.
*   **New:** `py_rme_canary/logic_layer`, `vis_layer/ui`.

## Template Structure
When updating `codex/AGENTS.md`, follow this hierarchy:
1.  **Identity:** Who am I? (RME Porting Specialist).
2.  **Context:** What are the active docs? (PRD, Status).
3.  **Capabilities:** What Skills do I have? (Links to `codex/skills/*.md`).
4.  **Rules:** What is forbidden? (Links to `codex/rules/*.md`).

## Verification
An `AGENTS.md` is valid ONLY if it explicitly links to:
- [ ] `codex/skills/port_feature.md`
- [ ] `codex/skills/verify_parity.md`
- [ ] `codex/rules/development.md`
