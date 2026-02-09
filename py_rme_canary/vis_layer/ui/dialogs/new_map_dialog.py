"""
New Map Dialog for creating maps with template presets.

Refactored to use ModernDialog and ThemeTokens.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from py_rme_canary.logic_layer.templates import (
    ALL_TEMPLATES,
    COMMON_MAP_SIZES,
    MapSize,
    MapTemplate,
)
from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog
from py_rme_canary.vis_layer.ui.theme import get_theme_manager


class NewMapDialog(ModernDialog):
    """Dialog for creating new maps with template support."""

    def __init__(self, parent=None):
        super().__init__(parent, title="Create New Map")
        self.setMinimumWidth(500)

        # Selected values
        self._selected_template: MapTemplate | None = None
        self._selected_size: MapSize | None = None

        self._setup_content() # Use custom method to populate content area
        self._setup_footer()
        self._connect_signals()
        self._load_defaults()

        # Apply theme-specific adjustments
        self._apply_styles()

    def _setup_content(self) -> None:
        """Setup dialog UI inside ModernDialog content area."""
        layout = self.content_layout # Use base class layout

        # Template selection group
        template_group = QGroupBox("Map Template")
        template_layout = QFormLayout()

        self._template_combo = QComboBox()
        for template in ALL_TEMPLATES:
            self._template_combo.addItem(template.name, template)
        template_layout.addRow("Version:", self._template_combo)

        self._template_desc = QLabel()
        self._template_desc.setWordWrap(True)
        self._template_desc.setObjectName("TemplateDesc")
        template_layout.addRow(self._template_desc)

        template_group.setLayout(template_layout)
        layout.addWidget(template_group)

        # Map size group
        size_group = QGroupBox("Map Size")
        size_layout = QFormLayout()

        self._size_combo = QComboBox()
        for size in COMMON_MAP_SIZES:
            self._size_combo.addItem(size.name, size)
        self._size_combo.addItem("Custom...", None)
        size_layout.addRow("Size:", self._size_combo)

        # Custom size inputs
        custom_layout = QHBoxLayout()
        self._width_spin = QSpinBox()
        self._width_spin.setRange(512, 65535)
        self._width_spin.setSingleStep(512)
        self._width_spin.setValue(2048)
        custom_layout.addWidget(QLabel("Width:"))
        custom_layout.addWidget(self._width_spin)

        self._height_spin = QSpinBox()
        self._height_spin.setRange(512, 65535)
        self._height_spin.setSingleStep(512)
        self._height_spin.setValue(2048)
        custom_layout.addWidget(QLabel("Height:"))
        custom_layout.addWidget(self._height_spin)
        custom_layout.addStretch()

        size_layout.addRow("Custom:", custom_layout)

        # Initially hide custom size
        self._width_spin.setEnabled(False)
        self._height_spin.setEnabled(False)

        size_group.setLayout(size_layout)
        layout.addWidget(size_group)

        # Map metadata group
        metadata_group = QGroupBox("Map Metadata")
        metadata_layout = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Unnamed Map")
        metadata_layout.addRow("Name:", self._name_edit)

        self._author_edit = QLineEdit()
        self._author_edit.setPlaceholderText("Unknown")
        metadata_layout.addRow("Author:", self._author_edit)

        self._description_edit = QTextEdit()
        self._description_edit.setMaximumHeight(80)
        self._description_edit.setPlaceholderText("Map description...")
        metadata_layout.addRow("Description:", self._description_edit)

        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)

    def _setup_footer(self):
        # Add buttons to ModernDialog footer
        self.add_spacer_to_footer()
        self.add_button("Cancel", callback=self.reject)
        self.add_button("Create Map", callback=self.accept, role="primary")

    def _apply_styles(self):
        tm = get_theme_manager()
        c = tm.tokens["color"]
        self._template_desc.setStyleSheet(f"color: {c['text']['tertiary']}; font-style: italic;")

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self._template_combo.currentIndexChanged.connect(self._on_template_changed)
        self._size_combo.currentIndexChanged.connect(self._on_size_changed)

    def _load_defaults(self) -> None:
        """Load default values."""
        # Select first template (7.4)
        if self._template_combo.count() > 0:
            self._template_combo.setCurrentIndex(0)
            self._on_template_changed(0)

    def _on_template_changed(self, index: int) -> None:
        """Handle template selection change."""
        template = self._template_combo.itemData(index)
        if template is None:
            return

        self._selected_template = template

        # Update description
        self._template_desc.setText(template.description)

        # Update default size
        for i in range(self._size_combo.count()):
            size = self._size_combo.itemData(i)
            if size == template.default_size:
                self._size_combo.setCurrentIndex(i)
                break

        # Update description placeholder
        self._description_edit.setPlaceholderText(template.default_description)

    def _on_size_changed(self, index: int) -> None:
        """Handle size selection change."""
        size = self._size_combo.itemData(index)

        if size is None:
            # Custom size selected
            self._width_spin.setEnabled(True)
            self._height_spin.setEnabled(True)
            self._selected_size = None
        else:
            # Preset size selected
            self._width_spin.setEnabled(False)
            self._height_spin.setEnabled(False)
            self._width_spin.setValue(size.width)
            self._height_spin.setValue(size.height)
            self._selected_size = size

    def get_template(self) -> MapTemplate:
        """Get selected template."""
        if self._selected_template is None:
            # Should not happen, but return first template as fallback
            return ALL_TEMPLATES[0]
        return self._selected_template

    def get_map_size(self) -> MapSize:
        """Get selected or custom map size."""
        if self._selected_size is not None:
            return self._selected_size
        # Custom size
        return MapSize(self._width_spin.value(), self._height_spin.value())

    def get_map_name(self) -> str:
        """Get map name."""
        name = self._name_edit.text().strip()
        return name if name else "Unnamed Map"

    def get_author(self) -> str:
        """Get author name."""
        author = self._author_edit.text().strip()
        return author if author else "Unknown"

    def get_description(self) -> str:
        """Get map description."""
        desc = self._description_edit.toPlainText().strip()
        if desc:
            return desc
        # Use template default
        template = self.get_template()
        return template.default_description
