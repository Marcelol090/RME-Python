"""
New Map Dialog for creating maps with template presets.

Enhanced to match C++ RME Redux new map dialog:
- Client version selector
- OTBM format selection (1-4 ServerID vs 5-6 ClientID)
- Template/size/metadata with responsive layout
- Icons and better grouping
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QWidget,
)

from py_rme_canary.logic_layer.templates import (
    ALL_TEMPLATES,
    COMMON_MAP_SIZES,
    MapSize,
    MapTemplate,
)
from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog
from py_rme_canary.vis_layer.ui.theme import get_theme_manager

# Known client versions (matching C++ RME Redux enumeration)
_CLIENT_VERSIONS: list[tuple[int, str]] = [
    (0, "Auto-detect"),
    (740, "7.40"),
    (760, "7.60"),
    (800, "8.00"),
    (810, "8.10"),
    (820, "8.20"),
    (840, "8.40"),
    (850, "8.50"),
    (854, "8.54"),
    (860, "8.60"),
    (870, "8.70"),
    (910, "9.10"),
    (920, "9.20"),
    (960, "9.60"),
    (1010, "10.10"),
    (1077, "10.77"),
    (1098, "10.98"),
    (1290, "12.90"),
    (1310, "13.10"),
    (1320, "13.20"),
    (1330, "13.30"),
]


class NewMapDialog(ModernDialog):
    """Dialog for creating new maps with template support.

    Enhanced to match C++ RME Redux with client version & OTBM format selection.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, title="Create New Map")
        self.setMinimumWidth(540)
        self.setMinimumHeight(480)
        self.resize(580, 560)

        self._selected_template: MapTemplate | None = None
        self._selected_size: MapSize | None = None

        self._setup_content()
        self._setup_footer()
        self._connect_signals()
        self._load_defaults()
        self._apply_styles()

    def _setup_content(self) -> None:
        """Setup dialog UI inside ModernDialog content area."""
        layout = self.content_layout

        # --- Client Version & Format ---
        version_group = QGroupBox("Client Version && Format")
        version_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        version_layout = QFormLayout()
        version_layout.setSpacing(8)

        self._client_version_combo = QComboBox()
        for vid, vlabel in _CLIENT_VERSIONS:
            self._client_version_combo.addItem(f"Client {vlabel}" if vid > 0 else vlabel, vid)
        version_layout.addRow("Client version:", self._client_version_combo)

        # OTBM format radio buttons (like C++ uses map version flags)
        format_row = QHBoxLayout()
        self._otbm_classic = QRadioButton("OTBM 1-4 (ServerID)")
        self._otbm_classic.setToolTip("Traditional format. Items stored by ServerID. Used by TFS/OTServ.")
        self._otbm_classic.setChecked(True)
        format_row.addWidget(self._otbm_classic)
        self._otbm_canary = QRadioButton("OTBM 5-6 (ClientID)")
        self._otbm_canary.setToolTip("Modern format. Items stored by ClientID. Used by Canary Server.")
        format_row.addWidget(self._otbm_canary)
        format_row.addStretch()
        version_layout.addRow("Map format:", format_row)

        version_group.setLayout(version_layout)
        layout.addWidget(version_group)

        # --- Template selection ---
        template_group = QGroupBox("Map Template")
        template_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        template_layout = QFormLayout()
        template_layout.setSpacing(8)

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

        # --- Map size ---
        size_group = QGroupBox("Map Size")
        size_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        size_layout = QFormLayout()
        size_layout.setSpacing(8)

        self._size_combo = QComboBox()
        for size in COMMON_MAP_SIZES:
            self._size_combo.addItem(size.name, size)
        self._size_combo.addItem("Custom...", None)
        size_layout.addRow("Size:", self._size_combo)

        custom_layout = QHBoxLayout()
        self._width_spin = QSpinBox()
        self._width_spin.setRange(512, 65535)
        self._width_spin.setSingleStep(512)
        self._width_spin.setValue(2048)
        custom_layout.addWidget(QLabel("W:"))
        custom_layout.addWidget(self._width_spin)

        self._height_spin = QSpinBox()
        self._height_spin.setRange(512, 65535)
        self._height_spin.setSingleStep(512)
        self._height_spin.setValue(2048)
        custom_layout.addWidget(QLabel("H:"))
        custom_layout.addWidget(self._height_spin)
        custom_layout.addStretch()
        size_layout.addRow("Dimensions:", custom_layout)

        self._width_spin.setEnabled(False)
        self._height_spin.setEnabled(False)

        size_group.setLayout(size_layout)
        layout.addWidget(size_group)

        # --- Metadata ---
        metadata_group = QGroupBox("Map Metadata")
        metadata_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        metadata_layout = QFormLayout()
        metadata_layout.setSpacing(8)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Unnamed Map")
        metadata_layout.addRow("Name:", self._name_edit)

        self._author_edit = QLineEdit()
        self._author_edit.setPlaceholderText("Unknown")
        metadata_layout.addRow("Author:", self._author_edit)

        self._description_edit = QTextEdit()
        self._description_edit.setMaximumHeight(70)
        self._description_edit.setPlaceholderText("Map description...")
        metadata_layout.addRow("Description:", self._description_edit)

        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)

    def _setup_footer(self) -> None:
        self.add_spacer_to_footer()
        self.add_button("Cancel", callback=self.reject)
        self.add_button("Create Map", callback=self.accept, role="primary")

    def _apply_styles(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        # Template description styling
        self._template_desc.setStyleSheet(f"color: {c['text']['tertiary']}; font-style: italic;")

        # Custom overrides for specific New NewMapDialog elements to match Stitch design
        self.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["lg"]}px;
                margin-top: 24px;
                padding-top: 24px;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: {c["text"]["secondary"]};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
                background-color: transparent; 
            }}

            QLabel {{
                color: {c["text"]["secondary"]};
            }}

            /* Primary Action Button (Create) */
            QPushButton[role="primary"] {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c["brand"]["primary"]}, stop:1 {c["brand"]["secondary"]});
                color: white;
                border: none;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 0.5px;
                padding: 10px 24px;
            }}
            
            QPushButton[role="primary"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c["brand"]["secondary"]}, stop:1 {c["brand"]["active"]});
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self._template_combo.currentIndexChanged.connect(self._on_template_changed)
        self._size_combo.currentIndexChanged.connect(self._on_size_changed)
        self._client_version_combo.currentIndexChanged.connect(self._on_client_version_changed)

    def _load_defaults(self) -> None:
        """Load default values."""
        if self._template_combo.count() > 0:
            self._template_combo.setCurrentIndex(0)
            self._on_template_changed(0)

    def _on_client_version_changed(self, index: int) -> None:
        """Auto-select OTBM format based on client version."""
        vid = self._client_version_combo.itemData(index)
        if vid is not None and int(vid) >= 1200:
            # Modern Canary-era clients default to OTBM 5/6 ClientID
            self._otbm_canary.setChecked(True)
        elif vid is not None and int(vid) > 0:
            self._otbm_classic.setChecked(True)

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
        template = self.get_template()
        return template.default_description

    def get_client_version(self) -> int:
        """Get selected client version (0 = auto-detect)."""
        return int(self._client_version_combo.currentData() or 0)

    def is_canary_format(self) -> bool:
        """Check if OTBM 5/6 (ClientID) format is selected."""
        return self._otbm_canary.isChecked()

    def get_otbm_version(self) -> int:
        """Return OTBM version hint (4 for classic, 6 for canary)."""
        return 6 if self.is_canary_format() else 4
