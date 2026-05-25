import os
import sys
import csv
import json
import datetime
import hashlib
from datetime import datetime as _dt

from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtGui import (
    QColor, QFont, QIcon, QLinearGradient, QBrush, QPainter, QPen,
    QBitmap, QPixmap, QKeySequence, QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFormLayout, QFrame, QGraphicsDropShadowEffect, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from backend.config import *
from backend.auth import authenticate, register_user, verify_recovery_key, recovery_key_exists, reset_user_password
from backend.database import ensure_data_dir_and_files, read_csv
from ui.dashboard_window import DashboardWindow

# =============================================================================

LOGIN_STYLE = """
* { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; color: #e2e8f0; }

#login_bg {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #060d1a, stop:0.45 #0d1f3c, stop:1 #0a1628);
}

/* ── Login card — Royal Navy with gold top accent ── */
#login_card {
    background: #0d2260;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    border-top: 4px solid #f0c040;
}

#login_title { font-size: 20px; font-weight: 800; color: #ffffff; letter-spacing: -0.3px; }
#login_sub   { font-size: 11px; font-weight: 700; letter-spacing: 0.5px; color: #f0c040; }
#field_label { font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.70); }
#version_label { color: rgba(255,255,255,0.30); font-size: 11px; }

/* ── Input fields ── */
#login_input {
    background: #1a2a6e;
    border: 1px solid #2a4aaa;
    border-radius: 9px;
    padding: 11px 14px;
    font-size: 13px;
    color: #ffffff;
}
#login_input:focus { border: 2px solid #f0c040; background: #1a2a6e; color: #ffffff; }

/* ── Primary button — Gold ── */
#sign_in_btn {
    background: #f0c040;
    color: #0d2260;
    border: none;
    border-radius: 9px;
    padding: 13px;
    font-weight: 800;
    font-size: 14px;
    letter-spacing: 0.2px;
}
#sign_in_btn:hover   { background: #e5b830; }
#sign_in_btn:pressed { background: #d4a820; }

/* ── Secondary button ── */
#create_btn {
    background: transparent;
    color: rgba(255,255,255,0.65);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 9px;
    padding: 12px;
    font-weight: 600;
    font-size: 13px;
}
#create_btn:hover { background: rgba(255,255,255,0.05); border-color: #f0c040; color: #f0c040; }

/* ── Show/Hide toggle ── */
#show_btn {
    background: transparent;
    border: none;
    color: rgba(255,255,255,0.45);
    padding: 4px 10px;
    font-size: 11px;
}
#show_btn:hover { color: rgba(255,255,255,0.80); }

/* ── Forgot link — gold ── */
#forgot_link {
    color: #f0c040;
    background: transparent;
    border: none;
    font-size: 12px;
    font-weight: 600;
}
#forgot_link:hover { color: #ffe070; }

/* ── Checkbox ── */
#remember_cb { color: rgba(255,255,255,0.65); font-size: 12px; }
QCheckBox::indicator {
    width: 15px; height: 15px;
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 4px;
    background: #1a2a6e;
}
QCheckBox::indicator:checked {
    background: #f0c040;
    border-color: #f0c040;
}

#or_label { color: rgba(255,255,255,0.30); font-size: 12px; }

/* ── Dialog styles (Register / Recovery) ── */
QDialog { background: #0d2260; }
QFormLayout QLabel { font-weight: 600; color: rgba(255,255,255,0.70); }
QDialogButtonBox QPushButton {
    background: #f0c040;
    color: #0d2260;
    border: none;
    border-radius: 7px;
    padding: 8px 18px;
    font-weight: 700;
}
QDialogButtonBox QPushButton:hover { background: #e5b830; }
QDialogButtonBox QPushButton[text="Cancel"] {
    background: rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.65);
    border: 1px solid rgba(255,255,255,0.15);
}
QDialogButtonBox QPushButton[text="Cancel"]:hover {
    background: rgba(255,255,255,0.12);
    color: #fff;
}
"""


def _make_shadow(radius=20, color="#00000030"):
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(radius)
    fx.setOffset(0, 8)
    fx.setColor(QColor(color))
    return fx


def _styled_input(placeholder: str, password: bool = False) -> QLineEdit:
    edit = QLineEdit()
    edit.setObjectName("login_input")
    edit.setPlaceholderText(placeholder)
    edit.setFixedHeight(44)
    if password:
        edit.setEchoMode(QLineEdit.EchoMode.Password)
    return edit


# ── PGPC logo mark (painted) ──────────────────────────────────────────────────

class _LogoBadge(QWidget):
    """Gold-bordered circular logo placeholder."""
    def __init__(self, size: int = 72):
        super().__init__()
        self.setFixedSize(size, size)
        self._s = size

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Outer gold ring
        p.setPen(QPen(QColor("#f0c040"), 3))
        p.setBrush(QBrush(QColor("#1a2a6e")))
        p.drawEllipse(2, 2, self._s - 4, self._s - 4)
        # Cross icon in white
        p.setPen(QPen(QColor("white"), max(3, self._s // 10),
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        cx, cy = self._s // 2, self._s // 2
        arm = self._s // 3
        p.drawLine(cx, cy - arm, cx, cy + arm)
        p.drawLine(cx - arm, cy, cx + arm, cy)


class RegisterDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Account")
        self.setFixedWidth(420)
        self.setStyleSheet(LOGIN_STYLE)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("Create Account")
        title.setObjectName("login_title")
        layout.addWidget(title)

        sub = QLabel("Fill in the details to register a new clinic account.")
        sub.setObjectName("login_sub")
        sub.setWordWrap(True)
        layout.addWidget(sub)
        layout.addSpacing(6)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.username_input = _styled_input("Enter username")
        self.password_input = _styled_input("Enter password", password=True)
        self.confirm_input  = _styled_input("Confirm password", password=True)

        form.addRow(self._lbl("Username"),         self.username_input)
        form.addRow(self._lbl("Password"),         self._pwd_row(self.password_input))
        form.addRow(self._lbl("Confirm Password"), self._pwd_row(self.confirm_input))
        layout.addLayout(form)
        layout.addSpacing(8)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _lbl(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("field_label")
        return lbl

    def _pwd_row(self, field: QLineEdit) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(field)
        toggle = QPushButton("Show")
        toggle.setObjectName("show_btn")
        toggle.setFixedSize(52, 44)
        toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle.clicked.connect(lambda: self._toggle(field, toggle))
        row.addWidget(toggle)
        return container

    def _toggle(self, field: QLineEdit, btn: QPushButton):
        if field.echoMode() == QLineEdit.EchoMode.Password:
            field.setEchoMode(QLineEdit.EchoMode.Normal)
            btn.setText("Hide")
        else:
            field.setEchoMode(QLineEdit.EchoMode.Password)
            btn.setText("Show")

    def get_data(self):
        return (
            self.username_input.text().strip(),
            self.password_input.text(),
            self.confirm_input.text(),
        )


# ── Main Login Window ─────────────────────────────────────────────────────────

class LoginWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Campus Clinic System")
        self.setMinimumSize(900, 600)
        self._dashboard_window = None
        self._init_ui()
        self._load_remembered_user()
        _shortcut = QShortcut(QKeySequence("Ctrl+Shift+Alt+R"), self)
        _shortcut.activated.connect(self._open_recovery_dialog)
        self.showMaximized()

    def _init_ui(self):
        self.setStyleSheet(LOGIN_STYLE)

        BASE_DIR = getattr(sys, "_MEIPASS",
                           os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        class BackgroundWidget(QWidget):
            def __init__(self_, image_path):
                super().__init__()
                self_.setObjectName("login_bg")
                self_._pixmap = QPixmap(image_path)

            def paintEvent(self_, event):
                painter = QPainter(self_)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                scaled = self_._pixmap.scaled(
                    self_.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                x = (scaled.width()  - self_.width())  // 2
                y = (scaled.height() - self_.height()) // 2
                painter.drawPixmap(0, 0, scaled, x, y, self_.width(), self_.height())
                painter.fillRect(self_.rect(), QColor(0, 0, 0, 130))

        bg = BackgroundWidget(os.path.join(BASE_DIR, "pgpc_bg.jpg"))
        self.setCentralWidget(bg)

        outer = QVBoxLayout(bg)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── Card ──────────────────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("login_card")
        card.setFixedWidth(440)
        card.setGraphicsEffect(_make_shadow(48, "#00000055"))

        lay = QVBoxLayout(card)
        lay.setContentsMargins(44, 36, 44, 32)
        lay.setSpacing(0)

        # Logo
        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_path = os.path.join(BASE_DIR, "pgpc_logo.jpg")
        if os.path.exists(logo_path):
            original = QPixmap(logo_path).scaled(
                72, 72,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            rounded = QPixmap(72, 72)
            rounded.fill(Qt.GlobalColor.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            from PyQt6.QtGui import QPainterPath
            path = QPainterPath()
            path.addEllipse(0, 0, 72, 72)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, original)
            # Gold ring
            painter.setClipping(False)
            painter.setPen(QPen(QColor("#f0c040"), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(2, 2, 68, 68)
            painter.end()
            logo_lbl = QLabel()
            logo_lbl.setPixmap(rounded)
        else:
            logo_lbl = QLabel()
            logo_lbl.setFixedSize(72, 72)
            badge = _LogoBadge(72)
            logo_row.addWidget(badge)
            logo_row.addStretch()
            lay.addLayout(logo_row)
            lay.addSpacing(16)
            logo_lbl = None  # skip below

        if logo_lbl:
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_row.addWidget(logo_lbl)
            logo_row.addStretch()
            lay.addLayout(logo_row)
            lay.addSpacing(16)

        title = QLabel("Campus Clinic System")
        title.setObjectName("login_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        sub = QLabel("Padre Garcia Polytechnic College")
        sub.setObjectName("login_sub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)
        lay.addSpacing(26)

        # Username
        lay.addWidget(self._field_label("Username"))
        lay.addSpacing(5)
        self.username_input = _styled_input("Enter your username")
        lay.addWidget(self.username_input)
        lay.addSpacing(14)

        # Password
        lay.addWidget(self._field_label("Password"))
        lay.addSpacing(5)
        self.password_input = _styled_input("Enter your password", password=True)
        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(6)
        pwd_row.addWidget(self.password_input)
        self.password_toggle = QPushButton("Show")
        self.password_toggle.setObjectName("show_btn")
        self.password_toggle.setFixedSize(52, 44)
        self.password_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.password_toggle.clicked.connect(self._toggle_password)
        pwd_row.addWidget(self.password_toggle)
        lay.addLayout(pwd_row)
        lay.addSpacing(12)

        # Options row
        opts_row = QHBoxLayout()
        self.remember_cb = QCheckBox("Remember me")
        self.remember_cb.setObjectName("remember_cb")
        opts_row.addWidget(self.remember_cb)
        opts_row.addStretch()
        forgot = QPushButton("Forgot password?")
        forgot.setObjectName("forgot_link")
        forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        forgot.clicked.connect(self._forgot_password)
        opts_row.addWidget(forgot)
        lay.addLayout(opts_row)
        lay.addSpacing(20)

        # Sign In
        sign_in = QPushButton("Sign In")
        sign_in.setObjectName("sign_in_btn")
        sign_in.setFixedHeight(46)
        sign_in.setCursor(Qt.CursorShape.PointingHandCursor)
        sign_in.clicked.connect(self.login)
        self.password_input.returnPressed.connect(self.login)
        self.username_input.returnPressed.connect(self.login)
        lay.addWidget(sign_in)
        lay.addSpacing(18)

        # Divider
        div_row = QHBoxLayout()
        for i in range(2):
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet("background: rgba(255,255,255,0.10); max-height: 1px; border: none;")
            div_row.addWidget(line, 1)
            if i == 0:
                or_lbl = QLabel("or")
                or_lbl.setObjectName("or_label")
                or_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                or_lbl.setFixedWidth(28)
                div_row.addWidget(or_lbl)
        lay.addLayout(div_row)
        lay.addSpacing(14)

        create_btn = QPushButton("Create New Account")
        create_btn.setObjectName("create_btn")
        create_btn.setFixedHeight(44)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self.open_register_dialog)
        lay.addWidget(create_btn)
        lay.addSpacing(16)

        ver = QLabel("Version 1.1.0  •  © 2024 PGPC")
        ver.setObjectName("version_label")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ver)

        outer.addWidget(card)

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("field_label")
        return lbl

    # ── Remember Me ──────────────────────────────────────────────────────────

    _REMEMBER_FILE = os.path.join(
        os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "remember.json",
    )

    def _load_remembered_user(self):
        try:
            with open(self._REMEMBER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            username = data.get("username", "")
            if username:
                self.username_input.setText(username)
                self.remember_cb.setChecked(True)
                self.password_input.setFocus()
        except (FileNotFoundError, ValueError, KeyError):
            pass

    def _save_remembered_user(self, username: str):
        try:
            os.makedirs(os.path.dirname(self._REMEMBER_FILE), exist_ok=True)
            with open(self._REMEMBER_FILE, "w", encoding="utf-8") as f:
                json.dump({"username": username}, f)
        except OSError:
            pass

    def _clear_remembered_user(self):
        try:
            with open(self._REMEMBER_FILE, "w", encoding="utf-8") as f:
                json.dump({"username": ""}, f)
        except OSError:
            pass

    def _forgot_password(self):
        QMessageBox.information(
            self, "Forgot Password",
            "Please contact your administrator to reset your password."
        )

    def _toggle_password(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.password_toggle.setText("Hide")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_toggle.setText("Show")

    # ── Auth ──────────────────────────────────────────────────────────────────

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if authenticate(username, password):
            if self.remember_cb.isChecked():
                self._save_remembered_user(username)
            else:
                self._clear_remembered_user()
            self.open_dashboard(username)
            return
        QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

    def _open_recovery_dialog(self):
        if not recovery_key_exists():
            QMessageBox.warning(self, "Recovery Unavailable",
                                "No recovery key has been set up for this installation.")
            return

        step1 = QDialog(self)
        step1.setWindowTitle("Admin Recovery — Step 1 of 2")
        step1.setFixedWidth(420)
        step1.setStyleSheet(LOGIN_STYLE)
        lay1 = QVBoxLayout(step1)
        lay1.setContentsMargins(28, 24, 28, 24)
        lay1.setSpacing(12)

        t1 = QLabel("Admin Account Recovery")
        t1.setObjectName("login_title")
        lay1.addWidget(t1)

        i1 = QLabel("Enter the recovery key shown when the system was first set up.")
        i1.setWordWrap(True)
        i1.setObjectName("login_sub")
        lay1.addWidget(i1)

        key_input = QLineEdit()
        key_input.setObjectName("login_input")
        key_input.setFixedHeight(44)
        key_input.setPlaceholderText("RC-XXXX-XXXX-XXXX-XXXX")
        lay1.addWidget(key_input)

        btns1 = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns1.accepted.connect(step1.accept)
        btns1.rejected.connect(step1.reject)
        lay1.addWidget(btns1)

        if step1.exec() != QDialog.DialogCode.Accepted:
            return
        if not verify_recovery_key(key_input.text()):
            QMessageBox.warning(self, "Recovery Failed", "Incorrect recovery key.")
            return

        users = read_csv(USERS_CSV)
        if not users:
            QMessageBox.warning(self, "No Accounts", "No user accounts exist yet.")
            return

        step2 = QDialog(self)
        step2.setWindowTitle("Admin Recovery — Step 2 of 2")
        step2.setFixedWidth(420)
        step2.setStyleSheet(LOGIN_STYLE)
        lay2 = QVBoxLayout(step2)
        lay2.setContentsMargins(28, 24, 28, 24)
        lay2.setSpacing(12)

        t2 = QLabel("Reset Account Password")
        t2.setObjectName("login_title")
        lay2.addWidget(t2)

        i2 = QLabel("Recovery key verified. Select the account and enter a new password.")
        i2.setWordWrap(True)
        i2.setObjectName("login_sub")
        lay2.addWidget(i2)

        form2 = QFormLayout()
        form2.setSpacing(10)

        user_combo = QComboBox()
        user_combo.addItems([u["username"] for u in users])
        form2.addRow(QLabel("Account:"), user_combo)

        new_pw = QLineEdit()
        new_pw.setObjectName("login_input")
        new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        new_pw.setFixedHeight(44)
        new_pw.setPlaceholderText("New password (min 6 characters)")
        form2.addRow(QLabel("New password:"), new_pw)

        confirm_pw = QLineEdit()
        confirm_pw.setObjectName("login_input")
        confirm_pw.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_pw.setFixedHeight(44)
        confirm_pw.setPlaceholderText("Confirm new password")
        form2.addRow(QLabel("Confirm:"), confirm_pw)

        lay2.addLayout(form2)

        btns2 = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns2.accepted.connect(step2.accept)
        btns2.rejected.connect(step2.reject)
        lay2.addWidget(btns2)

        if step2.exec() != QDialog.DialogCode.Accepted:
            return

        username  = user_combo.currentText()
        password1 = new_pw.text()
        password2 = confirm_pw.text()

        if len(password1) < 6:
            QMessageBox.warning(step2, "Too Short", "Password must be at least 6 characters.")
            return
        if password1 != password2:
            QMessageBox.warning(step2, "Mismatch", "Passwords do not match.")
            return

        if reset_user_password(username, password1):
            QMessageBox.information(self, "Password Reset",
                                    f"Password for '{username}' has been reset.")
        else:
            QMessageBox.critical(self, "Error", "Failed to reset the password.")

    def open_dashboard(self, username: str):
        self._dashboard_window = DashboardWindow(username=username,
                                                 logout_callback=self._on_logout)
        self._dashboard_window.show()
        self.hide()

    def open_register_dialog(self):
        dialog = RegisterDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        username, password, confirm = dialog.get_data()
        try:
            register_user(username, password, confirm)
        except ValueError as exc:
            QMessageBox.warning(self, "Registration Failed", str(exc))
            return
        QMessageBox.information(self, "Registration Complete",
                                "Account created successfully. You may now log in.")

    def _on_logout(self):
        self.username_input.clear()
        self.password_input.clear()
        self.showMaximized()


# =============================================================================
