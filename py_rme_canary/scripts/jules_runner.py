#!/usr/bin/env python3
"""CLI wrapper for local Jules workflow automation."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any

from jules_api import (
    JulesAPIError,
    JulesClient,
    load_env_defaults,
    normalize_session_name,
    normalize_source,
    resolve_config,
    resolve_git_branch,
    write_json,
)

UTC_TZ = getattr(dt, "UTC", dt.timezone.utc)  # noqa: UP017


def utc_now_iso() -> str:
    """Return ISO-8601 UTC timestamp."""
    return dt.datetime.now(UTC_TZ).replace(microsecond=0).isoformat()


def truncate_text(value: str, limit: int = 300) -> str:
    """Trim long values for compact report output."""
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def _compact_json(value: object) -> str:
    """Serialize JSON payload with deterministic formatting."""
    return json.dumps(value, indent=2, ensure_ascii=False)


def _compress_quality_report(raw: str) -> str:
    """Reduce noisy report sections to keep Jules prompts focused and small."""
    lines = raw.splitlines()
    output: list[str] = []
    in_artifacts = False
    artifact_kept = 0
    artifact_total = 0

    for line in lines:
        stripped = line.strip()
        is_header = stripped.startswith("##")
        if is_header:
            if in_artifacts and artifact_total > artifact_kept:
                omitted = artifact_total - artifact_kept
                output.append(f"- ... {omitted} additional artifacts omitted for prompt compactness")
            in_artifacts = "artefatos gerados" in stripped.lower()
            artifact_kept = 0
            artifact_total = 0
            output.append(line)
            continue

        if in_artifacts and stripped.startswith("-"):
            artifact_total += 1
            if artifact_kept < 12:
                output.append(line)
                artifact_kept += 1
            continue

        if stripped.startswith("- `quality_") and stripped.endswith(".log`"):
            continue
        output.append(line)

    if in_artifacts and artifact_total > artifact_kept:
        omitted = artifact_total - artifact_kept
        output.append(f"- ... {omitted} additional artifacts omitted for prompt compactness")

    compact = "\n".join(output).strip()
    compact = re.sub(r"\n{3,}", "\n\n", compact)
    return compact


def _balanced_truncate(text: str, limit: int) -> str:
    """Keep both beginning and end when truncating long report text."""
    if len(text) <= limit:
        return text
    head_size = int(limit * 0.7)
    tail_size = max(0, limit - head_size - 40)
    marker = "\n...[quality context truncated]...\n"
    return f"{text[:head_size]}{marker}{text[-tail_size:]}"


def read_quality_context(path: Path, *, max_chars: int = 4200) -> str:
    """Read quality report context used to prompt Jules."""
    if not path.exists() or not path.is_file():
        return ""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    clean = _compress_quality_report(raw.strip())
    return _balanced_truncate(clean, max_chars)


def build_quality_prompt(*, report_text: str, task: str) -> str:
    """Build an explicit, structured prompt optimized for Jules suggestions."""
    context_block = report_text if report_text else "Quality report context is not available."
    return (
        "You are Jules, a senior Python quality engineer for a PyQt6 map editor project.\n"
        "Objective: convert report evidence into high-impact, low-risk implementation steps.\n"
        "Execution style: linear and verifiable (Evidence -> Risk -> Action -> Verification).\n"
        "\n"
        "Hard constraints:\n"
        "1) Use only evidence present in the report context.\n"
        "2) Prefer high-impact actions that reduce defects, security risk, and CI instability.\n"
        "3) Keep suggestions small enough to become isolated PRs.\n"
        "4) Do not include markdown commentary outside the requested JSON block.\n"
        "5) If data is missing, explain uncertainty in the `rationale` field.\n"
        "6) For each suggestion, include at least one concrete verification step in the rationale.\n"
        "\n"
        "Reasoning protocol (apply in this order):\n"
        "- Step 1: Extract concrete evidence lines and classify impact "
        "(security, correctness, maintainability, performance).\n"
        "- Step 2: Rank by severity and blast-radius.\n"
        "- Step 3: Propose minimal PR-sized actions with explicit file targets.\n"
        "- Step 4: Add validation guidance (tests/lint/quality command).\n"
        "\n"
        "Output format (required): return a single ```json fenced block with this top-level shape:\n"
        "{\n"
        '  "jules_suggestions": {\n'
        '    "implemented": [\n'
        '      {"id":"IMP-001","summary":"...", "files":["path.py"], "evidence":"..."}\n'
        "    ],\n"
        '    "suggested_next": [\n'
        '      {"id":"SUG-001","severity":"HIGH|MED|LOW|CRITICAL","summary":"...",'
        ' "rationale":"...", "files":["path.py"], "links":["https://..."]}\n'
        "    ]\n"
        "  }\n"
        "}\n"
        "\n"
        "Volume limits:\n"
        "- implemented: maximum 4 entries.\n"
        "- suggested_next: maximum 8 entries.\n"
        "\n"
        "Quality bar for each `suggested_next` item:\n"
        "- `summary`: one concrete change, no vague wording.\n"
        "- `files`: repository-relative paths likely touched.\n"
        "- `rationale`: why now, risk if skipped, and how to verify.\n"
        "- `severity`: choose CRITICAL/HIGH/MED/LOW using report evidence only.\n"
        "\n"
        f"Task: {task}\n"
        "Quality report context (bounded by tags):\n"
        "<quality_report>\n"
        f"{context_block}\n"
        "</quality_report>\n"
    )


def _find_contract_candidates(payload: object) -> list[dict[str, Any]]:
    """Find nested dicts that already resemble the suggestions contract."""
    found: list[dict[str, Any]] = []
    stack: list[object] = [payload]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            if "implemented" in current and "suggested_next" in current:
                found.append(current)
            jules_block = current.get("jules_suggestions")
            if isinstance(jules_block, dict):
                found.append(jules_block)
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str):
            text = current.strip()
            if "implemented" in text and "suggested_next" in text:
                for fenced in re.findall(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL):
                    try:
                        parsed = json.loads(fenced)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(parsed, dict):
                        found.append(parsed)
    return found


def _coerce_implemented(entries: object) -> list[dict[str, Any]]:
    if not isinstance(entries, list):
        return []
    normalized: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            if isinstance(entry, str) and entry.strip():
                normalized.append(
                    {
                        "id": f"IMP-{index:03d}",
                        "summary": entry.strip(),
                        "files": [],
                        "evidence": "",
                    }
                )
            continue
        normalized.append(
            {
                "id": str(entry.get("id") or f"IMP-{index:03d}"),
                "summary": str(entry.get("summary") or entry.get("title") or "Implemented update"),
                "files": [str(v) for v in entry.get("files", []) if str(v).strip()],
                "evidence": str(entry.get("evidence") or ""),
            }
        )
    return normalized


def _coerce_suggested(entries: object) -> list[dict[str, Any]]:
    if not isinstance(entries, list):
        return []
    allowed_severity = {"CRITICAL", "HIGH", "MED", "LOW"}
    normalized: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            if isinstance(entry, str) and entry.strip():
                normalized.append(
                    {
                        "id": f"SUG-{index:03d}",
                        "severity": "MED",
                        "summary": entry.strip(),
                        "rationale": "",
                        "files": [],
                        "links": [],
                    }
                )
            continue
        severity = str(entry.get("severity") or "MED").upper()
        if severity not in allowed_severity:
            severity = "MED"
        normalized.append(
            {
                "id": str(entry.get("id") or f"SUG-{index:03d}"),
                "severity": str(entry.get("priority") or severity).upper()
                if str(entry.get("priority") or severity).upper() in allowed_severity
                else severity,
                "summary": str(entry.get("summary") or entry.get("title") or "Follow-up suggestion"),
                "rationale": str(entry.get("rationale") or ""),
                "files": [str(v) for v in entry.get("files", []) if str(v).strip()],
                "links": [str(v) for v in entry.get("links", []) if str(v).strip()],
            }
        )
    return normalized


def extract_contract_from_activity(activity: object) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Try extracting suggestions contract data from activity payload."""
    candidates = _find_contract_candidates(activity)
    for candidate in candidates:
        implemented = _coerce_implemented(candidate.get("implemented"))
        suggested = _coerce_suggested(
            candidate.get("suggested_next") or candidate.get("suggestedNext") or candidate.get("suggestions")
        )
        if implemented or suggested:
            return implemented, suggested
    return [], []


