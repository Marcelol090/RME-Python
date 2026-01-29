from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .project import MapMetadata, MapProject, normalize_engine


@dataclass(frozen=True, slots=True)
class DefinitionsConfig:
    items_otb: Path | None = None
    items_xml: Path | None = None


class ConfigurationError(ValueError):
    pass


class ConfigurationManager:
    """Resolves and tracks definition file paths based on engine/client_version."""

    CLIENT_VERSION_THRESHOLD_CANARY = 1300

    def __init__(self, *, metadata: MapMetadata, definitions: DefinitionsConfig):
        self._metadata = metadata
        self._definitions = definitions

    @property
    def metadata(self) -> MapMetadata:
        return self._metadata

    @property
    def definitions(self) -> DefinitionsConfig:
        return self._definitions

    @classmethod
    def from_project(cls, project: MapProject, *, project_path: str | Path) -> ConfigurationManager:
        base = Path(project_path).parent
        items_otb = Path(base / project.definitions.items_otb).resolve() if project.definitions.items_otb else None
        items_xml = Path(base / project.definitions.items_xml).resolve() if project.definitions.items_xml else None

        md = MapMetadata(
            engine=normalize_engine(project.engine),
            client_version=int(project.client_version),
            otbm_version=0,
            source="project",
        )
        return cls(metadata=md, definitions=DefinitionsConfig(items_otb=items_otb, items_xml=items_xml))

    @classmethod
    def from_sniff(cls, metadata: MapMetadata, *, workspace_root: str | Path) -> ConfigurationManager:
        root = Path(workspace_root)
        # Conservative defaults for this repo; project wrapper should override.
        # Legacy reference: engine selection drives which item definitions and
        # mappings are applied before interpreting tile/item ids.
        engine = normalize_engine(metadata.engine)

        # items.otb (preferred mapping source for classic pipelines)
        otb_candidates: list[Path] = []
        if engine and engine != "unknown":
            otb_candidates.append(root / "data" / engine / "items.otb")
            otb_candidates.append(root / "data" / engine / "items" / "items.otb")
        otb_candidates.append(root / "data" / "items" / "items.otb")

        items_otb: Path | None = None
        for c in otb_candidates:
            if c.exists():
                items_otb = c
                break

        candidates: list[Path] = []
        if engine and engine != "unknown":
            candidates.append(root / "data" / engine / "items.xml")
            candidates.append(root / "data" / engine / "items" / "items.xml")

        # Repo default layout.
        candidates.append(root / "data" / "items" / "items.xml")

        items_xml: Path | None = None
        for c in candidates:
            if c.exists():
                items_xml = c
                break

        defs = DefinitionsConfig(items_otb=items_otb, items_xml=items_xml)
        return cls(metadata=metadata, definitions=defs)

    @staticmethod
    def infer_engine_from_client_version(client_version: int) -> str:
        return "canary" if int(client_version) >= ConfigurationManager.CLIENT_VERSION_THRESHOLD_CANARY else "tfs"

    @staticmethod
    def get_app_config_path() -> Path:
        """Get path to global application config file."""
        # Defaults to current working directory for portable/dev usage
        return Path.cwd() / "config.toml"

    @staticmethod
    def load_app_settings() -> dict:
        """Load global application settings from config.toml."""
        path = ConfigurationManager.get_app_config_path()
        if not path.exists():
            return {}

        try:
            with open(path, "rb") as f:
                import tomllib

                return tomllib.load(f)
        except Exception:
            return {}

    @staticmethod
    def save_app_settings(settings: dict) -> None:
        """Save global application settings to config.toml."""
        path = ConfigurationManager.get_app_config_path()

        lines = []
        for k, v in settings.items():
            if isinstance(v, bool):
                val = str(v).lower()
            elif isinstance(v, (int, float)):
                val = str(v)
            elif isinstance(v, str):
                escaped = v.replace("\\", "\\\\").replace('"', '\\"')
                val = f'"{escaped}"'
            else:
                continue

            lines.append(f"{k} = {val}")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            f.write("\n")
