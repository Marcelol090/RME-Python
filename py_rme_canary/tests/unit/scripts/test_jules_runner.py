from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import jules_api  # type: ignore[import-not-found]
import jules_runner  # type: ignore[import-not-found]


def test_load_env_defaults_from_project_root(tmp_path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("JULES_API_KEY=test-key\nJULES_SOURCE=my-repo\n", encoding="utf-8")

    monkeypatch.delenv("JULES_API_KEY", raising=False)
    monkeypatch.delenv("JULES_SOURCE", raising=False)

    loaded = jules_api.load_env_defaults(tmp_path, override=False)
    assert loaded["JULES_API_KEY"] == "test-key"
    assert loaded["JULES_SOURCE"] == "my-repo"
    assert jules_api.normalize_source(loaded["JULES_SOURCE"]) == "sources/my-repo"


def test_generate_suggestions_without_key_creates_contract(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("JULES_API_KEY", raising=False)
    monkeypatch.delenv("JULES_SOURCE", raising=False)

    quality_report = tmp_path / ".quality_reports" / "refactor_summary.md"
    quality_report.parent.mkdir(parents=True, exist_ok=True)
    quality_report.write_text("# report\n", encoding="utf-8")

    schema_path = tmp_path / ".github" / "jules" / "suggestions.schema.json"
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(
        json.dumps(
            {
                "required": ["version", "category", "implemented", "suggested_next", "generated_at"],
                "properties": {"category": {"enum": ["quality", "security", "tests", "pipeline", "general"]}},
            }
        ),
        encoding="utf-8",
    )

    output_dir = tmp_path / "reports" / "jules"
    report_dir = tmp_path / ".quality_reports"
    exit_code = jules_runner.main(
        [
            "--project-root",
            str(tmp_path),
            "generate-suggestions",
            "--quality-report",
            str(quality_report),
            "--output-dir",
            str(output_dir),
            "--report-dir",
            str(report_dir),
            "--schema",
            str(schema_path),
        ]
    )

    assert exit_code == 0
    suggestions_json = output_dir / "suggestions.json"
    suggestions_md = output_dir / "suggestions.md"
    assert suggestions_json.exists()
    assert suggestions_md.exists()

    payload = json.loads(suggestions_json.read_text(encoding="utf-8"))
    assert payload["category"] == "pipeline"
    assert isinstance(payload["implemented"], list)
    assert isinstance(payload["suggested_next"], list)
    assert payload["suggested_next"]


def test_extract_contract_from_activity_supports_jules_suggestions_block() -> None:
    activity = {
        "kind": "ACTIVITY_PLAN",
        "jules_suggestions": {
            "implemented": [{"id": "IMP-123", "summary": "Done", "files": ["a.py"]}],
            "suggestedNext": [{"id": "SUG-321", "priority": "high", "summary": "Do next"}],
        },
    }
    implemented, suggested = jules_runner.extract_contract_from_activity(activity)
    assert implemented and implemented[0]["id"] == "IMP-123"
    assert suggested and suggested[0]["id"] == "SUG-321"
    assert suggested[0]["severity"] == "HIGH"


def test_list_sources_command_uses_client_and_writes_json(tmp_path, monkeypatch) -> None:
    class FakeClient:
        def list_sources(self, *, page_size: int = 100, page_token: str = "") -> object:
            return {"sources": [{"name": "sources/github/org/repo"}], "nextPageToken": ""}

    def _fake_resolve_client(args, require_source: bool = True):  # noqa: ANN001
        return FakeClient()

    monkeypatch.setattr(jules_runner, "_resolve_client", _fake_resolve_client)
    out_path = tmp_path / "sources.json"
    args = SimpleNamespace(
        project_root=str(tmp_path),
        source="",
        branch="",
        timeout=30.0,
        page_size=100,
        page_token="",
        max_print=5,
        json_out=str(out_path),
    )
    exit_code = jules_runner.command_list_sources(args)
    assert exit_code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["sources"][0]["name"].startswith("sources/")


def test_session_status_command_normalizes_latest_activity(tmp_path, monkeypatch) -> None:
    class FakeClient:
        def get_session(self, session_name: str) -> object:
            return {"name": session_name, "state": "AWAITING_USER_INPUT"}

        def get_latest_activity(self, session_name: str) -> object:
            return {"activities": [{"type": "PLAN", "summary": "step 1"}]}

    def _fake_resolve_client(args, require_source: bool = True):  # noqa: ANN001
        return FakeClient()

    monkeypatch.setattr(jules_runner, "_resolve_client", _fake_resolve_client)
    out_path = tmp_path / "status.json"
    args = SimpleNamespace(
        project_root=str(tmp_path),
        source="sources/github/org/repo",
        branch="main",
        timeout=30.0,
        session_name="abc123",
        json_out=str(out_path),
    )
    exit_code = jules_runner.command_session_status(args)
    assert exit_code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["session"]["name"] == "sessions/abc123"
    assert payload["latest_activity"]["type"] == "PLAN"


def test_read_quality_context_compacts_artifacts_section(tmp_path) -> None:
    report_path = tmp_path / "refactor_summary.md"
    artifacts = "\n".join(f"- `quality_2026020{i:02d}.log`" for i in range(1, 40))
    report_path.write_text(
        (
            "# Relatório\n"
            "## 📊 Sumário Executivo\n"
            "- Issues Ruff: 0\n"
            "## 📁 Artefatos Gerados\n"
            f"{artifacts}\n"
            "## 🎯 Próximos Passos\n"
            "- Revisar segurança\n"
        ),
        encoding="utf-8",
    )

    context = jules_runner.read_quality_context(report_path, max_chars=900)
    assert "additional artifacts omitted for prompt compactness" in context
    assert context.count("quality_2026020") < 20
    assert "Próximos Passos" in context


def test_build_quality_prompt_contains_structured_contract() -> None:
    prompt = jules_runner.build_quality_prompt(report_text="ctx", task="quality-pipeline-jules")
    assert "single ```json fenced block" in prompt
    assert '"jules_suggestions"' in prompt
    assert "Task: quality-pipeline-jules" in prompt
    assert "<quality_report>" in prompt
    assert "Evidence -> Risk -> Action -> Verification" in prompt
