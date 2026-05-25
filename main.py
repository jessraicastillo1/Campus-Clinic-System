import sys
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)
from PyQt6.QtCore import Qt
from backend.database import ensure_data_dir_and_files, needs_first_run_setup
from backend.auth import add_user, generate_recovery_key
from ui.login_window import LoginWindow

# ── Royal Dark — Global QSS ───────────────────────────────────────────────────
#
#  Color tokens
#  ─────────────────────────────────────────────────────
#  Sidebar           #0d2260
#  Active nav        #1a3a8a
#  Accent / gold     #f0c040
#  Page background   #f5f6fa
#  Card background   #ffffff
#  Headings          #1a3a8a
#  Body text         #1a1a2e
#  Muted / border    #d0d8ef
#  Table header      #1a3a8a  (white text)
#  Alt row           #f5f6fa
#  Selected row      #fff8e1
# ─────────────────────────────────────────────────────

ROYAL_DARK_STYLE = """
/* ── Base widget ── */
QWidget {
    font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
    font-size: 11px;
    color: #1a1a2e;
    background: transparent;
}

/* ── Main / top-level windows ── */
QMainWindow, QDialog {
    background: #f5f6fa;
}

/* ── QLabel ── */
QLabel {
    color: #1a1a2e;
    background: transparent;
}

/* ── QLineEdit ── */
QLineEdit {
    background: #ffffff;
    border: 1.5px solid #d0d8ef;
    border-radius: 6px;
    padding: 6px 10px;
    color: #1a1a2e;
    selection-background-color: #f0c040;
    selection-color: #0d2260;
}
QLineEdit:focus {
    border-color: #1a3a8a;
    background: #ffffff;
}
QLineEdit:disabled {
    background: #f5f6fa;
    color: #9ca3af;
    border-color: #e5e9f2;
}

/* ── QComboBox ── */
QComboBox {
    background: #ffffff;
    border: 1.5px solid #d0d8ef;
    border-radius: 6px;
    padding: 5px 10px;
    color: #1a1a2e;
    min-height: 28px;
}
QComboBox:focus        { border-color: #1a3a8a; }
QComboBox::drop-down   { border: none; width: 24px; }
QComboBox::down-arrow  { image: none; }
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1.5px solid #d0d8ef;
    border-radius: 6px;
    selection-background-color: #1a3a8a;
    selection-color: #ffffff;
    padding: 4px;
}

/* ── QPushButton — default ── */
QPushButton {
    background: #1a3a8a;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-weight: 700;
    font-size: 11px;
}
QPushButton:hover   { background: #1e4aa8; }
QPushButton:pressed { background: #0d2260; }
QPushButton:disabled {
    background: #e5e9f2;
    color: #9ca3af;
}

/* ── QPushButton — accent/gold variant (objectName="btn_gold") ── */
QPushButton#btn_gold {
    background: #f0c040;
    color: #0d2260;
}
QPushButton#btn_gold:hover   { background: #e5b830; }
QPushButton#btn_gold:pressed { background: #d4a820; }

/* ── QPushButton — danger variant (objectName="btn_danger") ── */
QPushButton#btn_danger {
    background: #fdecea;
    color: #c0392b;
    border: 1.5px solid rgba(192,57,43,0.30);
}
QPushButton#btn_danger:hover   { background: #f8c8c5; }
QPushButton#btn_danger:pressed { background: #f0a8a5; }

/* ── QPushButton — ghost / outline (objectName="btn_ghost") ── */
QPushButton#btn_ghost {
    background: #ffffff;
    color: #1a3a8a;
    border: 1.5px solid #1a3a8a;
}
QPushButton#btn_ghost:hover   { background: #e8edf8; }
QPushButton#btn_ghost:pressed { background: #d0d8ef; }

/* ── QDialogButtonBox pulls from QPushButton styles above ── */
QDialogButtonBox QPushButton { min-width: 80px; }

/* ── QTableWidget ── */
QTableWidget {
    background: #ffffff;
    border: none;
    color: #1a1a2e;
    gridline-color: #e8ebf2;
    selection-background-color: #fff8e1;
    selection-color: #0d2260;
    alternate-background-color: #f5f6fa;
}
QTableWidget::item {
    padding: 8px 12px;
    font-size: 11px;
    border: none;
}
QTableWidget::item:selected {
    background: #fff8e1;
    color: #0d2260;
    font-weight: 600;
}
QHeaderView::section {
    background: #1a3a8a;
    color: #ffffff;
    border: none;
    border-right: 1px solid rgba(255,255,255,0.10);
    padding: 9px 12px;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}
QHeaderView::section:last  { border-right: none; }
QHeaderView::section:checked { background: #f0c040; color: #0d2260; }

/* ── QScrollBar ── */
QScrollBar:vertical {
    background: #f0f1f5;
    width: 6px;
    border-radius: 3px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #b0bdd8;
    border-radius: 3px;
    min-height: 32px;
}
QScrollBar::handle:vertical:hover { background: #1a3a8a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #f0f1f5;
    height: 6px;
    border-radius: 3px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #b0bdd8;
    border-radius: 3px;
    min-width: 32px;
}
QScrollBar::handle:horizontal:hover { background: #1a3a8a; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── QCheckBox ── */
QCheckBox { spacing: 8px; color: #1a1a2e; }
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #d0d8ef;
    border-radius: 4px;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #1a3a8a;
    border-color: #1a3a8a;
}
QCheckBox::indicator:hover  { border-color: #1a3a8a; }

/* ── QDateEdit / QSpinBox ── */
QDateEdit, QSpinBox {
    background: #ffffff;
    border: 1.5px solid #d0d8ef;
    border-radius: 6px;
    padding: 5px 10px;
    color: #1a1a2e;
    min-height: 28px;
}
QDateEdit:focus, QSpinBox:focus { border-color: #1a3a8a; }
QDateEdit::up-button, QDateEdit::down-button,
QSpinBox::up-button, QSpinBox::down-button { width: 18px; }

/* ── QListWidget ── */
QListWidget {
    background: #ffffff;
    border: 1.5px solid #d0d8ef;
    border-radius: 6px;
    color: #1a1a2e;
    outline: none;
}
QListWidget::item { padding: 6px 10px; }
QListWidget::item:selected {
    background: #1a3a8a;
    color: #ffffff;
    border-radius: 4px;
}
QListWidget::item:hover { background: #f5f6fa; }

/* ── QMessageBox ── */
QMessageBox {
    background: #ffffff;
}
QMessageBox QLabel {
    color: #1a1a2e;
    font-size: 12px;
}
QMessageBox QPushButton {
    min-width: 88px;
    padding: 7px 14px;
}

/* ── QScrollArea ── */
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }

/* ── QFrame separators ── */
QFrame[frameShape="4"],   /* HLine */
QFrame[frameShape="5"] {  /* VLine */
    color: #d0d8ef;
}

/* ── QTabWidget / QTabBar (if used) ── */
QTabBar::tab {
    background: #e8edf8;
    color: #5a6480;
    border-radius: 6px 6px 0 0;
    padding: 7px 18px;
    margin-right: 2px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #1a3a8a;
    color: #ffffff;
}
QTabBar::tab:hover:!selected { background: #d0d8ef; }

/* ── QToolTip ── */
QToolTip {
    background: #0d2260;
    color: #ffffff;
    border: 1px solid #1a3a8a;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 10px;
}
"""


