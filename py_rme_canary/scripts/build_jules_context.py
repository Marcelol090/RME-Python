#!/usr/bin/env python3
"""Build Jules PR context snapshot files used by Codex review workflows."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

DEFAULT_API_URL = "https://api.github.com"
JULES_LOGIN = "google-labs-jules"

try:
    from datetime import UTC
except ImportError:
    UTC = UTC


class GithubAPIError(RuntimeError):
    """Raised when GitHub API replies with HTTP/network errors."""

    def __init__(self, message: str, *, status: int | None = None, payload: object | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.payload = payload


@dataclass(frozen=True, slots=True)
class GithubRepoRef:
    """Repository coordinates used to fetch PR context."""

    owner: str
    repo: str
    pr_number: int
    token: str
    api_base_url: str = DEFAULT_API_URL


def utc_now_iso() -> str:
    """Return UTC timestamp in compact ISO-8601 format."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def truncate_text(value: str, limit: int = 300) -> str:
    """Trim text for context report readability."""
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def _decode_json(raw_data: bytes) -> object:
    text = raw_data.decode("utf-8", errors="replace").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def _build_url(base: str, path: str, query: dict[str, Any] | None = None) -> str:
    normalized_path = path if path.startswith("/") else f"/{path}"
    base_url = base.rstrip("/")
    url = f"{base_url}{normalized_path}"
    if query:
        url = f"{url}?{urlencode(query, doseq=True)}"
    return url


def _extract_next_link(link_header: str) -> str | None:
    parts = [chunk.strip() for chunk in link_header.split(",") if chunk.strip()]
    for part in parts:
        if 'rel="next"' not in part:
            continue
        if not part.startswith("<") or ">" not in part:
            continue
        return part[1 : part.index(">")]
    return None


def _validate_https_api_url(url: str) -> None:
    parsed = urlparse(str(url))
    scheme = str(parsed.scheme or "").lower()
    if scheme != "https":
        raise GithubAPIError(f"Refusing non-HTTPS URL: {url}")


def github_get(url: str, *, token: str, timeout_seconds: float = 30.0) -> tuple[object, str | None]:
    """Execute a GitHub API GET request and return JSON payload plus next link."""
    _validate_https_api_url(url)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "py-rme-codex-jules-context/1.0",
    }
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # nosec B310 - URL is validated as HTTPS
            body = response.read()
            payload = _decode_json(body)
            next_url = _extract_next_link(response.headers.get("Link", ""))
            return payload, next_url
    except HTTPError as exc:
        payload = _decode_json(exc.read()) if exc.fp else {}
        raise GithubAPIError(
            f"GitHub API HTTP error {exc.code}",
            status=int(exc.code),
            payload=payload,
        ) from exc
    except URLError as exc:
        raise GithubAPIError(f"GitHub API network error: {exc.reason}") from exc


def github_get_all_pages(
    *,
    repo_ref: GithubRepoRef,
    path: str,
    per_page: int = 100,
    max_items: int = 300,
) -> list[dict[str, Any]]:
    """Fetch paginated list endpoints from GitHub API."""
    results: list[dict[str, Any]] = []
    next_url: str | None = _build_url(
        repo_ref.api_base_url,
        path,
        query={"per_page": int(per_page)},
    )
    while next_url and len(results) < max_items:
        payload, resolved_next = github_get(next_url, token=repo_ref.token)
        if not isinstance(payload, list):
            break
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            results.append(entry)
            if len(results) >= max_items:
                break
        next_url = resolved_next
    return results


