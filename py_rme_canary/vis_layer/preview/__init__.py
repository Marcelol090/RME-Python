"""In-game preview window (pygame-based)."""

from typing import Any

__all__ = ["PreviewController", "PreviewSnapshot", "PreviewViewport"]


def __getattr__(name: str) -> Any:
	if name == "PreviewController":
		from .preview_controller import PreviewController

		return PreviewController
	if name in {"PreviewSnapshot", "PreviewViewport"}:
		from .preview_renderer import PreviewSnapshot, PreviewViewport

		return PreviewSnapshot if name == "PreviewSnapshot" else PreviewViewport
	raise AttributeError(name)