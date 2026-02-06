from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.renderer.map_drawer import MapDrawer, RenderBackend


class Drawer(Protocol):
    """Base protocol for all render drawers."""

    def draw(self, drawer: "MapDrawer", backend: "RenderBackend", *args: Any, **kwargs: Any) -> None:
        """Draw content."""
        ...
