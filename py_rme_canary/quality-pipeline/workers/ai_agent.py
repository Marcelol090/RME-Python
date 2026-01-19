#!/usr/bin/env python3
"""
AI Agent - Autonomous Code Refactoring (v3.0)
Event-sourced state machine with rollback support

Design: github.com/microsoft/autogen pattern
"""

import json
import logging
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent execution states"""

    INIT = "init"
    ANALYZE = "analyze"
    PRIORITIZE = "prioritize"
    PLAN = "plan"
    EXECUTE = "execute"
    VALIDATE = "validate"
    ROLLBACK = "rollback"
    COMMIT = "commit"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass
class Event:
    """State transition event (audit log)"""

    timestamp: float
    from_state: AgentState
    to_state: AgentState
    payload: dict[str, Any]
    success: bool = True
    error: str | None = None


@dataclass
class Issue:
    """Code issue detected by analysis"""

    file: Path
    line: int
    rule_id: str
    severity: str  # critical, high, medium, low
    message: str
    fix_confidence: float  # 0.0 - 1.0
    llm_suggestion: str | None = None


@dataclass
class FixPlan:
    """Execution plan for fixes"""

    issue: Issue
    fix_command: str
    dependencies: list[str] = field(default_factory=list)
    priority_score: float = 0.0


class AgentContext:
    """Execution context with event log"""

    def __init__(self, project_root: Path, config: dict[str, Any]):
        self.project_root = project_root
        self.config = config
        self.state = AgentState.INIT

        # Event sourcing
        self.events: list[Event] = []
        self.snapshots: dict[AgentState, dict[str, Any]] = {}

        # Working data
        self.issues: list[Issue] = []
        self.plan: list[FixPlan] = []
        self.applied_fixes: list[str] = []

        # Git state
        self.rollback_commit: str | None = None

    def emit_event(self, to_state: AgentState, payload: dict[str, Any], success: bool = True, error: str | None = None):
        """Record state transition"""
        event = Event(
            timestamp=time.time(),
            from_state=self.state,
            to_state=to_state,
            payload=payload,
            success=success,
            error=error,
        )

        self.events.append(event)

        if success:
            self.state = to_state
            log.info(f"State: {self.state.value}")
        else:
            log.error(f"Transition failed: {self.state.value} → {to_state.value}")

    def snapshot(self):
        """Create state snapshot"""
        self.snapshots[self.state] = {
            "issues": [vars(i) for i in self.issues],
            "plan": [vars(p) for p in self.plan],
            "applied_fixes": self.applied_fixes.copy(),
        }

    def restore_snapshot(self, state: AgentState):
        """Restore from snapshot"""
        if state not in self.snapshots:
            raise ValueError(f"No snapshot for state: {state}")

        data = self.snapshots[state]
        # Restore logic (simplified)
        self.state = state
        log.info(f"Restored to state: {state.value}")


class StateMachine:
    """Agent state machine orchestrator"""

    def __init__(self, context: AgentContext):
        self.ctx = context

        # State handlers
        self.handlers: dict[AgentState, Callable] = {
            AgentState.INIT: self._handle_init,
            AgentState.ANALYZE: self._handle_analyze,
            AgentState.PRIORITIZE: self._handle_prioritize,
            AgentState.PLAN: self._handle_plan,
            AgentState.EXECUTE: self._handle_execute,
            AgentState.VALIDATE: self._handle_validate,
            AgentState.ROLLBACK: self._handle_rollback,
            AgentState.COMMIT: self._handle_commit,
        }

    def run(self) -> bool:
        """Execute state machine until terminal state"""

        log.info(f"Agent starting: {self.ctx.project_root}")

        max_iterations = 100  # Safety limit
        iterations = 0

        while self.ctx.state not in [AgentState.COMPLETED, AgentState.FAILED]:
            if iterations >= max_iterations:
                log.error("Max iterations reached")
                self.ctx.emit_event(AgentState.FAILED, {"reason": "timeout"}, success=False)
                break

            handler = self.handlers.get(self.ctx.state)

            if not handler:
                log.error(f"No handler for state: {self.ctx.state}")
                self.ctx.emit_event(AgentState.FAILED, {"reason": "no_handler"}, success=False)
                break

            try:
                handler()
            except Exception as e:
                log.exception(f"Handler failed: {e}")
                self.ctx.emit_event(AgentState.FAILED, {"error": str(e)}, success=False)
                break

            iterations += 1

        success = self.ctx.state == AgentState.COMPLETED

        if success:
            log.info(f"Agent completed: {len(self.ctx.applied_fixes)} fixes applied")
        else:
            log.error(f"Agent failed in state: {self.ctx.state.value}")

        return success

    def _handle_init(self):
        """Initialize agent (create git snapshot)"""

        # Create rollback point
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=False, cwd=self.ctx.project_root, capture_output=True, text=True
        )

        if result.returncode == 0:
            self.ctx.rollback_commit = result.stdout.strip()
            log.info(f"Rollback commit: {self.ctx.rollback_commit[:8]}")

        self.ctx.emit_event(AgentState.ANALYZE, {"rollback_commit": self.ctx.rollback_commit})

    def _handle_analyze(self):
        """Analyze codebase with all tools"""

        log.info("Running analysis tools...")

        # Run Ruff
        ruff_result = subprocess.run(
            ["ruff", "check", ".", "--output-format=json"],
            check=False,
            cwd=self.ctx.project_root,
            capture_output=True,
            text=True,
        )

        # Parse Ruff output
        if ruff_result.returncode in [0, 1]:  # 1 = issues found
            try:
                ruff_data = json.loads(ruff_result.stdout)

                for item in ruff_data:
                    issue = Issue(
                        file=Path(item["filename"]),
                        line=item["location"]["row"],
                        rule_id=item["code"],
                        severity=self._map_severity(item),
                        message=item["message"],
                        fix_confidence=0.9 if item.get("fix") else 0.5,
                    )
                    self.ctx.issues.append(issue)

            except json.JSONDecodeError:
                log.warning("Failed to parse Ruff output")

        # Run Mypy
        mypy_result = subprocess.run(
            ["mypy", ".", "--no-error-summary"], check=False, cwd=self.ctx.project_root, capture_output=True, text=True
        )

        # Parse Mypy errors (simplified)
        for line in mypy_result.stderr.split("\n"):
            if ": error:" in line:
                parts = line.split(":")
                if len(parts) >= 4:
                    issue = Issue(
                        file=Path(parts[0]),
                        line=int(parts[1]) if parts[1].isdigit() else 0,
                        rule_id="mypy",
                        severity="high",
                        message=":".join(parts[3:]).strip(),
                        fix_confidence=0.3,  # Lower for type errors
                    )
                    self.ctx.issues.append(issue)

        log.info(f"Found {len(self.ctx.issues)} issue(s)")

        self.ctx.snapshot()
        self.ctx.emit_event(AgentState.PRIORITIZE, {"issues_count": len(self.ctx.issues)})

    def _handle_prioritize(self):
        """Score and sort issues by impact"""

        log.info("Prioritizing issues...")

        # Severity weights
        severity_weight = {"critical": 10.0, "high": 5.0, "medium": 2.0, "low": 1.0, "info": 0.5}

        # Score each issue
        for issue in self.ctx.issues:
            score = severity_weight.get(issue.severity, 1.0)
            score *= issue.fix_confidence

            # Bonus for auto-fixable
            if issue.fix_confidence >= 0.8:
                score *= 1.5

            # Penalty for type errors (harder to auto-fix)
            if issue.rule_id == "mypy":
                score *= 0.5

            # Create plan item
            fix_cmd = self._generate_fix_command(issue)

            if fix_cmd:
                plan = FixPlan(issue=issue, fix_command=fix_cmd, priority_score=score)
                self.ctx.plan.append(plan)

        # Sort by priority
        self.ctx.plan.sort(key=lambda p: p.priority_score, reverse=True)

        # Filter low-confidence fixes if configured
        min_confidence = self.ctx.config.get("min_fix_confidence", 0.7)
        self.ctx.plan = [p for p in self.ctx.plan if p.issue.fix_confidence >= min_confidence]

        log.info(f"Execution plan: {len(self.ctx.plan)} fix(es)")

        self.ctx.snapshot()
        self.ctx.emit_event(AgentState.PLAN, {"plan_size": len(self.ctx.plan)})

    def _handle_plan(self):
        """Generate execution plan (dependency ordering)"""

        log.info("Building execution plan...")

        # Simple plan for now (already sorted by priority)
        # Future: dependency graph analysis

        self.ctx.emit_event(AgentState.EXECUTE, {"plan_ready": True})

    def _handle_execute(self):
        """Execute fixes incrementally"""

        log.info("Executing fixes...")

        max_fixes = self.ctx.config.get("max_auto_fixes", 50)
        applied = 0

        for i, plan in enumerate(self.ctx.plan):
            if applied >= max_fixes:
                log.info(f"Reached max fixes limit: {max_fixes}")
                break

            log.info(f"Fix {i + 1}/{len(self.ctx.plan)}: {plan.issue.rule_id} ({plan.priority_score:.2f})")

            # Execute fix command
            result = subprocess.run(
                plan.fix_command, check=False, shell=True, cwd=self.ctx.project_root, capture_output=True, text=True
            )

            if result.returncode == 0:
                self.ctx.applied_fixes.append(str(plan.issue.file))
                applied += 1
                log.info("  ✓ Applied")
            else:
                log.warning(f"  ✗ Failed: {result.stderr[:100]}")

        log.info(f"Applied {applied} fix(es)")

        self.ctx.emit_event(AgentState.VALIDATE, {"fixes_applied": applied})

    def _handle_validate(self):
        """Validate fixes (run tests)"""

        log.info("Validating fixes...")

        # Run tests if available
        test_cmd = self.ctx.config.get("test_command", "pytest")

        if self.ctx.config.get("run_tests", True):
            result = subprocess.run(test_cmd, check=False, shell=True, cwd=self.ctx.project_root, capture_output=True)

            if result.returncode != 0:
                log.error("Tests failed after fixes")
                self.ctx.emit_event(AgentState.ROLLBACK, {"reason": "test_failure"}, success=True)
                return

        # Validate with Mypy
        mypy_result = subprocess.run(["mypy", "."], check=False, cwd=self.ctx.project_root, capture_output=True)

        if mypy_result.returncode != 0:
            log.warning("Mypy found issues (non-fatal)")

        self.ctx.emit_event(AgentState.COMMIT, {"validation": "passed"})

    def _handle_rollback(self):
        """Rollback to snapshot"""

        log.info("Rolling back changes...")

        if self.ctx.rollback_commit:
            subprocess.run(["git", "reset", "--hard", self.ctx.rollback_commit], check=False, cwd=self.ctx.project_root)
            log.info("Rollback complete")

        self.ctx.emit_event(AgentState.FAILED, {"rollback": "completed"})

    def _handle_commit(self):
        """Commit successful fixes"""

        log.info("Committing fixes...")

        if self.ctx.config.get("auto_commit", False):
            subprocess.run(["git", "add", "-A"], check=False, cwd=self.ctx.project_root)

            subprocess.run(
                ["git", "commit", "-m", "refactor: automated quality improvements"],
                check=False,
                cwd=self.ctx.project_root,
            )

        self.ctx.emit_event(AgentState.COMPLETED, {"fixes_committed": len(self.ctx.applied_fixes)})

    def _map_severity(self, ruff_item: dict) -> str:
        """Map Ruff code to severity"""
        code = ruff_item["code"]

        if code.startswith("E") or code.startswith("F"):
            return "high"
        elif code.startswith("W"):
            return "medium"
        elif code.startswith("S"):  # Security
            return "critical"
        else:
            return "low"

    def _generate_fix_command(self, issue: Issue) -> str | None:
        """Generate fix command for issue"""

        # Ruff auto-fix
        if issue.rule_id.startswith(("E", "F", "W", "I", "N")):
            return f"ruff check --fix --select {issue.rule_id} {issue.file}"

        # No auto-fix for Mypy errors
        if issue.rule_id == "mypy":
            return None

        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AI Agent - Autonomous Refactoring")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    # Load config
    config = {}
    if args.config and args.config.exists():
        config = json.loads(args.config.read_text())

    # Defaults
    config.setdefault("min_fix_confidence", 0.7)
    config.setdefault("max_auto_fixes", 50)
    config.setdefault("run_tests", True)
    config.setdefault("auto_commit", not args.dry_run)

    # Create context
    context = AgentContext(args.project, config)

    # Run agent
    machine = StateMachine(context)
    success = machine.run()

    # Event log
    log_file = args.project / ".quality_reports" / "agent_events.jsonl"
    log_file.parent.mkdir(exist_ok=True)

    with open(log_file, "w") as f:
        for event in context.events:
            f.write(json.dumps(vars(event), default=str) + "\n")

    log.info(f"Event log: {log_file}")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
