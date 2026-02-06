from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_jules_context as context_builder  # type: ignore[import-not-found]


def test_filter_comments_by_author_returns_only_target() -> None:
    comments = [
        {"user": {"login": "google-labs-jules"}, "body": "plan"},
        {"user": {"login": "someone-else"}, "body": "ignore"},
        {"user": {"login": "Google-Labs-Jules"}, "body": "case-insensitive"},
    ]
    filtered = context_builder.filter_comments_by_author(comments, "google-labs-jules")
    assert len(filtered) == 2
    assert all(item["user"]["login"].lower() == "google-labs-jules" for item in filtered)


def test_summarize_changed_files_aggregates_totals() -> None:
    files = [
        {"filename": "a.py", "status": "modified", "additions": 10, "deletions": 2, "changes": 12},
        {"filename": "b.py", "status": "added", "additions": 5, "deletions": 0, "changes": 5},
    ]
    summary = context_builder.summarize_changed_files(files, max_items=1)
    assert summary["total_files"] == 2
    assert summary["additions"] == 15
    assert summary["deletions"] == 2
    assert summary["changes"] == 17
    assert summary["status_counts"] == {"modified": 1, "added": 1}
    assert len(summary["shown_files"]) == 1
    assert summary["truncated"] is True


def test_render_markdown_snapshot_contains_sections() -> None:
    context = {
        "generated_at": "2026-02-06T10:00:00+00:00",
        "pr": {
            "number": 42,
            "title": "Improve async Jules workflow",
            "body": "Implements monitor updates.",
            "draft": False,
            "user": {"login": "google-labs-jules"},
            "base": {"ref": "main"},
            "head": {"ref": "jules/task-42"},
        },
        "issue_comments": [
            {
                "created_at": "2026-02-06T10:01:00Z",
                "body": "Plan ready",
                "user": {"login": "google-labs-jules"},
            }
        ],
        "review_comments": [],
        "changed_files": [{"filename": "x.py", "status": "modified", "additions": 1, "deletions": 1, "changes": 2}],
        "commits": [{"sha": "abcdef1234", "author": {"login": "google-labs-jules"}, "commit": {"message": "feat: x"}}],
    }

    rendered = context_builder.render_markdown_snapshot(context)
    assert "# Jules PR Context Snapshot" in rendered
    assert "## PR Body" in rendered
    assert "## Changed Files Summary" in rendered
    assert "## Jules Issue Comments" in rendered
    assert "## Recent Commits" in rendered
    assert "Improve async Jules workflow" in rendered
