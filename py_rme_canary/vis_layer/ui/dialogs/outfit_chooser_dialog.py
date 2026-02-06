"""Outfit Chooser Dialog.

Full creature outfit editor matching C++ OutfitChooserDialog from Redux.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass

OUTFIT_COLORS: list[int] = [
    0xFFFFFF,
    0xFFD4BF,
    0xFFE9BF,
    0xFFFFBF,
    0xE9FFBF,
    0xD4FFBF,
    0xBFFFBF,
    0xBFFFD4,
    0xBFFFE9,
    0xBFFFFF,
    0xBFE9FF,
    0xBFD4FF,
    0xBFBFFF,
    0xD4BFFF,
    0xE9BFFF,
    0xFFBFFF,
    0xFFBFE9,
    0xFFBFD4,
    0xFFBFBF,
    0xDADADA,
    0xBF9F8F,
    0xBFAF8F,
    0xBFBF8F,
    0xAFBF8F,
    0x9FBF8F,
    0x8FBF8F,
    0x8FBF9F,
    0x8FBFAF,
    0x8FBFBF,
    0x8FAFBF,
    0x8F9FBF,
    0x8F8FBF,
    0x9F8FBF,
    0xAF8FBF,
    0xBF8FBF,
    0xBF8FAF,
    0xBF8F9F,
    0xBF8F8F,
    0xB6B6B6,
    0xA05F3F,
    0xA07F3F,
    0xA09F3F,
    0x7FA03F,
    0x5FA03F,
    0x3FA03F,
    0x3FA05F,
    0x3FA07F,
    0x3FA0A0,
    0x3F7FA0,
    0x3F5FA0,
    0x3F3FA0,
    0x5F3FA0,
    0x7F3FA0,
    0xA03FA0,
    0xA03F7F,
    0xA03F5F,
    0xA03F3F,
    0x919191,
    0x7F2F0F,
    0x7F4F0F,
    0x7F7F0F,
    0x4F7F0F,
    0x2F7F0F,
    0x0F7F0F,
    0x0F7F2F,
    0x0F7F4F,
    0x0F7F7F,
    0x0F4F7F,
    0x0F2F7F,
    0x0F0F7F,
    0x2F0F7F,
    0x4F0F7F,
    0x7F0F7F,
    0x7F0F4F,
    0x7F0F2F,
    0x7F0F0F,
    0x6D6D6D,
    0x600000,
    0x603000,
    0x606000,
    0x306000,
    0x006000,
    0x006000,
    0x006030,
    0x006060,
    0x006060,
    0x003060,
    0x000060,
    0x000060,
    0x300060,
    0x600060,
    0x600060,
    0x600030,
    0x600000,
    0x484848,
    0x400000,
    0x402000,
    0x404000,
    0x204000,
    0x004000,
    0x004000,
    0x004020,
    0x004040,
    0x004040,
    0x002040,
    0x000040,
    0x000040,
    0x200040,
    0x400040,
    0x400040,
    0x400020,
    0x400000,
    0x242424,
    0x200000,
    0x201000,
    0x202000,
    0x102000,
    0x002000,
    0x002000,
    0x002010,
    0x002020,
    0x002020,
    0x001020,
    0x000020,
    0x000020,
    0x100020,
    0x200020,
    0x200020,
    0x200010,
    0x200000,
    0x000000,
    0x000000,
    0x000000,
    0x000000,
    0x000000,
]


@dataclass
class FavoriteOutfit:
    name: str
    looktype: int
    head: int = 0
    body: int = 0
    legs: int = 0
    feet: int = 0
    addons: int = 0

    def to_dict(self):
        return dict(
            name=self.name,
            looktype=self.looktype,
            head=self.head,
            body=self.body,
            legs=self.legs,
            feet=self.feet,
            addons=self.addons,
        )

    @classmethod
    def from_dict(cls, d):
        return cls(
            name=d.get("name", ""),
            looktype=d.get("looktype", 1),
            head=d.get("head", 0),
            body=d.get("body", 0),
            legs=d.get("legs", 0),
            feet=d.get("feet", 0),
            addons=d.get("addons", 0),
        )


class ColorSwatch(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, idx, rgb, parent=None):
        super().__init__(parent)
        self._idx, self._rgb, self._sel = idx, rgb, False
        self.setFixedSize(16, 16)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_selected(self, s):
        self._sel = s
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r, g, b = (self._rgb >> 16) & 0xFF, (self._rgb >> 8) & 0xFF, self._rgb & 0xFF
        p.fillRect(self.rect(), QColor(r, g, b))
        if self._sel:
            p.setPen(QPen(Qt.GlobalColor.white, 2))
            p.drawRect(1, 1, self.width() - 2, self.height() - 2)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._idx)


class ColorPalette(QWidget):
    color_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sw, self._sel = [], 0
        la = QGridLayout(self)
        la.setSpacing(1)
        la.setContentsMargins(0, 0, 0, 0)
        for i, rgb in enumerate(OUTFIT_COLORS):
            sw = ColorSwatch(i, rgb, self)
            sw.clicked.connect(self._pick)
            self._sw.append(sw)
            la.addWidget(sw, i // 19, i % 19)

    def _pick(self, i):
        self.set_selected(i)
        self.color_selected.emit(i)

    def set_selected(self, i):
        if 0 <= self._sel < len(self._sw):
            self._sw[self._sel].set_selected(False)
        self._sel = i
        if 0 <= i < len(self._sw):
            self._sw[i].set_selected(True)


class OutfitPreviewWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lt, self._hd, self._bd, self._lg, self._ft, self._ad = 1, 0, 0, 0, 0, 0
        self._dir, self._fr = 2, 0
        self.setFixedSize(192, 192)
        self.setStyleSheet("OutfitPreviewWidget{background:#1A1A2E;border:2px solid #363650;border-radius:8px;}")
        self._t = QTimer(self)
        self._t.timeout.connect(lambda: self._nxt())
        self._t.start(200)

    def set_outfit(self, lt, hd, bd, lg, ft, ad):
        self._lt, self._hd, self._bd, self._lg, self._ft, self._ad = lt, hd, bd, lg, ft, ad
        self.update()

    def _nxt(self):
        self._fr = (self._fr + 1) % 4
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(0x1A, 0x1A, 0x2E))
        cx, cy = self.width() // 2, self.height() // 2
        p.setPen(QPen(QColor(0x8B, 0x5C, 0xF6), 2))
        p.setBrush(QColor(0x36, 0x36, 0x50))
        p.drawEllipse(cx - 30, cy - 40, 60, 80)
        hc = OUTFIT_COLORS[self._hd] if self._hd < len(OUTFIT_COLORS) else 0xFFFFFF
        p.setBrush(QColor((hc >> 16) & 0xFF, (hc >> 8) & 0xFF, hc & 0xFF))
        p.drawEllipse(cx - 20, cy - 60, 40, 40)
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        p.drawText(10, self.height() - 10, f"Dir:{['S','E','N','W'][self._dir]}")
        p.drawText(10, 20, f"LT:{self._lt}")

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._dir = (self._dir + 1) % 4
            self.update()


class OutfitGrid(QScrollArea):
    outfit_selected = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._outs, self._btns, self._ftxt, self._conly = [], [], "", False
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._con = QWidget()
        self._la = QGridLayout(self._con)
        self._la.setSpacing(4)
        self._la.setContentsMargins(4, 4, 4, 4)
        self.setWidget(self._con)
        self.setStyleSheet("OutfitGrid{background:#1E1E2E;border:1px solid #363650;}")

    def set_outfits(self, outs):
        self._outs = outs
        self._rebuild()

    def set_filter(self, t, c=False):
        self._ftxt, self._conly = t.lower(), c
        self._rebuild()

    def _rebuild(self):
        for b in self._btns:
            b.deleteLater()
        self._btns.clear()
        flt = [
            (lt, n, l)
            for lt, n, l in self._outs
            if (not self._ftxt or self._ftxt in n.lower()) and (not self._conly or l >= 2)
        ]
        for i, (lt, n, _) in enumerate(flt):
            label = (n[:10] + "..." if len(n) > 10 else n) + "\n#" + str(lt)
            b = QPushButton(label)
            b.setStyleSheet(
                "QPushButton{background:#2A2A3E;color:#E5E5E7;border:1px solid #363650;min-width:90px;min-height:100px;}"
            )
            b.clicked.connect(lambda c, x=lt, y=n: self.outfit_selected.emit(x, y))
            self._la.addWidget(b, i // 4, i % 4)
            self._btns.append(b)


class FavoritesList(QListWidget):
    favorite_selected = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._favs = []
        self.itemDoubleClicked.connect(self._dbl)
        self.setStyleSheet("FavoritesList{background:#1E1E2E;color:#E5E5E7;}")

    def set_favorites(self, favs):
        self._favs = favs
        self.clear()
        [self.addItem(f"{f.name} (#{f.looktype})") for f in favs]

    def get_favorites(self):
        return list(self._favs)

    def add_favorite(self, f):
        self._favs.append(f)
        self.addItem(f"{f.name} (#{f.looktype})")

    def remove_selected(self):
        r = self.currentRow()
        if 0 <= r < len(self._favs):
            del self._favs[r]
            self.takeItem(r)

    def _dbl(self, it):
        r = self.row(it)
        if 0 <= r < len(self._favs):
            self.favorite_selected.emit(self._favs[r])


class OutfitChooserDialog(QDialog):
    outfit_changed = pyqtSignal(int, int, int, int, int, int, str, int)

    def __init__(self, parent=None, lt=1, hd=0, bd=0, lg=0, ft=0, ad=0, nm="You", sp=220):
        super().__init__(parent)
        self._lt, self._hd, self._bd, self._lg, self._ft, self._ad, self._nm, self._sp = lt, hd, bd, lg, ft, ad, nm, sp
        self._part = 0
        self.setWindowTitle("Customise Character")
        self.setMinimumSize(1100, 750)
        self._setup()
        self._style()
        self._load()
        self._pops()
        self._upd()
        self._upcol()

    def _setup(self):
        m = QVBoxLayout(self)
        c = QHBoxLayout()
        c.setSpacing(16)
        c1 = QVBoxLayout()
        c1.addWidget(QLabel("Character Preview"))
        self.pv = OutfitPreviewWidget()
        c1.addWidget(self.pv, 0, Qt.AlignmentFlag.AlignHCenter)
        c1.addWidget(QLabel("Appearance"))
        pr = QHBoxLayout()
        self.pg = QButtonGroup(self)
        for i, t in enumerate(["Head", "Primary", "Secondary", "Detail"]):
            b = QPushButton(t)
            b.setCheckable(True)
            b.setChecked(i == 0)
            self.pg.addButton(b, i)
            pr.addWidget(b)
        self.pg.buttonClicked.connect(self._pch)
        c1.addLayout(pr)
        self.cp = ColorPalette()
        self.cp.color_selected.connect(self._csel)
        c1.addWidget(self.cp)
        ar = QHBoxLayout()
        self.ca1 = QCheckBox("Addon 1")
        self.ca1.stateChanged.connect(self._adch)
        ar.addWidget(self.ca1)
        self.ca2 = QCheckBox("Addon 2")
        self.ca2.stateChanged.connect(self._adch)
        ar.addWidget(self.ca2)
        rb = QPushButton("Random")
        rb.clicked.connect(self._rand)
        ar.addWidget(rb)
        c1.addLayout(ar)
        fl = QGridLayout()
        fl.addWidget(QLabel("Speed:"), 0, 0)
        self.sps = QSpinBox()
        self.sps.setRange(50, 3000)
        self.sps.setValue(self._sp)
        fl.addWidget(self.sps, 0, 1)
        fl.addWidget(QLabel("Name:"), 1, 0)
        self.nme = QLineEdit(self._nm)
        fl.addWidget(self.nme, 1, 1)
        c1.addLayout(fl)
        c1.addStretch()
        c.addLayout(c1)
        c2 = QVBoxLayout()
        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("Available Outfits"))
        hdr.addStretch()
        self.se = QLineEdit()
        self.se.setPlaceholderText("Search...")
        self.se.textChanged.connect(self._sch)
        hdr.addWidget(self.se)
        self.cc = QCheckBox("Template Only")
        self.cc.stateChanged.connect(self._sch)
        hdr.addWidget(self.cc)
        c2.addLayout(hdr)
        self.og = OutfitGrid()
        self.og.outfit_selected.connect(self._osel)
        c2.addWidget(self.og, 1)
        c.addLayout(c2, 1)
        c3 = QVBoxLayout()
        c3.addWidget(QLabel("Favorites"))
        self.fl = FavoritesList()
        self.fl.setFixedWidth(220)
        self.fl.favorite_selected.connect(self._fsel)
        c3.addWidget(self.fl, 1)
        fb = QHBoxLayout()
        ba = QPushButton("Add")
        ba.clicked.connect(self._fadd)
        fb.addWidget(ba)
        br = QPushButton("Remove")
        br.clicked.connect(self.fl.remove_selected)
        fb.addWidget(br)
        c3.addLayout(fb)
        c.addLayout(c3)
        m.addLayout(c, 1)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        m.addWidget(bb)

    def _style(self):
        self.setStyleSheet("QDialog{background:#1E1E2E;}QLabel{color:#E5E5E7;}")

    def _load(self):
        p = Path.home() / ".py_rme_canary" / "outfit_preferences.json"
        try:
            if p.exists():
                d = json.loads(p.read_text())
                self._sp = d.get("speed", 220)
                self._nm = d.get("name", "You")
                self.fl.set_favorites([FavoriteOutfit.from_dict(f) for f in d.get("favorites", [])])
                self.sps.setValue(self._sp)
                self.nme.setText(self._nm)
        except:
            pass

    def _save(self):
        p = Path.home() / ".py_rme_canary"
        p.mkdir(parents=True, exist_ok=True)
        (p / "outfit_preferences.json").write_text(
            json.dumps(
                {"speed": self._sp, "name": self._nm, "favorites": [f.to_dict() for f in self.fl.get_favorites()]},
                indent=2,
            )
        )

    def _pops(self):
        self.og.set_outfits([(i, f"Outfit {i}", 2 if i % 3 == 0 else 1) for i in range(1, 500)])

    def _upd(self):
        self.pv.set_outfit(self._lt, self._hd, self._bd, self._lg, self._ft, self._ad)

    def _upcol(self):
        self.cp.set_selected([self._hd, self._bd, self._lg, self._ft][self._part])

    def _pch(self, b):
        self._part = self.pg.id(b)
        self._upcol()

    def _csel(self, i):
        if self._part == 0:
            self._hd = i
        elif self._part == 1:
            self._bd = i
        elif self._part == 2:
            self._lg = i
        else:
            self._ft = i
        self._upd()

    def _adch(self):
        self._ad = (1 if self.ca1.isChecked() else 0) | (2 if self.ca2.isChecked() else 0)
        self._upd()

    def _rand(self):
        mx = len(OUTFIT_COLORS) - 1
        self._hd, self._bd, self._lg, self._ft = (
            random.randint(0, mx),
            random.randint(0, mx),
            random.randint(0, mx),
            random.randint(0, mx),
        )
        self._upd()
        self._upcol()

    def _sch(self):
        self.og.set_filter(self.se.text(), self.cc.isChecked())

    def _osel(self, lt, n):
        self._lt = lt
        self._upd()

    def _fsel(self, f):
        self._lt, self._hd, self._bd, self._lg, self._ft, self._ad = (
            f.looktype,
            f.head,
            f.body,
            f.legs,
            f.feet,
            f.addons,
        )
        self.ca1.setChecked(bool(self._ad & 1))
        self.ca2.setChecked(bool(self._ad & 2))
        self._upd()
        self._upcol()

    def _fadd(self):
        nm, ok = QInputDialog.getText(self, "Add Favorite", "Name:", text="My Outfit")
        if ok and nm:
            self.fl.add_favorite(FavoriteOutfit(nm, self._lt, self._hd, self._bd, self._lg, self._ft, self._ad))

    def _ok(self):
        self._nm, self._sp = self.nme.text(), self.sps.value()
        self._save()
        self.outfit_changed.emit(self._lt, self._hd, self._bd, self._lg, self._ft, self._ad, self._nm, self._sp)
        self.accept()

    def get_outfit(self):
        return (self._lt, self._hd, self._bd, self._lg, self._ft, self._ad)
