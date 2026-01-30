from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .project import MapMetadata, MapProject, normalize_engine


@dataclass(frozen=True, slots=True)
class DefinitionsConfig:
    items_otb: Path | None = None
    items_xml: Path | None = None
    brushes_json: Path | None = None  # Version-aware brush definitions
    detected_client_version: int | None = None  # Auto-detected from items.otb header
    detected_otbm_version: int | None = None  # OTBM version for ServerID/ClientID detection


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
        """Resolve definition files based on metadata (version-aware).

        Priority order for items.otb/items.xml:
        1. data/{client_version}/items.otb  (e.g., data/1310/items.otb)
        2. data/{engine}/items.otb          (e.g., data/canary/items.otb)
        3. data/{engine}/items/items.otb
        4. data/items/items.otb

        This matches RME's approach where each Tibia version gets its own folder.
        """
        root = Path(workspace_root)
        engine = normalize_engine(metadata.engine)
        client_version = int(metadata.client_version) if metadata.client_version else 0

        # Build candidate paths for items.otb (ServerID ↔ ClientID mapping)
        otb_candidates: list[Path] = []

        # Priority 1: Version-specific folder (e.g., data/1310/items.otb)
        if client_version > 0:
            otb_candidates.append(root / "data" / str(client_version) / "items.otb")

        # Priority 2: Engine-specific folder (e.g., data/canary/items.otb)
        if engine and engine != "unknown":
            otb_candidates.append(root / "data" / engine / "items.otb")
            otb_candidates.append(root / "data" / engine / "items" / "items.otb")

        # Priority 3: Generic folder
        otb_candidates.append(root / "data" / "items" / "items.otb")

        items_otb: Path | None = None
        detected_version: int | None = None

        for c in otb_candidates:
            if c.exists():
                items_otb = c
                # Try to extract client version from items.otb header
                try:
                    from ..database.items_otb import ItemsOTB

                    header = ItemsOTB.read_header(c)
                    detected_version = header.client_version
                except Exception:
                    pass  # Fall back to metadata version
                break

        # Build candidate paths for items.xml
        xml_candidates: list[Path] = []

        # Use detected version if metadata version was unknown
        effective_version = detected_version if detected_version and client_version == 0 else client_version

        # Priority 1: Version-specific folder (e.g., data/1310/items.xml)
        if effective_version > 0:
            xml_candidates.append(root / "data" / str(effective_version) / "items.xml")

        # Priority 2: Engine-specific folder
        if engine and engine != "unknown":
            xml_candidates.append(root / "data" / engine / "items.xml")
            xml_candidates.append(root / "data" / engine / "items" / "items.xml")

        # Priority 3: Generic folder
        xml_candidates.append(root / "data" / "items" / "items.xml")

        items_xml: Path | None = None
        for c in xml_candidates:
            if c.exists():
                items_xml = c
                break

        defs = DefinitionsConfig(
            items_otb=items_otb,
            items_xml=items_xml,
            brushes_json=root / "data" / "brushes.json" if (root / "data" / "brushes.json").exists() else None,
            detected_client_version=detected_version,
            detected_otbm_version=metadata.otbm_version,
        )
        return cls(metadata=metadata, definitions=defs)

    @staticmethod
    def infer_engine_from_client_version(client_version: int) -> str:
        return "canary" if int(client_version) >= ConfigurationManager.CLIENT_VERSION_THRESHOLD_CANARY else "tfs"

    @staticmethod
    def is_canary_format(otbm_version: int) -> bool:
        """Check if OTBM version uses ClientID format (Canary/modern format).

        OTBM versions 0-4 = ServerID format (traditional)
        OTBM versions 5-6 = ClientID format (Canary)
        """
        from ..constants import MapVersionID

        return int(otbm_version) >= int(MapVersionID.MAP_OTBM_5)

    @staticmethod
    def uses_client_id_as_server_id(otbm_version: int) -> bool:
        """Alias for is_canary_format for RME compatibility."""
        return ConfigurationManager.is_canary_format(otbm_version)

    def load_brushes(self) -> dict[str, Any] | None:
        """Load intelligent brush definitions based on version.

        Returns:
            Dictionary with brush definitions filtered for current version, or None
        """
        if not self._definitions.brushes_json or not self._definitions.brushes_json.exists():
            return None

        import json

        try:
            with open(self._definitions.brushes_json, encoding="utf-8") as f:
                brush_data = json.load(f)

            # Filter brushes based on format (ServerID vs ClientID)
            if self.is_canary_format(self._metadata.otbm_version):
                # Use client_id for Canary format
                for brush in brush_data.get("brushes", []):
                    if brush.get("client_id"):
                        brush["active_id"] = brush["client_id"]
                    elif brush.get("server_id"):
                        brush["active_id"] = brush["server_id"]
            else:
                # Use server_id for traditional format
                for brush in brush_data.get("brushes", []):
                    if brush.get("server_id"):
                        brush["active_id"] = brush["server_id"]
                    elif brush.get("client_id"):
                        brush["active_id"] = brush["client_id"]

            return brush_data
        except Exception as e:
            print(f"Warning: Could not load brush definitions: {e}")
            return None

    def get_brush_by_name(self, brush_name: str) -> dict[str, Any] | None:
        """Get a specific brush by name with version-aware ID selection.

        Returns:
            Brush definition with 'active_id' set to appropriate ID for current version
        """
        brushes = self.load_brushes()
        if not brushes:
            return None

        for brush in brushes.get("brushes", []):
            if brush.get("name", "").lower() == brush_name.lower():
                return brush

        return None