# ── Styled message-box helper ─────────────────────────────────────────────────


def _show_info(parent, title: str, text: str) -> None:
    """Themed informational QMessageBox."""
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setIcon(QMessageBox.Icon.Information)
    mb.setStandardButtons(QMessageBox.StandardButton.Ok)
    mb.setStyleSheet("""
        QMessageBox {
            background: #ffffff;
        }
        QMessageBox QLabel {
            color: #1a1a2e;
            font-size: 12px;
            min-width: 280px;
        }
        QPushButton {
            background: #1a3a8a;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 7px 22px;
            font-weight: 700;
            font-size: 11px;
            min-width: 88px;
        }
        QPushButton:hover   { background: #1e4aa8; }
        QPushButton:pressed { background: #0d2260; }
    """)
    mb.exec()


def _show_warning(parent, title: str, text: str) -> None:
    """Themed warning QMessageBox."""
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setIcon(QMessageBox.Icon.Warning)
    mb.setStandardButtons(QMessageBox.StandardButton.Ok)
    mb.setStyleSheet("""
        QMessageBox {
            background: #ffffff;
        }
        QMessageBox QLabel {
            color: #1a1a2e;
            font-size: 12px;
            min-width: 280px;
        }
        QPushButton {
            background: #f0c040;
            color: #0d2260;
            border: none;
            border-radius: 6px;
            padding: 7px 22px;
            font-weight: 700;
            font-size: 11px;
            min-width: 88px;
        }
        QPushButton:hover   { background: #e5b830; }
        QPushButton:pressed { background: #d4a820; }
    """)
    mb.exec()


def _show_critical(parent, title: str, text: str) -> None:
    """Themed critical / error QMessageBox."""
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setIcon(QMessageBox.Icon.Critical)
    mb.setStandardButtons(QMessageBox.StandardButton.Ok)
    mb.setStyleSheet("""
        QMessageBox {
            background: #ffffff;
        }
        QMessageBox QLabel {
            color: #1a1a2e;
            font-size: 12px;
            min-width: 280px;
        }
        QPushButton {
            background: #c0392b;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 7px 22px;
            font-weight: 700;
            font-size: 11px;
            min-width: 88px;
        }
        QPushButton:hover   { background: #a93226; }
        QPushButton:pressed { background: #922b21; }
    """)
    mb.exec()


