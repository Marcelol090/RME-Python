#!/usr/bin/env python3
"""
Monorepo Discovery & Workspace Manager - v2.2.0
Nx/Turborepo-compatible workspace detection
"""

import argparse
import json
import logging
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

import yaml

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


@dataclass
class Workspace:
    """Single project in monorepo"""

    name: str
    path: Path
    config: dict[str, Any]
    dependencies: list[str] = field(default_factory=list)
    language: str = "python"


class MonorepoScanner:
    """Detect and parse monorepo structures"""

    WORKSPACE_PATTERNS: ClassVar[list[str]] = [
        "quality.yaml",  # Quality pipeline config
        "pyproject.toml",  # Python project
        "package.json",  # Node.js project
        "Cargo.toml",  # Rust project
        "go.mod",  # Go project
    ]

    def __init__(self, root: Path):
        self.root = root.resolve()

    def scan(self) -> list[Workspace]:
        """Discover all workspaces in monorepo"""

        log.info(f"Scanning monorepo: {self.root}")

        # Check if root is monorepo
        monorepo_type = self._detect_monorepo_type()

        if monorepo_type == "single":
            log.info("Single project detected (not a monorepo)")
            return [self._create_workspace(self.root)]

        log.info(f"Monorepo type: {monorepo_type}")

        # Find workspaces
        workspaces = []

        if monorepo_type == "nx":
            workspaces = self._scan_nx_workspace()
        elif monorepo_type == "turborepo":
            workspaces = self._scan_turborepo_workspace()
        elif monorepo_type == "poetry":
            workspaces = self._scan_poetry_workspace()
        elif monorepo_type == "custom":
            workspaces = self._scan_custom_workspace()

        log.info(f"Discovered {len(workspaces)} workspace(s)")

        return workspaces

    def _detect_monorepo_type(self) -> str:
        """Detect monorepo manager type"""

        if (self.root / "nx.json").exists():
            return "nx"

        if (self.root / "turbo.json").exists():
            return "turborepo"

        if (self.root / "pyproject.toml").exists():
            with open(self.root / "pyproject.toml") as f:
                content = f.read()
                if "[tool.poetry]" in content and "packages" in content:
                    return "poetry"

        # Check for common monorepo structure
        potential_packages = ["packages", "apps", "libs", "projects"]
        if any((self.root / p).is_dir() for p in potential_packages):
            return "custom"

        return "single"

    def _scan_nx_workspace(self) -> list[Workspace]:
        """Scan Nx monorepo structure"""

        _ = json.loads((self.root / "nx.json").read_text())
        workspaces = []

        # Nx uses workspace.json or project.json files
        if (self.root / "workspace.json").exists():
            workspace_config = json.loads((self.root / "workspace.json").read_text())
            projects = workspace_config.get("projects", {})

            for name, project_path in projects.items():
                full_path = self.root / project_path
                if full_path.exists():
                    workspace = self._create_workspace(full_path, name)
                    workspaces.append(workspace)

        return workspaces

    def _scan_turborepo_workspace(self) -> list[Workspace]:
        """Scan Turborepo structure"""

        _ = json.loads((self.root / "turbo.json").read_text())

        # Turborepo uses package.json workspaces
        if (self.root / "package.json").exists():
            pkg = json.loads((self.root / "package.json").read_text())
            workspace_patterns = pkg.get("workspaces", [])

            workspaces = []
            for pattern in workspace_patterns:
                # Resolve glob pattern
                for workspace_dir in self._glob_workspaces(pattern):
                    workspace = self._create_workspace(workspace_dir)
                    workspaces.append(workspace)

            return workspaces

        return []

    def _scan_poetry_workspace(self) -> list[Workspace]:
        """Scan Poetry monorepo"""

        pyproject = Path(self.root / "pyproject.toml")

        # Parse TOML manually (lightweight)
        workspaces = []

        with open(pyproject) as f:
            content = f.read()

            # Simple TOML parsing for packages list
            if "packages = [" in content:
                start = content.index("packages = [") + 12
                end = content.index("]", start)
                packages_str = content[start:end]

                # Extract package paths
                for line in packages_str.split(","):
                    pkg_path = line.strip().strip("\"'")
                    if pkg_path:
                        full_path = self.root / pkg_path
                        if full_path.exists():
                            workspace = self._create_workspace(full_path)
                            workspaces.append(workspace)

        return workspaces

    def _scan_custom_workspace(self) -> list[Workspace]:
        """Scan custom monorepo structure"""

        workspaces = []

        # Search for workspace indicators in common dirs
        for search_dir in ["packages", "apps", "libs", "projects"]:
            search_path = self.root / search_dir

            if not search_path.exists():
                continue

            # Find subdirectories with config files
            for subdir in search_path.iterdir():
                if not subdir.is_dir():
                    continue

                # Check if it has workspace config
                if any((subdir / pattern).exists() for pattern in self.WORKSPACE_PATTERNS):
                    workspace = self._create_workspace(subdir)
                    workspaces.append(workspace)

        return workspaces

    def _create_workspace(self, path: Path, name: str | None = None) -> Workspace:
        """Create Workspace object from directory"""

        # Load quality config if exists
        quality_config_path = path / "quality.yaml"

        config = yaml.safe_load(quality_config_path.read_text()) if quality_config_path.exists() else {}

        # Detect language
        language = self._detect_language(path)

        # Extract dependencies from config
        dependencies = self._extract_dependencies(path, language)

        workspace_name = name or path.name

        return Workspace(name=workspace_name, path=path, config=config, dependencies=dependencies, language=language)

    def _detect_language(self, path: Path) -> str:
        """Detect primary language of workspace"""

        if (path / "pyproject.toml").exists() or (path / "setup.py").exists():
            return "python"

        if (path / "package.json").exists():
            return "typescript"

        if (path / "Cargo.toml").exists():
            return "rust"

        if (path / "go.mod").exists():
            return "go"

        return "unknown"

    def _extract_dependencies(self, path: Path, language: str) -> list[str]:
        """Extract workspace dependencies"""

        deps = []

        if language == "python" and (path / "pyproject.toml").exists():
            # Parse Python dependencies
            with open(path / "pyproject.toml") as f:
                content = f.read()

                # Simple extraction (not full TOML parse for speed)
                if "dependencies = [" in content:
                    start = content.index("dependencies = [") + 16
                    end = content.index("]", start)
                    deps_str = content[start:end]

                    for line in deps_str.split(","):
                        dep = line.strip().strip("\"'")
                        if dep and not dep.startswith("#"):
                            # Extract package name (before version specifier)
                            pkg_name = dep.split(">=")[0].split("==")[0].split("~=")[0].strip()
                            deps.append(pkg_name)

        return deps

    def _glob_workspaces(self, pattern: str) -> list[Path]:
        """Resolve workspace glob pattern"""

        # Simple glob support (no full fnmatch for speed)
        if "*" in pattern:
            base = pattern.split("*", maxsplit=1)[0]
            base_path = self.root / base

            if base_path.exists():
                return [p for p in base_path.iterdir() if p.is_dir()]

        return [self.root / pattern]


