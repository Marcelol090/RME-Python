"""PNG/BMP Export Dialog for RME.

Provides UI for exporting map to PNG with progress bar.

Layer: vis_layer (uses PyQt6)
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.logic_layer.png_exporter import ExportConfig, PNGExporter


class ExportWorker(QThread):
    """Background worker for PNG export."""

    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(bool)  # success

    def __init__(
        self,
        exporter: PNGExporter,
        path: str,
        config: Any,
        render_tile: Any,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._exporter = exporter
        self._path = path
        self._config = config
        self._render_tile = render_tile
        self._cancelled = False

    def run(self) -> None:
        def on_progress(current: int, total: int, message: str) -> bool:
            self.progress.emit(current, total, message)
            return not self._cancelled

        success = self._exporter.export(
            path=self._path,
            config=self._config,
            render_tile=self._render_tile,
            on_progress=on_progress,
        )
        self.finished.emit(success)

    def cancel(self) -> None:
        self._cancelled = True
        self._exporter.cancel()


class PNGExportDialog(QDialog):
    """Dialog for image export options with progress."""

    def __init__(
        self,
        parent: QWidget | None = None,
        session: Any = None,
    ) -> None:
        super().__init__(parent)
        self._session = session
        self._worker: ExportWorker | None = None

        self.setWindowTitle("Export Image")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Options group
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)

        # Z-level
        z_row = QHBoxLayout()
        z_row.addWidget(QLabel("Z-Level:"))
        self._z_spin = QSpinBox()
        self._z_spin.setRange(0, 15)
        self._z_spin.setValue(7)
        z_row.addWidget(self._z_spin)
        z_row.addStretch()
        options_layout.addLayout(z_row)

        # Format
        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Format:"))
        self._format_combo = QComboBox()
        self._format_combo.addItem("Single Image", "single")
        self._format_combo.addItem("Tiled (for large maps)", "tiled")
        format_row.addWidget(self._format_combo)
        format_row.addStretch()
        options_layout.addLayout(format_row)

        # Image type
        image_row = QHBoxLayout()
        image_row.addWidget(QLabel("Image Type:"))
        self._image_combo = QComboBox()
        self._image_combo.addItem("PNG (.png)", "PNG")
        self._image_combo.addItem("BMP (.bmp)", "BMP")
        image_row.addWidget(self._image_combo)
        image_row.addStretch()
        options_layout.addLayout(image_row)

        # Tile size
        tile_row = QHBoxLayout()
        tile_row.addWidget(QLabel("Tile Size (px):"))
        self._tile_size_spin = QSpinBox()
        self._tile_size_spin.setRange(8, 64)
        self._tile_size_spin.setValue(32)
        tile_row.addWidget(self._tile_size_spin)
        tile_row.addStretch()
        options_layout.addLayout(tile_row)

        # Chunk size (for tiled)
        chunk_row = QHBoxLayout()
        chunk_row.addWidget(QLabel("Chunk Size (tiles):"))
        self._chunk_size_spin = QSpinBox()
        self._chunk_size_spin.setRange(64, 512)
        self._chunk_size_spin.setValue(256)
        chunk_row.addWidget(self._chunk_size_spin)
        chunk_row.addStretch()
        options_layout.addLayout(chunk_row)

        layout.addWidget(options_group)

        # Memory estimate
        self._memory_label = QLabel("Estimated memory: calculating...")
        layout.addWidget(self._memory_label)

        # Progress section
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel("")
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

        # Buttons
        button_layout = QHBoxLayout()
        self._export_btn = QPushButton("Export...")
        self._export_btn.clicked.connect(self._on_export)
        button_layout.addWidget(self._export_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self._cancel_btn)

        layout.addLayout(button_layout)

        # Connect signals
        self._z_spin.valueChanged.connect(self._update_estimate)
        self._tile_size_spin.valueChanged.connect(self._update_estimate)
        self._format_combo.currentIndexChanged.connect(self._update_estimate)
        self._image_combo.currentIndexChanged.connect(self._update_estimate)

        self._update_estimate()

    def _update_estimate(self) -> None:
        """Update memory estimate."""
        from py_rme_canary.logic_layer.png_exporter import ExportConfig, get_default_exporter

        config = self._get_config()
        exporter = get_default_exporter()

        # Set bounds from session if available
        if self._session:
            try:
                w = getattr(self._session, "map_width", 2048) or 2048
                h = getattr(self._session, "map_height", 2048) or 2048
                exporter.set_map_bounds(0, 0, w, h)
            except Exception:
                exporter.set_map_bounds(0, 0, 2048, 2048)
        else:
            exporter.set_map_bounds(0, 0, 2048, 2048)

        mem_mb = exporter.estimate_memory_mb(config)

        if config.format == "tiled":
            self._memory_label.setText("Mode: Tiled (low memory usage)")
        elif mem_mb > 1000:
            self._memory_label.setText(f"⚠️ Est. memory: {mem_mb:.0f} MB - consider tiled export")
        else:
            self._memory_label.setText(f"Est. memory: {mem_mb:.1f} MB")

    def _get_config(self) -> Any:
        """Build export config from UI."""
        from py_rme_canary.logic_layer.png_exporter import ExportConfig

        return ExportConfig(
            z_level=int(self._z_spin.value()),
            tile_pixel_size=int(self._tile_size_spin.value()),
            chunk_size=int(self._chunk_size_spin.value()),
            format=str(self._format_combo.currentData()),
            image_format=str(self._image_combo.currentData()),
        )

    def _ensure_extension(self, path: str, extension: str) -> str:
        if not path:
            return path

        path_obj = Path(path)
        if path_obj.suffix:
            return path

        return f"{path}{extension}"

    def _on_export(self) -> None:
        """Handle export button click."""
        config = self._get_config()

        file_filter = "PNG Files (*.png)" if config.image_format == "PNG" else "BMP Files (*.bmp)"
        default_ext = ".png" if config.image_format == "PNG" else ".bmp"

        # Get save path
        if config.format == "tiled":
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Image Tiles", "", file_filter
            )
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Image", "", file_filter
            )

        if not path:
            return

        path = self._ensure_extension(path, default_ext)

        self._start_export(path, config)

    def _start_export(self, path: str, config: Any) -> None:
        """Start background export."""
        from py_rme_canary.logic_layer.png_exporter import get_default_exporter

        exporter = get_default_exporter()

        # Set bounds from session
        if self._session:
            try:
                w = getattr(self._session, "map_width", 2048) or 2048
                h = getattr(self._session, "map_height", 2048) or 2048
                exporter.set_map_bounds(0, 0, w, h)
            except Exception:
                exporter.set_map_bounds(0, 0, 2048, 2048)
        else:
            exporter.set_map_bounds(0, 0, 2048, 2048)

        # Create tile render callback
        def render_tile(x: int, y: int, z: int, tile_size: int) -> bytes | None:
            # Placeholder - this should be connected to actual renderer
            # Returns 32x32 black transparent tile
            return None

        # Show progress UI
        self._progress_bar.setVisible(True)
        self._status_label.setVisible(True)
        self._export_btn.setEnabled(False)

        # Start worker
        self._worker = ExportWorker(exporter, path, config, render_tile, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, current: int, total: int, message: str) -> None:
        """Update progress bar."""
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)
        self._status_label.setText(message)

    def _on_finished(self, success: bool) -> None:
        """Handle export completion."""
        self._progress_bar.setVisible(False)
        self._status_label.setVisible(False)
        self._export_btn.setEnabled(True)
        self._worker = None

        if success:
            QMessageBox.information(self, "Export Complete", "Image export completed successfully!")
            self.accept()
        else:
            QMessageBox.warning(self, "Export Failed", "Image export was cancelled or failed.")

    def _on_cancel(self) -> None:
        """Handle cancel button."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()
        self.reject()

    def closeEvent(self, event: Any) -> None:
        """Handle dialog close."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()
        event.accept()
