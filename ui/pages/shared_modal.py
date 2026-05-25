"""
shared_modal.py — Royal Dark modal helpers
All page dialog forms import from here for a consistent navy × gold look.
"""
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QPainter, QPen, QFont
from PyQt6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QComboBox, QDateEdit,
    QDialog, QScrollArea, QPushButton, QGraphicsDropShadowEffect,
)

# ── Shared colour tokens ──────────────────────────────────────────────────────
NAVY   = "#0d2260"
NAVYL  = "#1a3a8a"
GOLD   = "#f0c040"
PAGE   = "#f5f6fa"
CARD   = "#ffffff"
BORDER = "#d0d8ef"
MUTED  = "#5a6480"
RED    = "#c0392b"

# ── Master dialog stylesheet ──────────────────────────────────────────────────
MODAL_STYLE = f"""
QDialog {{ background: {CARD}; }}

#modal_titlebar  {{ background: {NAVYL}; }}
#modal_title     {{ color: #ffffff; font-size: 14px; font-weight: 800; }}
#modal_titlebar_red {{ background: {RED}; }}   /* Emergency accent */
#modal_titlebar_gold {{ background: #c9a227; }} /* Incident accent */

#modal_body_widget {{ background: {CARD}; }}
QScrollArea        {{ background: {CARD}; border: none; }}

#section_lbl {{
    font-size: 9.5px; font-weight: 700;
    letter-spacing: 1.2px; color: {MUTED};
    text-transform: uppercase;
}}
#field_lbl  {{ font-size: 11px; font-weight: 700; color: {MUTED}; }}
#req_star   {{ color: {RED}; font-size: 11px; font-weight: 700; }}

#form_input {{
    background: {PAGE}; border: 1px solid {BORDER};
    border-radius: 7px; padding: 0px 11px;
    font-size: 12px; color: #1a1a2e;
}}
#form_input:focus {{ border: 2px solid {NAVYL}; background: {CARD}; }}

#form_input_ro {{
    background: #eef0f7; border: 1px dashed #b0bdd8;
    border-radius: 7px; padding: 0px 11px;
    font-size: 12px; color: #7a87a8;
}}

QComboBox {{
    background: {PAGE}; border: 1px solid {BORDER};
    border-radius: 7px; padding: 0px 11px;
    font-size: 12px; color: #1a1a2e;
    min-height: 36px; max-height: 36px;
}}
QComboBox:focus {{ border: 2px solid {NAVYL}; background: {CARD}; }}
QComboBox::drop-down  {{ border: none; padding-right: 10px; subcontrol-position: right center; }}
QComboBox QAbstractItemView {{
    background: {CARD}; border: 1px solid {BORDER};
    selection-background-color: #e8edf8;
    selection-color: {NAVYL}; color: #1a1a2e; font-size: 12px;
}}

QDateEdit {{
    background: {PAGE}; border: 1px solid {BORDER};
    border-radius: 7px; padding: 0px 11px;
    font-size: 12px; color: #1a1a2e;
    min-height: 36px; max-height: 36px;
}}
QDateEdit:focus {{ border: 2px solid {NAVYL}; background: {CARD}; }}
QDateEdit::drop-down {{ border: none; padding-right: 10px; }}

QTimeEdit {{
    background: {PAGE}; border: 1px solid {BORDER};
    border-radius: 7px; padding: 0px 11px;
    font-size: 12px; color: #1a1a2e;
    min-height: 36px; max-height: 36px;
}}
QTimeEdit:focus {{ border: 2px solid {NAVYL}; background: {CARD}; }}

QCheckBox {{ color: #1a1a2e; font-size: 12px; font-weight: 600; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {BORDER}; border-radius: 4px; background: {PAGE};
}}
QCheckBox::indicator:checked {{
    background: {NAVYL}; border-color: {NAVYL};
}}

#modal_footer    {{ background: {PAGE}; border-top: 1px solid {BORDER}; }}

#btn_save {{
    background: {GOLD}; color: {NAVY};
    border: none; border-radius: 6px;
    padding: 9px 22px; font-size: 12px; font-weight: 800; min-height: 36px;
}}
#btn_save:hover   {{ background: #e5b830; }}
#btn_save:pressed {{ background: #d4a820; }}

#btn_cancel {{
    background: {CARD}; color: {NAVYL};
    border: 1.5px solid {NAVYL}; border-radius: 6px;
    padding: 8px 20px; font-size: 12px; font-weight: 700; min-height: 36px;
}}
#btn_cancel:hover   {{ background: #e8edf8; }}
#btn_cancel:pressed {{ background: #d0d8ef; }}

#btn_print_footer {{
    background: {PAGE}; color: {NAVYL};
    border: 1.5px solid {BORDER}; border-radius: 6px;
    padding: 8px 18px; font-size: 12px; font-weight: 700; min-height: 36px;
}}
#btn_print_footer:hover {{ background: #e8edf8; border-color: {NAVYL}; }}

QScrollBar:vertical {{ background: #f0f1f5; width: 4px; border-radius: 2px; }}
QScrollBar::handle:vertical {{ background: #c0cce0; border-radius: 2px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


# ── Widget factory helpers ────────────────────────────────────────────────────

def section_div(title: str) -> QWidget:
    """Gold-underlined section divider."""
    w   = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 16, 0, 8)
    lay.setSpacing(10)
    lbl = QLabel(title)
    lbl.setObjectName("section_lbl")
    lay.addWidget(lbl)
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"background: {GOLD}; max-height: 2px; border: none;")
    lay.addWidget(line, 1)
    return w


def field_lbl(text: str, required: bool = False) -> QWidget:
    """Compact field label with optional red asterisk."""
    w   = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 2)
    lay.setSpacing(2)
    lbl = QLabel(text)
    lbl.setObjectName("field_lbl")
    lay.addWidget(lbl)
    if required:
        star = QLabel("*")
        star.setObjectName("req_star")
        lay.addWidget(star)
    lay.addStretch()
    return w


def inp(placeholder: str = "", readonly: bool = False, value: str = "") -> QLineEdit:
    """Styled QLineEdit."""
    e = QLineEdit()
    e.setObjectName("form_input_ro" if readonly else "form_input")
    e.setFixedHeight(36)
    e.setPlaceholderText(placeholder)
    e.setReadOnly(readonly)
    if value:
        e.setText(value)
    return e


def combo(items: list, current: str = "") -> QComboBox:
    """Styled QComboBox."""
    cb = QComboBox()
    cb.addItems(items)
    if current and current in items:
        cb.setCurrentText(current)
    elif current:
        cb.addItem(current)
        cb.setCurrentText(current)
    return cb


def date_edit(value: str = "", default_today: bool = True) -> QDateEdit:
    """Styled QDateEdit."""
    de = QDateEdit()
    de.setCalendarPopup(True)
    de.setDisplayFormat("MM/dd/yyyy")
    de.setFixedHeight(36)
    if value:
        try:
            p = value.split("-")
            de.setDate(QDate(int(p[0]), int(p[1]), int(p[2])))
        except Exception:
            de.setDate(QDate.currentDate() if default_today else QDate(2000, 1, 1))
    else:
        de.setDate(QDate.currentDate() if default_today else QDate(2000, 1, 1))
    return de


def pill_label(text: str, color: str = "blue") -> QLabel:
    """Coloured status pill label."""
    _COLOURS = {
        "green":  ("#e6f4ec", "#1a7a4a"),
        "blue":   ("#e8edf8", "#1a3a8a"),
        "gold":   ("#fdf6e3", "#c9a227"),
        "red":    ("#fdecea", "#c0392b"),
        "muted":  ("#f0f1f5", "#5a6480"),
    }
    bg, fg = _COLOURS.get(color, _COLOURS["blue"])
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        QLabel {{
            background: {bg}; color: {fg};
            border-radius: 10px; padding: 3px 10px;
            font-size: 10px; font-weight: 700;
        }}
    """)
    return lbl