def get_pr_context(repo_ref: GithubRepoRef) -> dict[str, Any]:
    """Fetch PR metadata + discussion context from GitHub."""
    pr_path = f"/repos/{repo_ref.owner}/{repo_ref.repo}/pulls/{repo_ref.pr_number}"
    issue_comments_path = f"/repos/{repo_ref.owner}/{repo_ref.repo}/issues/{repo_ref.pr_number}/comments"
    review_comments_path = f"/repos/{repo_ref.owner}/{repo_ref.repo}/pulls/{repo_ref.pr_number}/comments"
    files_path = f"/repos/{repo_ref.owner}/{repo_ref.repo}/pulls/{repo_ref.pr_number}/files"
    commits_path = f"/repos/{repo_ref.owner}/{repo_ref.repo}/pulls/{repo_ref.pr_number}/commits"

    pr_payload, _ = github_get(_build_url(repo_ref.api_base_url, pr_path), token=repo_ref.token)
    if not isinstance(pr_payload, dict):
        raise GithubAPIError("Unexpected PR payload format.")

    issue_comments = github_get_all_pages(repo_ref=repo_ref, path=issue_comments_path, max_items=400)
    review_comments = github_get_all_pages(repo_ref=repo_ref, path=review_comments_path, max_items=400)
    changed_files = github_get_all_pages(repo_ref=repo_ref, path=files_path, max_items=400)
    commits = github_get_all_pages(repo_ref=repo_ref, path=commits_path, max_items=200)

    return {
        "generated_at": utc_now_iso(),
        "pr": pr_payload,
        "issue_comments": issue_comments,
        "review_comments": review_comments,
        "changed_files": changed_files,
        "commits": commits,
    }


def filter_comments_by_author(comments: list[dict[str, Any]], author_login: str) -> list[dict[str, Any]]:
    """Return comments authored by the target GitHub user."""
    selected: list[dict[str, Any]] = []
    target = str(author_login).strip().lower()
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        login = str(comment.get("user", {}).get("login", "")).strip().lower()
        if login == target:
            selected.append(comment)
    return selected


