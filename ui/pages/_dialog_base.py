"""
_dialog_base.py  –  Shared base class for all Royal Dark FormDialogs.

Provides:
  • _BaseFormDialog  – title bar, scroll body, section headers,
                       labelled form rows, toast notifications,
                       patient-ID searchable combo, pill badges,
                       textarea helper, and the standard button row.
"""

from __future__ import annotations

import datetime

from PyQt6.QtCore    import Qt, QDate, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui     import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QFrame, QGraphicsOpacityEffect,
    QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QScrollArea, QSizePolicy, QSpinBox, QDoubleSpinBox,
    QVBoxLayout, QWidget,
)

from backend.config   import PATIENTS_CSV
from backend.database import read_csv

# ── colour tokens ─────────────────────────────────────────────────────────────
NAVY   = "#0d2260"
BLUE   = "#1a3a8a"
GOLD   = "#f0c040"
GOLD_D = "#e6b830"
WHITE  = "#ffffff"
BG     = "#f5f6fa"
BORDER = "#d0d8ef"
TEXT   = "#1a1a2e"
MUTED  = "#5a6480"

# section label
SEC_STYLE  = (
    "color: #1a3a8a; font-size: 10px; font-weight: 800; "
    "letter-spacing: 1.2px; padding-bottom: 4px; "
    "border-bottom: 2px solid #d0d8ef; margin-bottom: 2px;"
)
# field label
LBL_STYLE  = "font-weight: 600; color: #5a6480; font-size: 12px;"
# read-only field
RO_STYLE   = (
    "background: #eef0f7; color: #5a6480; border: 1px dashed #d0d8ef;"
    " border-radius: 7px; padding: 7px 11px; font-size: 12px;"
)
# normal field
FLD_STYLE  = (
    "background: #f5f6fa; border: 1px solid #d0d8ef; border-radius: 7px;"
    " padding: 7px 11px; font-size: 12px; color: #1a1a2e; min-height: 34px;"
)
FLD_FOCUS  = (
    "background: #ffffff; border: 2px solid #1a3a8a; border-radius: 7px;"
    " padding: 7px 11px; font-size: 12px; color: #1a1a2e; min-height: 34px;"
)


# =============================================================================