# ── First-run setup dialog ────────────────────────────────────────────────────

_DIALOG_STYLE = """
QDialog {
    background: #ffffff;
}
QLabel {
    color: #1a1a2e;
}
QLabel#dlg_title {
    color: #1a3a8a;
    font-size: 16px;
    font-weight: 800;
}
QLabel#dlg_info {
    color: #5a6480;
    font-size: 11px;
}
QLabel#dlg_form_label {
    color: #1a3a8a;
    font-weight: 700;
    font-size: 11px;
}
QLineEdit {
    background: #f5f6fa;
    border: 1.5px solid #d0d8ef;
    border-radius: 6px;
    padding: 7px 10px;
    color: #1a1a2e;
    font-size: 11px;
}
QLineEdit:focus {
    border-color: #1a3a8a;
    background: #ffffff;
}
QDialogButtonBox QPushButton {
    background: #f0c040;
    color: #0d2260;
    border: none;
    border-radius: 6px;
    padding: 8px 24px;
    font-weight: 800;
    font-size: 11px;
    min-width: 90px;
}
QDialogButtonBox QPushButton:hover   { background: #e5b830; }
QDialogButtonBox QPushButton:pressed { background: #d4a820; }
"""

_RECOVERY_MSG_STYLE = """
QMessageBox {
    background: #ffffff;
}
QMessageBox QLabel {
    color: #1a1a2e;
    font-size: 12px;
}
QPushButton {
    background: #1a3a8a;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 24px;
    font-weight: 700;
    font-size: 11px;
    min-width: 90px;
}
QPushButton:hover   { background: #1e4aa8; }
QPushButton:pressed { background: #0d2260; }
"""


class _FirstRunDialog(QDialog):
    """Shown once when there are no user accounts yet."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome – Initial Setup")
        self.setFixedWidth(420)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setStyleSheet(_DIALOG_STYLE)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(14)

        # ── Header ────────────────────────────────────────────────────────────
        title = QLabel("Set Up Administrator Account")
        title.setObjectName("dlg_title")
        lay.addWidget(title)

        info = QLabel(
            "No user accounts exist yet. Please create a password for the "
            "admin account before continuing. The password must be at least "
            "6 characters long."
        )
        info.setObjectName("dlg_info")
        info.setWordWrap(True)
        lay.addWidget(info)

        # ── Form ──────────────────────────────────────────────────────────────
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._pw1 = QLineEdit()
        self._pw1.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw1.setPlaceholderText("New password (min 6 characters)")
        self._pw1.setFixedHeight(38)

        self._pw2 = QLineEdit()
        self._pw2.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw2.setPlaceholderText("Confirm password")
        self._pw2.setFixedHeight(38)

        pw_lbl = QLabel("Password:")
        pw_lbl.setObjectName("dlg_form_label")
        cfm_lbl = QLabel("Confirm:")
        cfm_lbl.setObjectName("dlg_form_label")

        form.addRow(pw_lbl, self._pw1)
        form.addRow(cfm_lbl, self._pw2)
        lay.addLayout(form)

        # ── Button ────────────────────────────────────────────────────────────
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setText("Create Account")
        buttons.accepted.connect(self._on_ok)
        lay.addWidget(buttons)

    def _on_ok(self):
        pw1 = self._pw1.text()
        pw2 = self._pw2.text()

        if len(pw1) < 6:
            _show_warning(self, "Too Short", "Password must be at least 6 characters.")
            return

        if pw1 != pw2:
            _show_warning(self, "Mismatch", "Passwords do not match. Please try again.")
            self._pw2.clear()
            return

        add_user("admin", pw1, "admin")

        # ── Recovery key — shown once, never again ────────────────────────────
        key = generate_recovery_key()
        msg = QMessageBox(self)
        msg.setWindowTitle("Save Your Recovery Key")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(
            "<b>Write down this recovery key and keep it safe.</b><br><br>"
            "It is the only way to reset account passwords if you are ever "
            "locked out.<br>"
            "<b>It will never be shown again.</b>"
        )
        msg.setInformativeText(
            f"<center><b style='font-size:16px;letter-spacing:3px;"
            f"color:#0d2260;background:#fff8e1;padding:6px 14px;"
            f"border-radius:6px;'>{key}</b></center>"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setStyleSheet(_RECOVERY_MSG_STYLE)
        msg.exec()
        self.accept()


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    ensure_data_dir_and_files()
    app = QApplication(sys.argv)

    # Apply the Royal Dark theme globally so every QDialog, QMessageBox,
    # and sub-window inherits the palette without extra per-widget work.
    app.setStyleSheet(ROYAL_DARK_STYLE)

    if needs_first_run_setup():
        dlg = _FirstRunDialog()
        while dlg.exec() != QDialog.DialogCode.Accepted:
            _show_warning(
                None,
                "Setup Required",
                "You must create the administrator account before continuing.",
            )

    window = LoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