def build_modal_shell(dialog: QDialog, title: str,
                      icon: str = "＋",
                      titlebar_id: str = "modal_titlebar",
                      width: int = 560) -> tuple:
    """
    Builds the standard navy titlebar + scrollable body + footer shell.
    Returns (body_layout, footer_layout, root_layout).
    """
    dialog.setFixedWidth(width)
    dialog.setMinimumHeight(400)
    dialog.setMaximumHeight(700)
    dialog.setStyleSheet(MODAL_STYLE)

    root = QVBoxLayout(dialog)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(0)

    # Titlebar
    tb = QWidget()
    tb.setObjectName(titlebar_id)
    tb.setFixedHeight(52)
    tb_lay = QHBoxLayout(tb)
    tb_lay.setContentsMargins(20, 0, 20, 0)
    icon_lbl = QLabel(icon + " ")
    icon_lbl.setStyleSheet(f"color: {GOLD}; font-size: 15px; font-weight: 800;")
    tb_lay.addWidget(icon_lbl)
    title_lbl = QLabel(title)
    title_lbl.setObjectName("modal_title")
    tb_lay.addWidget(title_lbl)
    tb_lay.addStretch()
    root.addWidget(tb)

    # Scrollable body
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    body = QWidget()
    body.setObjectName("modal_body_widget")
    body_lay = QVBoxLayout(body)
    body_lay.setContentsMargins(20, 4, 20, 12)
    body_lay.setSpacing(0)
    scroll.setWidget(body)
    root.addWidget(scroll, 1)

    # Footer
    footer = QWidget()
    footer.setObjectName("modal_footer")
    footer.setFixedHeight(60)
    foot_lay = QHBoxLayout(footer)
    foot_lay.setContentsMargins(20, 0, 20, 0)
    foot_lay.setSpacing(10)
    root.addWidget(footer)

    return body_lay, foot_lay, root