class _BaseFormDialog(QDialog):
    """
    Subclasses must call:
        self._build_ui(title_text, title_bar_color="#1a3a8a")
    at the end of their own __init__, and override:
        _populate_form(self)   → add sections/rows to self._body_layout
        get_data(self) → dict
    """

    # ── username injected by the page that opens the dialog ───────────────
    _session_user: str = ""

    # ── patient cache (loaded once per dialog open) ───────────────────────
    _patient_rows: list[dict] | None = None

    def __init__(self, parent=None, data: dict | None = None,
                 session_user: str = ""):
        super().__init__(parent)
        self._data         = data or {}
        self._session_user = session_user
        self._fields: dict = {}

    # ── public entry point for subclasses ─────────────────────────────────

    def _build_ui(self, title: str, bar_color: str = BLUE) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── title bar ──────────────────────────────────────────────────
        bar = QWidget()
        bar.setFixedHeight(50)
        bar.setStyleSheet(f"background: {bar_color};")
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(20, 0, 20, 0)

        icon_lbl = QLabel("✦")
        icon_lbl.setStyleSheet(f"color: {GOLD}; font-size: 14px; margin-right: 6px;")
        bar_lay.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "color: #ffffff; font-size: 14px; font-weight: 800; letter-spacing: 0.3px;"
        )
        bar_lay.addWidget(title_lbl)
        bar_lay.addStretch()
        outer.addWidget(bar)

        # ── scrollable body ────────────────────────────────────────────
        self._body_widget = QWidget()
        self._body_layout = QVBoxLayout(self._body_widget)
        self._body_layout.setContentsMargins(22, 18, 22, 12)
        self._body_layout.setSpacing(14)

        self._populate_form()
        self._body_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: #f5f6fa;")
        scroll.setWidget(self._body_widget)
        outer.addWidget(scroll, 1)

        # ── divider ────────────────────────────────────────────────────
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color: {BORDER};")
        outer.addWidget(div)

        # ── button row ─────────────────────────────────────────────────
        self._build_button_row(outer)

        self.setMinimumWidth(540)
        self.resize(560, 580)

    def _build_button_row(self, outer: QVBoxLayout) -> None:
        """Standard Save / Cancel row. Subclasses may override."""
        row_w = QWidget()
        row_w.setStyleSheet("background: #ffffff;")
        row = QHBoxLayout(row_w)
        row.setContentsMargins(22, 12, 22, 14)
        row.setSpacing(10)
        row.addStretch()

        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(36)
        cancel.setMinimumWidth(90)
        cancel.setStyleSheet(
            "background:#ffffff; color:#1a3a8a; border:1.5px solid #1a3a8a;"
            " border-radius:6px; font-size:12px; font-weight:700;"
        )
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)

        save = QPushButton("Save")
        save.setFixedHeight(36)
        save.setMinimumWidth(90)
        save.setStyleSheet(
            f"background:{GOLD}; color:{NAVY}; border:none;"
            " border-radius:6px; font-size:12px; font-weight:700;"
        )
        save.clicked.connect(self._on_save)
        row.addWidget(save)

        outer.addWidget(row_w)

    # ── section / row helpers ──────────────────────────────────────────────

    def _section(self, title: str) -> None:
        lbl = QLabel(title.upper())
        lbl.setStyleSheet(SEC_STYLE)
        self._body_layout.addWidget(lbl)

    def _row(self, label: str, widget: QWidget,
             required: bool = False) -> None:
        """Add a label + widget pair as a horizontal row."""
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        lbl_text = f"{label} <span style='color:#c0392b;'>*</span>" if required else label
        lbl = QLabel()
        lbl.setText(lbl_text)
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setFixedWidth(148)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl.setStyleSheet(LBL_STYLE)
        lbl.setWordWrap(True)

        lay.addWidget(lbl)
        lay.addWidget(widget, 1)
        self._body_layout.addWidget(row)

    def _spacer(self, px: int = 6) -> None:
        sp = QWidget()
        sp.setFixedHeight(px)
        self._body_layout.addWidget(sp)

    # ── widget factories ───────────────────────────────────────────────────

    def _ro_field(self, text: str = "") -> QLineEdit:
        w = QLineEdit(text)
        w.setReadOnly(True)
        w.setStyleSheet(RO_STYLE)
        return w

    def _text_field(self, placeholder: str = "",
                    text: str = "") -> QLineEdit:
        w = QLineEdit(text)
        w.setPlaceholderText(placeholder)
        w.setStyleSheet(FLD_STYLE)
        w.setMinimumHeight(34)
        return w

    def _textarea(self, rows: int = 3,
                  placeholder: str = "") -> QPlainTextEdit:
        w = QPlainTextEdit()
        w.setPlaceholderText(placeholder)
        w.setFixedHeight(rows * 22 + 18)
        w.setStyleSheet(
            "background:#f5f6fa; border:1px solid #d0d8ef; border-radius:7px;"
            " padding:6px 10px; font-size:12px; color:#1a1a2e;"
        )
        return w

    def _combo(self, options: list[str],
               current: str = "") -> QComboBox:
        w = QComboBox()
        w.addItems(options)
        w.setStyleSheet(FLD_STYLE)
        w.setMinimumHeight(34)
        if current and current in options:
            w.setCurrentText(current)
        elif current:
            w.addItem(current); w.setCurrentText(current)
        return w

    def _date_field(self, date: QDate | None = None) -> QDateEdit:
        w = QDateEdit()
        w.setCalendarPopup(True)
        w.setDisplayFormat("MM/dd/yyyy")
        w.setStyleSheet(FLD_STYLE)
        w.setMinimumHeight(34)
        w.setDate(date if date else QDate.currentDate())
        return w

    def _date_from_str(self, raw: str) -> QDate:
        if raw:
            try:
                p = raw.split("-")
                return QDate(int(p[0]), int(p[1]), int(p[2]))
            except Exception:
                pass
        return QDate.currentDate()

    def _spinbox(self, min_v: int = 0, max_v: int = 9999,
                 value: int = 0) -> QSpinBox:
        w = QSpinBox()
        w.setRange(min_v, max_v)
        w.setValue(value)
        w.setStyleSheet(FLD_STYLE)
        w.setMinimumHeight(34)
        return w

    def _double_spinbox(self, min_v: float = 0.0, max_v: float = 9999.0,
                        value: float = 0.0, decimals: int = 1,
                        suffix: str = "") -> QDoubleSpinBox:
        w = QDoubleSpinBox()
        w.setRange(min_v, max_v)
        w.setDecimals(decimals)
        w.setValue(value)
        if suffix:
            w.setSuffix(f" {suffix}")
        w.setStyleSheet(FLD_STYLE)
        w.setMinimumHeight(34)
        return w

    def _pill(self, text: str, color: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFixedHeight(26)
        lbl.setStyleSheet(
            f"background:{color}20; color:{color}; border:1px solid {color}60;"
            " border-radius:13px; padding:0 14px; font-size:11px; font-weight:700;"
        )
        return lbl

    # ── patient searchable dropdown ────────────────────────────────────────

    def _patient_combo(self, current_id: str = "") -> QComboBox:
        """Return a combo pre-loaded with all patients as '[ID] First Last'."""
        if _BaseFormDialog._patient_rows is None:
            _BaseFormDialog._patient_rows = read_csv(PATIENTS_CSV)
        rows = _BaseFormDialog._patient_rows

        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        combo.lineEdit().setPlaceholderText("Search patient…")
        combo.setStyleSheet(FLD_STYLE)
        combo.setMinimumHeight(34)

        id_to_idx: dict[str, int] = {}
        combo.addItem("")
        for i, r in enumerate(rows, start=1):
            pid   = r.get("patient_id", "")
            fname = r.get("first_name", "")
            lname = r.get("last_name", "")
            combo.addItem(f"[{pid}]  {fname} {lname}".strip(), userData=pid)
            id_to_idx[pid] = i

        if current_id and current_id in id_to_idx:
            combo.setCurrentIndex(id_to_idx[current_id])

        combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        combo.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        return combo

    def _patient_id_from_combo(self, combo: QComboBox) -> str:
        """Extract the raw patient_id from a patient combo selection."""
        data = combo.currentData()
        if data:
            return str(data)
        # fallback: parse [ID] from display text
        text = combo.currentText().strip()
        if text.startswith("["):
            end = text.find("]")
            if end > 0:
                return text[1:end]
        return text

    # ── toast notification ─────────────────────────────────────────────────

    def _show_toast(self, message: str, color: str = "#1a7a4a") -> None:
        toast = QLabel(message, self)
        toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toast.setStyleSheet(
            f"background:{color}; color:#ffffff; border-radius:8px;"
            " padding:10px 20px; font-size:12px; font-weight:700;"
        )
        toast.adjustSize()
        toast.setFixedWidth(max(toast.width() + 30, 300))
        # center at bottom
        x = (self.width()  - toast.width())  // 2
        y =  self.height() - toast.height()  - 60
        toast.move(x, y)

        eff = QGraphicsOpacityEffect(toast)
        toast.setGraphicsEffect(eff)
        toast.show()

        anim = QPropertyAnimation(eff, b"opacity", toast)
        anim.setDuration(3500)
        anim.setKeyValueAt(0.0,  1.0)
        anim.setKeyValueAt(0.75, 1.0)
        anim.setKeyValueAt(1.0,  0.0)
        anim.setEasingCurve(QEasingCurve.Type.InQuad)
        anim.start()
        QTimer.singleShot(3600, toast.deleteLater)

    # ── subclass interface ─────────────────────────────────────────────────

    def _populate_form(self) -> None:
        """Override in subclass to add sections and rows."""
        raise NotImplementedError

    def get_data(self) -> dict:
        """Override in subclass to collect and return form data."""
        raise NotImplementedError

    def _on_save(self) -> None:
        """Override or extend to validate then accept."""
        self.accept()