class WorkspaceOrchestrator:
    """Execute quality pipeline across monorepo workspaces"""

    def __init__(self, root: Path, config: dict[str, Any]):
        self.root = root
        self.config = config
        self.scanner = MonorepoScanner(root)

    def plan_execution(self) -> dict[str, Any]:
        """Create execution plan for all workspaces"""

        workspaces = self.scanner.scan()

        # Build dependency graph
        graph = self._build_dependency_graph(workspaces)

        # Topological sort for execution order
        execution_order = self._topological_sort(graph)

        plan = {
            "total_workspaces": len(workspaces),
            "execution_order": execution_order,
            "workspaces": {
                ws.name: {
                    "path": str(ws.path),
                    "language": ws.language,
                    "dependencies": ws.dependencies,
                    "config": ws.config,
                }
                for ws in workspaces
            },
        }

        return plan

    def _build_dependency_graph(self, workspaces: list[Workspace]) -> dict[str, list[str]]:
        """Build workspace dependency graph"""

        graph = {ws.name: [] for ws in workspaces}
        workspace_names = {ws.name for ws in workspaces}

        for workspace in workspaces:
            # Add internal workspace dependencies
            for dep in workspace.dependencies:
                if dep in workspace_names:
                    graph[workspace.name].append(dep)

        return graph

    def _topological_sort(self, graph: dict[str, list[str]]) -> list[str]:
        """Topological sort for execution order"""

        # Calculate in-degrees
        in_degree = dict.fromkeys(graph, 0)

        for deps in graph.values():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1

        # Find nodes with no dependencies
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            # Reduce in-degree for dependents
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(result) != len(graph):
            log.warning("Circular dependencies detected, using partial order")

        return result


def main():
    parser = argparse.ArgumentParser(description="Monorepo Discovery")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, help="Save plan to JSON")

    args = parser.parse_args()

    orchestrator = WorkspaceOrchestrator(args.root, {})
    plan = orchestrator.plan_execution()

    print(json.dumps(plan, indent=2))

    if args.output:
        args.output.write_text(json.dumps(plan, indent=2))
        log.info(f"Plan saved to {args.output}")


if __name__ == "__main__":
    main()