def _extract_first_activity(payload: object) -> object:
    """Normalize latest activity payloads from different API response shapes."""
    if isinstance(payload, dict):
        for key in ("activity", "latestActivity"):
            candidate = payload.get(key)
            if isinstance(candidate, dict | list):
                return candidate
        activities = payload.get("activities")
        if isinstance(activities, list) and activities:
            return activities[0]
    return payload


def _resolve_client(args: argparse.Namespace, *, require_source: bool = True) -> JulesClient:
    project_root = Path(args.project_root).resolve()
    load_env_defaults(project_root, override=False)
    source_override = args.source if require_source else (args.source or os.environ.get("JULES_SOURCE", ""))
    config = resolve_config(
        project_root,
        source=source_override,
        branch=args.branch,
        timeout_seconds=float(args.timeout),
    )
    return JulesClient(config)


def build_fallback_contract(
    *,
    category: str,
    task: str,
    quality_report: Path,
    session_name: str | None,
    implemented: list[dict[str, Any]],
    suggested_next: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build schema-compatible suggestions contract."""
    generated_at = utc_now_iso()

    effective_implemented = list(implemented)
    if session_name:
        effective_implemented.insert(
            0,
            {
                "id": "IMP-001",
                "summary": "Jules API session created from local quality pipeline.",
                "files": [
                    "py_rme_canary/scripts/jules_api.py",
                    "py_rme_canary/scripts/jules_runner.py",
                    "py_rme_canary/quality-pipeline/quality_lf.sh",
                ],
                "evidence": session_name,
            },
        )

    return {
        "version": 1,
        "category": category,
        "task": task,
        "generated_at": generated_at,
        "quality_bundle": {
            "path": str(quality_report).replace("\\", "/"),
            "generated_at": generated_at,
        },
        "implemented": effective_implemented,
        "suggested_next": suggested_next,
    }


def validate_contract(payload: dict[str, Any], schema_path: Path | None) -> list[str]:
    """Validate contract with a minimal schema-aware checker."""
    errors: list[str] = []
    required = ["version", "category", "implemented", "suggested_next", "generated_at"]
    for key in required:
        if key not in payload:
            errors.append(f"Missing required field: {key}")

    category = str(payload.get("category", ""))
    allowed = {"quality", "security", "tests", "pipeline", "general"}
    if category and category not in allowed:
        errors.append(f"Invalid category: {category}")

    if not isinstance(payload.get("implemented", []), list):
        errors.append("Field `implemented` must be a list.")
    if not isinstance(payload.get("suggested_next", []), list):
        errors.append("Field `suggested_next` must be a list.")

    if schema_path is not None and schema_path.exists():
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema_required = schema.get("required", [])
            for key in schema_required:
                if key not in payload:
                    errors.append(f"Schema required field missing: {key}")
            enum_values = schema.get("properties", {}).get("category", {}).get("enum", [])
            if enum_values and category not in {str(v) for v in enum_values}:
                errors.append(f"Category outside schema enum: {category}")
        except Exception as exc:  # pragma: no cover - defensive path
            errors.append(f"Unable to parse schema file: {exc}")

    return errors


def write_markdown_report(path: Path, contract: dict[str, Any], *, session_name: str | None = None) -> None:
    """Write human-readable suggestions markdown."""
    lines = [
        "# Jules Suggestions",
        "",
        f"- Generated at: `{contract.get('generated_at', '')}`",
        f"- Category: `{contract.get('category', '')}`",
        f"- Task: `{contract.get('task', '')}`",
    ]
    if session_name:
        lines.append(f"- Session: `{session_name}`")
    lines.append("")
    lines.append("## Implemented")
    implemented = contract.get("implemented", [])
    if isinstance(implemented, list) and implemented:
        for entry in implemented:
            if not isinstance(entry, dict):
                continue
            summary = truncate_text(str(entry.get("summary", "")), 220)
            files = ", ".join(str(v) for v in entry.get("files", []))
            lines.append(f"- [{entry.get('id', 'IMP-XXX')}] {summary}")
            if files:
                lines.append(f"  - files: `{files}`")
    else:
        lines.append("- No implemented items captured.")
    lines.append("")
    lines.append("## Suggested Next")
    suggested_next = contract.get("suggested_next", [])
    if isinstance(suggested_next, list) and suggested_next:
        for entry in suggested_next:
            if not isinstance(entry, dict):
                continue
            summary = truncate_text(str(entry.get("summary", "")), 220)
            severity = str(entry.get("severity", "MED"))
            lines.append(f"- [{severity}] [{entry.get('id', 'SUG-XXX')}] {summary}")
    else:
        lines.append("- No follow-up suggestions provided.")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def command_check(args: argparse.Namespace) -> int:
    """Verify local Jules API connectivity."""
    try:
        client = _resolve_client(args)
    except ValueError as exc:
        print(f"[jules] check failed: {exc}")
        return 1

    config = client.config
    result: dict[str, Any] = {
        "checked_at": utc_now_iso(),
        "source": config.normalized_source(),
        "branch": config.branch,
        "source_exists": False,
    }
    try:
        result["source_exists"] = client.source_exists(config.source)
        result["status"] = "ok" if result["source_exists"] else "source_missing"
    except JulesAPIError as exc:
        result["status"] = "api_error"
        result["error"] = str(exc)
        if exc.status is not None:
            result["http_status"] = int(exc.status)

    if args.json_out:
        out_path = Path(args.json_out)
        write_json(out_path, result)

    print(f"[jules] status={result.get('status')} source={result.get('source')}")
    return 0 if result.get("status") == "ok" else 2


def command_list_sources(args: argparse.Namespace) -> int:
    """List Jules sources for the current API key."""
    try:
        client = _resolve_client(args, require_source=False)
        payload = client.list_sources(page_size=int(args.page_size), page_token=str(args.page_token or ""))
    except (ValueError, JulesAPIError) as exc:
        print(f"[jules] list-sources failed: {exc}")
        return 1

    if args.json_out:
        write_json(Path(args.json_out), payload)

    sources = payload.get("sources", []) if isinstance(payload, dict) else []
    if not isinstance(sources, list):
        sources = []
    print(f"[jules] sources={len(sources)}")
    for item in sources[: int(args.max_print)]:
        if isinstance(item, dict):
            print(f" - {item.get('name', '')}")
    return 0


def command_list_sessions(args: argparse.Namespace) -> int:
    """List Jules sessions for the configured source."""
    try:
        client = _resolve_client(args)
        payload = client.list_sessions(page_size=int(args.page_size), page_token=str(args.page_token or ""))
    except (ValueError, JulesAPIError) as exc:
        print(f"[jules] list-sessions failed: {exc}")
        return 1

    if args.json_out:
        write_json(Path(args.json_out), payload)

    sessions = payload.get("sessions", []) if isinstance(payload, dict) else []
    if not isinstance(sessions, list):
        sessions = []
    print(f"[jules] sessions={len(sessions)}")
    for item in sessions[: int(args.max_print)]:
        if not isinstance(item, dict):
            continue
        print(f" - {item.get('name', '')} [{item.get('state', 'UNKNOWN')}]")
    return 0


def command_session_status(args: argparse.Namespace) -> int:
    """Fetch session payload + latest activity for monitoring/debugging."""
    session_name = normalize_session_name(args.session_name)
    if not session_name:
        print("[jules] session-status failed: empty session name.")
        return 1
    try:
        client = _resolve_client(args)
        session_payload = client.get_session(session_name)
        latest_activity = client.get_latest_activity(session_name)
    except (ValueError, JulesAPIError) as exc:
        print(f"[jules] session-status failed: {exc}")
        return 1

    latest_normalized = _extract_first_activity(latest_activity)
    out_payload = {
        "checked_at": utc_now_iso(),
        "session": session_payload,
        "latest_activity": latest_normalized,
    }
    if args.json_out:
        write_json(Path(args.json_out), out_payload)
    print(f"[jules] session={session_name}")
    return 0


def command_approve_plan(args: argparse.Namespace) -> int:
    """Approve pending plan for a session."""
    session_name = normalize_session_name(args.session_name)
    if not session_name:
        print("[jules] approve-plan failed: empty session name.")
        return 1
    try:
        client = _resolve_client(args)
        payload = client.approve_plan(session_name)
    except (ValueError, JulesAPIError) as exc:
        print(f"[jules] approve-plan failed: {exc}")
        return 1
    if args.json_out:
        write_json(Path(args.json_out), payload)
    print(f"[jules] approve-plan ok: {session_name}")
    return 0


def command_send_message(args: argparse.Namespace) -> int:
    """Send follow-up message to a session conversation."""
    session_name = normalize_session_name(args.session_name)
    if not session_name:
        print("[jules] send-message failed: empty session name.")
        return 1
    try:
        client = _resolve_client(args)
        payload = client.send_message(session_name, message=args.message)
    except (ValueError, JulesAPIError) as exc:
        print(f"[jules] send-message failed: {exc}")
        return 1
    if args.json_out:
        write_json(Path(args.json_out), payload)
    print(f"[jules] send-message ok: {session_name}")
    return 0


def command_generate_suggestions(args: argparse.Namespace) -> int:
    """Trigger Jules session and generate schema-compatible suggestions artifacts."""
    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    report_dir = Path(args.report_dir).resolve()
    quality_report = Path(args.quality_report).resolve()
    schema_path = Path(args.schema).resolve() if args.schema else None
    report_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    load_env_defaults(project_root, override=False)

    branch = str(args.branch or resolve_git_branch(project_root)).strip() or "main"
    source = normalize_source(args.source or os.environ.get("JULES_SOURCE", ""))
    task = str(args.task).strip() or "quality-pipeline-jules"
    category = str(args.category).strip() or "pipeline"

    session_name: str | None = None
    session_payload: object = {}
    activity_payload: object = {}
    implemented: list[dict[str, Any]] = []
    suggested_next: list[dict[str, Any]] = []
    api_error: str | None = None

    if not os.environ.get("JULES_API_KEY"):
        suggested_next.append(
            {
                "id": "SUG-001",
                "severity": "HIGH",
                "summary": "Jules API key is missing in environment.",
                "rationale": "Set JULES_API_KEY in .env to enable automated Jules suggestions.",
                "files": ["py_rme_canary/.env", ".env"],
            }
        )
    elif not source:
        suggested_next.append(
            {
                "id": "SUG-002",
                "severity": "HIGH",
                "summary": "Jules source is missing in environment.",
                "rationale": "Set JULES_SOURCE in .env so local pipeline can target the correct repository source.",
                "files": ["py_rme_canary/.env", ".env"],
            }
        )
    else:
        try:
            config = resolve_config(
                project_root,
                source=source,
                branch=branch,
                timeout_seconds=float(args.timeout),
            )
            client = JulesClient(config)
            prompt = build_quality_prompt(
                report_text=read_quality_context(quality_report),
                task=task,
            )
            session_payload = client.create_session(
                prompt=prompt,
                source=config.source,
                branch=config.branch,
                require_plan_approval=bool(args.require_plan_approval),
                automation_mode=args.automation_mode,
            )
            write_json(report_dir / "jules_session.json", session_payload)

            if isinstance(session_payload, dict):
                session_name = normalize_session_name(str(session_payload.get("name", "")))
                if session_name:
                    try:
                        raw_activity_payload = client.get_latest_activity(session_name)
                        activity_payload = _extract_first_activity(raw_activity_payload)
                        write_json(report_dir / "jules_activity.json", activity_payload)
                        write_json(report_dir / "jules_activity_raw.json", raw_activity_payload)
                    except JulesAPIError as exc:
                        activity_payload = {"error": str(exc)}
                        write_json(report_dir / "jules_activity.json", activity_payload)

            implemented, suggested_next = extract_contract_from_activity(activity_payload)
        except (ValueError, JulesAPIError) as exc:
            api_error = str(exc)
            suggested_next.append(
                {
                    "id": "SUG-003",
                    "severity": "MED",
                    "summary": "Jules API call failed during local quality run.",
                    "rationale": truncate_text(str(exc), 300),
                    "files": ["py_rme_canary/scripts/jules_runner.py"],
                }
            )

    contract = build_fallback_contract(
        category=category,
        task=task,
        quality_report=quality_report,
        session_name=session_name,
        implemented=implemented,
        suggested_next=suggested_next,
    )
    if api_error:
        contract["api_error"] = api_error

    suggestions_json = output_dir / "suggestions.json"
    suggestions_md = output_dir / "suggestions.md"
    write_json(suggestions_json, contract)
    write_markdown_report(suggestions_md, contract, session_name=session_name)

    errors = validate_contract(contract, schema_path)
    if errors:
        write_json(report_dir / "jules_contract_validation.json", {"errors": errors, "path": str(suggestions_json)})
        for entry in errors:
            print(f"[jules] validation error: {entry}")
        if args.strict:
            return 1
    else:
        write_json(report_dir / "jules_contract_validation.json", {"errors": [], "path": str(suggestions_json)})

    print(f"[jules] suggestions written to {suggestions_json}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Jules local integration runner.")
    parser.add_argument("--project-root", default=".", help="Repository root path.")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout (seconds).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Validate Jules API connectivity.")
    check.add_argument("--source", default="", help="Jules source override.")
    check.add_argument("--branch", default="", help="Branch override.")
    check.add_argument("--json-out", default="", help="Optional json output file.")
    check.set_defaults(func=command_check)

    list_sources = subparsers.add_parser("list-sources", help="List Jules sources.")
    list_sources.add_argument("--source", default="", help="Ignored override; kept for interface compatibility.")
    list_sources.add_argument("--branch", default="", help="Branch override.")
    list_sources.add_argument("--page-size", default=100, type=int, help="Pagination size.")
    list_sources.add_argument("--page-token", default="", help="Optional page token.")
    list_sources.add_argument("--max-print", default=30, type=int, help="Max number of names printed.")
    list_sources.add_argument("--json-out", default="", help="Optional json output file.")
    list_sources.set_defaults(func=command_list_sources)

    list_sessions = subparsers.add_parser("list-sessions", help="List Jules sessions.")
    list_sessions.add_argument("--source", default="", help="Jules source override.")
    list_sessions.add_argument("--branch", default="", help="Branch override.")
    list_sessions.add_argument("--page-size", default=50, type=int, help="Pagination size.")
    list_sessions.add_argument("--page-token", default="", help="Optional page token.")
    list_sessions.add_argument("--max-print", default=30, type=int, help="Max number of sessions printed.")
    list_sessions.add_argument("--json-out", default="", help="Optional json output file.")
    list_sessions.set_defaults(func=command_list_sessions)

    status = subparsers.add_parser("session-status", help="Fetch session + latest activity.")
    status.add_argument("session_name", help="Session name/id (sessions/<id> or raw id).")
    status.add_argument("--source", default="", help="Jules source override.")
    status.add_argument("--branch", default="", help="Branch override.")
    status.add_argument("--json-out", default="", help="Optional json output file.")
    status.set_defaults(func=command_session_status)

    approve = subparsers.add_parser("approve-plan", help="Approve session plan.")
    approve.add_argument("session_name", help="Session name/id (sessions/<id> or raw id).")
    approve.add_argument("--source", default="", help="Jules source override.")
    approve.add_argument("--branch", default="", help="Branch override.")
    approve.add_argument("--json-out", default="", help="Optional json output file.")
    approve.set_defaults(func=command_approve_plan)

    send_message = subparsers.add_parser("send-message", help="Send message to session.")
    send_message.add_argument("session_name", help="Session name/id (sessions/<id> or raw id).")
    send_message.add_argument("message", help="Message text.")
    send_message.add_argument("--source", default="", help="Jules source override.")
    send_message.add_argument("--branch", default="", help="Branch override.")
    send_message.add_argument("--json-out", default="", help="Optional json output file.")
    send_message.set_defaults(func=command_send_message)

    generate = subparsers.add_parser("generate-suggestions", help="Create local suggestions artifacts.")
    generate.add_argument("--source", default="", help="Jules source override.")
    generate.add_argument("--branch", default="", help="Branch override.")
    generate.add_argument("--task", default="quality-pipeline-jules", help="Task label for the contract.")
    generate.add_argument("--category", default="pipeline", help="Contract category.")
    generate.add_argument(
        "--quality-report", default=".quality_reports/refactor_summary.md", help="Quality report path."
    )
    generate.add_argument("--output-dir", default="reports/jules", help="Output folder for suggestions.* files.")
    generate.add_argument("--report-dir", default=".quality_reports", help="Output folder for raw Jules payloads.")
    generate.add_argument("--schema", default=".github/jules/suggestions.schema.json", help="Suggestions schema path.")
    generate.add_argument("--automation-mode", default="", help="Optional Jules automationMode value.")
    generate.add_argument(
        "--require-plan-approval", action="store_true", help="Request plan approval in Jules session."
    )
    generate.add_argument("--strict", action="store_true", help="Return non-zero on validation/api failures.")
    generate.set_defaults(func=command_generate_suggestions)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