def summarize_changed_files(files: list[dict[str, Any]], *, max_items: int = 60) -> dict[str, Any]:
    """Build aggregate stats for changed files in the PR."""
    shown = files[:max_items]
    status_counts: dict[str, int] = {}
    additions = 0
    deletions = 0
    changes = 0
    for entry in files:
        if not isinstance(entry, dict):
            continue
        status = str(entry.get("status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1
        additions += int(entry.get("additions", 0) or 0)
        deletions += int(entry.get("deletions", 0) or 0)
        changes += int(entry.get("changes", 0) or 0)
    return {
        "total_files": len(files),
        "status_counts": status_counts,
        "additions": additions,
        "deletions": deletions,
        "changes": changes,
        "shown_files": shown,
        "truncated": len(files) > len(shown),
    }


def render_markdown_snapshot(context: dict[str, Any]) -> str:
    """Render a markdown context file consumed by Codex workflow."""
    pr = context.get("pr", {})
    if not isinstance(pr, dict):
        pr = {}
    issue_comments = context.get("issue_comments", [])
    review_comments = context.get("review_comments", [])
    commits = context.get("commits", [])
    changed_files = context.get("changed_files", [])
    if not isinstance(issue_comments, list):
        issue_comments = []
    if not isinstance(review_comments, list):
        review_comments = []
    if not isinstance(commits, list):
        commits = []
    if not isinstance(changed_files, list):
        changed_files = []

    jules_issue_comments = filter_comments_by_author(issue_comments, JULES_LOGIN)
    jules_review_comments = filter_comments_by_author(review_comments, JULES_LOGIN)
    file_summary = summarize_changed_files(changed_files, max_items=80)

    lines = [
        "# Jules PR Context Snapshot",
        "",
        f"- Generated at: `{context.get('generated_at', '')}`",
        f"- PR: `#{pr.get('number', '')}`",
        f"- Title: {truncate_text(str(pr.get('title', '')), 220)}",
        f"- Author: `{pr.get('user', {}).get('login', '')}`",
        f"- Base -> Head: `{pr.get('base', {}).get('ref', '')}` -> `{pr.get('head', {}).get('ref', '')}`",
        f"- Draft: `{pr.get('draft', False)}`",
        "",
        "## PR Body",
        "",
        str(pr.get("body", "") or "_(empty)_"),
        "",
        "## Changed Files Summary",
        "",
        f"- Total files: `{file_summary.get('total_files', 0)}`",
        f"- Additions: `{file_summary.get('additions', 0)}`",
        f"- Deletions: `{file_summary.get('deletions', 0)}`",
        f"- Total line changes: `{file_summary.get('changes', 0)}`",
    ]

    status_counts = file_summary.get("status_counts", {})
    if isinstance(status_counts, dict) and status_counts:
        status_line = ", ".join(f"{key}={value}" for key, value in sorted(status_counts.items()))
        lines.append(f"- Status counts: `{status_line}`")

    shown_files = file_summary.get("shown_files", [])
    if isinstance(shown_files, list) and shown_files:
        lines.append("")
        lines.append("## Changed Files (sample)")
        lines.append("")
        for entry in shown_files:
            if not isinstance(entry, dict):
                continue
            filename = str(entry.get("filename", ""))
            status = str(entry.get("status", ""))
            additions = int(entry.get("additions", 0) or 0)
            deletions = int(entry.get("deletions", 0) or 0)
            lines.append(f"- `{filename}` [{status}] (+{additions}/-{deletions})")
        if file_summary.get("truncated"):
            lines.append("- _(truncated list)_")

    lines.extend(["", "## Jules Issue Comments", ""])
    if jules_issue_comments:
        for comment in jules_issue_comments[-20:]:
            created_at = str(comment.get("created_at", ""))
            body = truncate_text(str(comment.get("body", "")).strip(), 1800)
            lines.extend([f"### {created_at}", "", body or "_(empty)_", ""])
    else:
        lines.append("No Jules issue comments found.")
        lines.append("")

    lines.extend(["## Jules Review Comments", ""])
    if jules_review_comments:
        for comment in jules_review_comments[-20:]:
            created_at = str(comment.get("created_at", ""))
            body = truncate_text(str(comment.get("body", "")).strip(), 1800)
            path = str(comment.get("path", ""))
            line = comment.get("line")
            location = f" ({path}:{line})" if path and line else (f" ({path})" if path else "")
            lines.extend([f"### {created_at}{location}", "", body or "_(empty)_", ""])
    else:
        lines.append("No Jules review comments found.")
        lines.append("")

    lines.extend(["## Recent Commits", ""])
    if commits:
        for commit in commits[-20:]:
            if not isinstance(commit, dict):
                continue
            sha = str(commit.get("sha", ""))[:8]
            message = str(commit.get("commit", {}).get("message", "")).splitlines()[0]
            author = str(
                commit.get("author", {}).get("login") or commit.get("commit", {}).get("author", {}).get("name", "")
            )
            lines.append(f"- `{sha}` by `{author}`: {truncate_text(message, 180)}")
    else:
        lines.append("No commits found.")

    lines.append("")
    return "\n".join(lines)


def write_snapshot_files(*, context: dict[str, Any], markdown_path: Path, json_path: Path) -> None:
    """Write context snapshot to markdown + json files."""
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown_snapshot(context), encoding="utf-8")
    json_path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Jules PR context snapshot files.")
    parser.add_argument("--owner", required=True, help="GitHub repository owner.")
    parser.add_argument("--repo", required=True, help="GitHub repository name.")
    parser.add_argument("--pr-number", required=True, type=int, help="Pull request number.")
    parser.add_argument("--token", default="", help="GitHub token (default: GITHUB_TOKEN env var).")
    parser.add_argument("--api-base-url", default=DEFAULT_API_URL, help="GitHub API base URL.")
    parser.add_argument("--out-md", default=".codex_context/jules_pr_context.md", help="Markdown output path.")
    parser.add_argument("--out-json", default=".codex_context/jules_pr_context.json", help="JSON output path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    token = str(args.token or os.environ.get("GITHUB_TOKEN", "")).strip()
    if not token:
        print("[jules-context] missing GitHub token.")
        return 1

    repo_ref = GithubRepoRef(
        owner=str(args.owner).strip(),
        repo=str(args.repo).strip(),
        pr_number=int(args.pr_number),
        token=token,
        api_base_url=str(args.api_base_url).strip() or DEFAULT_API_URL,
    )

    try:
        context = get_pr_context(repo_ref)
    except GithubAPIError as exc:
        print(f"[jules-context] failed: {exc}")
        if exc.status is not None:
            print(f"[jules-context] http_status={exc.status}")
        return 2

    markdown_path = Path(args.out_md).resolve()
    json_path = Path(args.out_json).resolve()
    write_snapshot_files(context=context, markdown_path=markdown_path, json_path=json_path)
    print(f"[jules-context] snapshot written: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