def add_footer_buttons(foot_lay, dialog: QDialog,
                       save_text: str = "💾  Save",
                       show_required_note: bool = True,
                       extra_buttons: list = None):
    """Adds cancel + save (and optional extra) buttons to footer."""
    if show_required_note:
        req = QLabel("<span style='color:#c0392b;font-weight:700'>*</span>"
                     "<span style='color:#5a6480;font-size:11px'> Required fields</span>")
        req.setTextFormat(Qt.TextFormat.RichText)
        foot_lay.addWidget(req)
    foot_lay.addStretch()

    if extra_buttons:
        for btn in extra_buttons:
            foot_lay.addWidget(btn)

    cancel = QPushButton("Cancel")
    cancel.setObjectName("btn_cancel")
    cancel.setCursor(Qt.CursorShape.PointingHandCursor)
    cancel.clicked.connect(dialog.reject)
    foot_lay.addWidget(cancel)

    save = QPushButton(save_text)
    save.setObjectName("btn_save")
    save.setCursor(Qt.CursorShape.PointingHandCursor)
    foot_lay.addWidget(save)
    return save  # caller connects save.clicked


def confirm_delete_dialog(parent, name: str) -> bool:
    """
    Shows a Royal Dark styled confirm-delete dialog.
    Returns True if user confirmed.
    """
    dlg = QDialog(parent)
    dlg.setWindowTitle("Confirm Delete")
    dlg.setFixedWidth(380)
    dlg.setStyleSheet(f"""
        QDialog  {{ background: {CARD}; }}
        QLabel   {{ color: #1a1a2e; }}
    """)
    root = QVBoxLayout(dlg)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(0)

    body = QWidget()
    body.setStyleSheet(f"background: {CARD};")
    b_lay = QVBoxLayout(body)
    b_lay.setContentsMargins(28, 28, 28, 10)
    b_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

    icon = QLabel("🗑")
    icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon.setStyleSheet("""
        background: #fdecea; border-radius: 27px;
        min-width: 54px; max-width: 54px;
        min-height: 54px; max-height: 54px;
        font-size: 22px; padding: 8px;
    """)
    b_lay.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

    t = QLabel("Delete Record?")
    t.setAlignment(Qt.AlignmentFlag.AlignCenter)
    t.setStyleSheet("font-size: 16px; font-weight: 800; color: #1a1a2e; margin-top: 12px;")
    b_lay.addWidget(t)

    sub = QLabel(f"This will permanently delete <b>{name}</b>.<br>"
                 "This action <b>cannot be undone</b>.")
    sub.setWordWrap(True)
    sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
    sub.setTextFormat(Qt.TextFormat.RichText)
    sub.setStyleSheet("font-size: 12px; color: #5a6480; margin-top: 6px;")
    b_lay.addWidget(sub)
    root.addWidget(body)

    foot = QWidget()
    foot.setStyleSheet(f"background: {PAGE}; border-top: 1px solid {BORDER};")
    f_lay = QHBoxLayout(foot)
    f_lay.setContentsMargins(20, 12, 20, 12)
    f_lay.setSpacing(10)
    f_lay.addStretch()

    c_btn = QPushButton("Cancel")
    c_btn.setStyleSheet(f"""
        background: {CARD}; color: {NAVYL};
        border: 1.5px solid {NAVYL}; border-radius: 6px;
        padding: 8px 20px; font-weight: 700; font-size: 12px;
    """)
    c_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    c_btn.clicked.connect(dlg.reject)
    f_lay.addWidget(c_btn)

    d_btn = QPushButton("🗑  Delete Permanently")
    d_btn.setStyleSheet("""
        background: #c0392b; color: #fff;
        border: none; border-radius: 6px;
        padding: 8px 20px; font-weight: 800; font-size: 12px;
    """)
    d_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    d_btn.clicked.connect(dlg.accept)
    f_lay.addWidget(d_btn)
    root.addWidget(foot)

    return dlg.exec() == QDialog.DialogCode.Accepted
