# Agent Workflow Guide

> [!NOTE]
> This guide defines the **Linear Flow** and **Reflective Feedback** mechanisms for the Agent.

## 🔄 The OODA Loop (Continuous Intelligence)

The Agent operates on a continuous **OODA Loop**:

1.  **Observe**: Read file state, test results, error logs.
2.  **Orient**: Compare observation against the Plan (`implementation_plan.md`) and Requirements.
3.  **Decide**: Determine the NEXT atomic step. Update `task.md`.
4.  **Act**: Execute the tool call (Edit, Run, etc.).

---

## 🛣️ Linear Lifecycle

### Phase 1: Planning (Orient)
*   **Trigger**: New complex user request.
*   **Mandatory Actions**:
    1.  **Research**: Use `knowledge_retrieval` to find context.
    2.  **Plan**: Create `implementation_plan.md`.
    3.  **Approve**: Ask user for review (unless trivial).

### Phase 2: Tasks (Decide)
*   **Trigger**: Plan approval.
*   **Mandatory Actions**:
    1.  **Breakdown**: Create `task.md` with granular checklists.
    2.  **Prioritize**: Identify the critical path.

### Phase 3: Implementation (Act)
*   **Trigger**: Active item in `task.md`.
*   **Mandatory Actions**:
    1.  **Atomic Edits**: Change one logical unit at a time.
    2.  **Persist State**: Mark `task.md` item as `[/]` (in-progress).

### Phase 4: Verification (Observe/Reflect)
*   **Trigger**: Completion of a code change.
*   **Mandatory Actions**:
    1.  **Test**: Run `pytest` or manual verification options.
    2.  **Jules**: Trigger Jules API for suggestions (`run_jules_generate_tests` or `quality.sh`).
    3.  **Reflexion**: Ask "Did this fix the root cause?"
    4.  **Done**: Mark `task.md` item as `[x]`.

---

## Jules/Codex Automation Flow

Use this sequence for feature work that should go through async automation:

1.  **Local Quality Gate**
    - Run `./quality.sh --dry-run --skip-tests --skip-libcst --skip-sonarlint`.
    - Fix blocking issues before opening async automation.
    - Optionally inspect Jules API state via `jules_runner.py list-sources|list-sessions|session-status`.
2.  **Jules Async Implementation**
    - Add label `jules` to the target issue.
    - Workflow `jules-on-issue-label.yml` invokes Jules and expects:
      - `reports/jules/suggestions.md`
      - `reports/jules/suggestions.json`
3.  **Codex PR Alignment**
    - For PRs authored by `google-labs-jules`, workflow `codex_review_for_jules_prs.yml` runs Codex review.
    - O workflow também reage quando o Jules comenta no PR (`issue_comment`), mantendo revisão assíncrona monitorada.
    - Codex usa `codex/review_jules_pr.md` + snapshots `.codex_context/jules_pr_context.md` e `.codex_context/jules_pr_context.json`.
    - O snapshot é construído por `py_rme_canary/scripts/build_jules_context.py` (metadata, comentários, commits e arquivos alterados).
4.  **Scheduled Safety Net**
    - `codex_review_scheduler.yml` dispatches missing Codex reviews for open Jules PRs.
    - `jules-security-agent.yml` performs daily security-focused async scans.

Required secrets in CI:
- `JULES_API_KEY`
- `OPENAI_API_KEY`

---

## 🧠 Reflexion (Self-Correction)

**Triggers for Self-Reflection:**
*   A test fails.
*   A tool call errors.
*   The output text differs from the `task.md` goal.

**The Reflexion Prompt (Internal Monologue):**
> "I attempted X. The result was Y. This failed because Z. My new plan is A."

---

## 📝 Task Management
*   **File**: `task.md` (in artifacts directory)
*   **Tool**: `task_boundary`
*   **Rule**: NEVER proceed to the next step without updating `task.md`.
