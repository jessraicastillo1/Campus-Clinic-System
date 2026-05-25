import os
import sys
import csv
import datetime
import hashlib
from datetime import datetime as _dt

from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtGui import (
    QColor, QFont, QIcon, QLinearGradient, QBrush, QPainter, QPen,
)
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFormLayout, QFrame, QGraphicsDropShadowEffect, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from backend.config import *
from backend.utils import *
from backend.database import *
from backend.auth import *
from backend.inventory import *
from backend.queue_logic import *
from ui.pages import *

# =============================================================================

DASHBOARD_STYLE = """
* { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }

QMainWindow { background: #f5f6fa; }

/* ══════════════════════════════════════════
   SIDEBAR — Royal Navy
══════════════════════════════════════════ */
#sidebar {
    background: #0d2260;
    min-width: 228px;
    max-width: 228px;
}

/* Brand */
#brand_area {
    background: transparent;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}
#brand_name {
    color: #ffffff;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: -0.2px;
    line-height: 1.2;
}
#brand_sub {
    color: #f0c040;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.7px;
    text-transform: uppercase;
}

/* User pill */
#user_area {
    background: transparent;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}
#user_name  { color: #ffffff; font-size: 12px; font-weight: 700; }
#user_role  { color: rgba(255,255,255,0.45); font-size: 10px; }

/* Nav list */
QListWidget {
    background: transparent;
    border: none;
    outline: none;
    padding: 4px 0;
}
QListWidget::item {
    color: rgba(255,255,255,0.65);
    border-left: 4px solid transparent;
    padding: 7px 12px;
    margin: 0;
    font-size: 12px;
}
QListWidget::item:hover {
    background: rgba(255,255,255,0.06);
    color: #ffffff;
}
QListWidget::item:selected {
    background: #1a3a8a;
    color: #f0c040;
    font-weight: 700;
    border-left: 4px solid #f0c040;
}

/* Nav section labels */
#nav_section_lbl {
    color: rgba(255,255,255,0.35);
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.2px;
    padding: 10px 16px 2px;
    text-transform: uppercase;
}

/* Logout / Backup */
#logout_btn {
    background: transparent;
    color: rgba(255,255,255,0.55);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 7px;
    padding: 7px 12px;
    margin: 8px;
    font-size: 11px;
    text-align: left;
}
#logout_btn:hover {
    background: rgba(239,68,68,0.12);
    color: #f87171;
    border-color: rgba(239,68,68,0.30);
}

/* ══════════════════════════════════════════
   CONTENT AREA
══════════════════════════════════════════ */
#content_area { background: #f5f6fa; }

/* Topbar — Navy Light */
#topbar {
    background: #1a3a8a;
    border-bottom: none;
    min-height: 54px;
    max-height: 54px;
}
#page_title    { font-size: 15px; font-weight: 800; color: #ffffff; letter-spacing: -0.2px; }
#page_subtitle { font-size: 10px; color: rgba(255,255,255,0.55); margin-top: 1px; }

/* PGPC badge */
#pgpc_badge {
    background: rgba(240,192,64,0.18);
    border: 1px solid rgba(240,192,64,0.45);
    border-radius: 5px;
    color: #f0c040;
    font-size: 10px;
    font-weight: 800;
    padding: 4px 10px;
    letter-spacing: 0.5px;
}

/* Topbar chips */
#date_chip {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.20);
    border-radius: 6px;
    padding: 5px 10px;
    color: rgba(255,255,255,0.90);
    font-size: 10px;
    font-weight: 500;
    min-height: 28px;
    max-height: 28px;
}
#refresh_btn {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 6px;
    padding: 5px 10px;
    color: rgba(255,255,255,0.90);
    font-size: 10px;
    min-height: 28px;
    max-height: 28px;
}
#refresh_btn:hover   { background: rgba(255,255,255,0.18); }
#refresh_btn:pressed { background: rgba(255,255,255,0.08); }

/* View-Only badge */
#view_badge {
    background: rgba(240,192,64,0.12);
    border: 1px solid rgba(240,192,64,0.35);
    border-radius: 6px;
    color: #f0c040;
    font-size: 10px;
    font-weight: 700;
    padding: 5px 10px;
    min-height: 28px;
    max-height: 28px;
}

/* ══════════════════════════════════════════
   TABLE WIDGETS (dashboard sections)
══════════════════════════════════════════ */
QTableWidget {
    background: #ffffff;
    border: 1px solid #d0d8ef;
    border-radius: 8px;
    color: #1a1a2e;
    gridline-color: #e8ebf2;
    selection-background-color: #fff8e1;
    selection-color: #0d2260;
    alternate-background-color: #f5f6fa;
}
QHeaderView::section {
    background: #1a3a8a;
    color: #ffffff;
    border: none;
    border-right: 1px solid rgba(255,255,255,0.08);
    padding: 8px 12px;
    font-weight: 700;
    font-size: 11px;
}
QHeaderView::section:last { border-right: none; }
QTableWidget::item { padding: 8px 12px; font-size: 11px; color: #1a1a2e; }
QTableWidget::item:selected { background: #fff8e1; color: #0d2260; font-weight: 600; }

/* ══════════════════════════════════════════
   GENERIC BUTTONS (fallback)
══════════════════════════════════════════ */
QPushButton {
    background: #ffffff;
    color: #1a3a8a;
    border: 1.5px solid #1a3a8a;
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 700;
}
QPushButton:hover   { background: #e8edf8; }
QPushButton:pressed { background: #d0d8ef; }

/* ══════════════════════════════════════════
   MISC
══════════════════════════════════════════ */
QLabel#pageTitle { color: #0d2260; font-size: 20px; font-weight: 800; }
QWidget#content_area { background: #f5f6fa; }

QScrollBar:vertical {
    background: #e8ebf2; width: 5px; border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #b0bdd8; border-radius: 3px; min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

#dash_scroll { border: none; background: transparent; }
#dash_body   { background: #f5f6fa; }
"""


# ── Brand icon (painted cross in navy square) ─────────────────────────────────

class _BrandIcon(QWidget):
    def __init__(self, size: int = 34):
        super().__init__()
        self.setFixedSize(size, size)
        self._s = size

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Gold ring circle
        p.setBrush(QBrush(QColor("#1a2a6e")))
        p.setPen(QPen(QColor("#f0c040"), 2))
        r = self._s - 1
        p.drawEllipse(1, 1, r - 2, r - 2)
        # White cross
        p.setPen(QPen(QColor("white"), max(2, self._s // 10),
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        cx, cy = self._s // 2, self._s // 2
        arm = self._s // 3
        p.drawLine(cx, cy - arm, cx, cy + arm)
        p.drawLine(cx - arm, cy, cx + arm, cy)


# ── Avatar circle ─────────────────────────────────────────────────────────────

class _AvatarCircle(QWidget):
    def __init__(self, letter: str, size: int = 28):
        super().__init__()
        self.setFixedSize(size, size)
        self._letter = letter.upper()[:1]
        self._size   = size

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor("#1a3a8a")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, self._size, self._size)
        p.setPen(QPen(QColor("#f0c040")))
        f = QFont("Segoe UI", int(self._size * 0.38))
        f.setBold(True)
        p.setFont(f)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._letter)


# ── Nav pages ─────────────────────────────────────────────────────────────────

_NAV_PAGES = [
    ("⊞   Dashboard",         "HomePage"),
    ("👤  Patients",          "PatientPage"),
    ("📋  Medical History",   "HistoryPage"),
    ("🚨  Emergency",         "EmergencyPage"),
    ("💉  Vaccinations",      "VaccinesPage"),
    ("❤️   Vitals",            "VitalsPage"),
    ("💊  Prescriptions",     "PrescriptionsPage"),
    ("↗   Referrals",         "ReferralsPage"),
    ("📦  Inventory",         "InventoryPage"),
    ("🧪  Dispense",          "DispensePage"),
    ("📅  Appointments",      "AppointmentsPage"),
    ("🔢  Queue",             "QueuePage"),
    ("✅  Clearances",        "ClearancesPage"),
    ("🗓   Absences",          "AbsencesPage"),
    ("⚠️   Incidents",         "IncidentsPage"),
    ("🔐  Audit Log",         "AuditPage"),
    ("👥  Users",             "UsersPage"),
]

_PAGE_CLASS_MAP = {
    "HomePage":          HomePage,
    "PatientPage":       PatientPage,
    "HistoryPage":       HistoryPage,
    "EmergencyPage":     EmergencyPage,
    "VaccinesPage":      VaccinesPage,
    "VitalsPage":        VitalsPage,
    "PrescriptionsPage": PrescriptionsPage,
    "ReferralsPage":     ReferralsPage,
    "InventoryPage":     InventoryPage,
    "DispensePage":      DispensePage,
    "AppointmentsPage":  AppointmentsPage,
    "QueuePage":         QueuePage,
    "ClearancesPage":    ClearancesPage,
    "AbsencesPage":      AbsencesPage,
    "IncidentsPage":     IncidentsPage,
    "AuditPage":         AuditPage,
    "UsersPage":         UsersPage,
}

# ── Change Password dialog ────────────────────────────────────────────────────

class _ChangePasswordDialog(QDialog):
    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self._username = username
        self.setWindowTitle("Change Password")
        self.setFixedWidth(380)
        self.setStyleSheet("""
            QDialog  { background: #ffffff; }
            QLabel   { color: #1a1a2e; font-size: 12px; font-weight: 600; }
            QLineEdit {
                background: #f5f6fa; border: 1px solid #d0d8ef;
                border-radius: 7px; padding: 0 11px;
                font-size: 12px; color: #1a1a2e;
                min-height: 36px; max-height: 36px;
            }
            QLineEdit:focus { border: 2px solid #1a3a8a; }
            QDialogButtonBox QPushButton {
                background: #f0c040; color: #0d2260;
                border: none; border-radius: 6px;
                padding: 8px 18px; font-weight: 700;
            }
            QDialogButtonBox QPushButton:hover { background: #e5b830; }
            QDialogButtonBox QPushButton[text="Cancel"] {
                background: #fff; color: #1a3a8a;
                border: 1.5px solid #1a3a8a;
            }
            QDialogButtonBox QPushButton[text="Cancel"]:hover { background: #e8edf8; }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(12)

        title = QLabel("Change Password")
        title.setStyleSheet("font-size: 15px; font-weight: 800; color: #0d2260;")
        lay.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self._current = QLineEdit()
        self._current.setEchoMode(QLineEdit.EchoMode.Password)
        self._current.setPlaceholderText("Current password")

        self._new1 = QLineEdit()
        self._new1.setEchoMode(QLineEdit.EchoMode.Password)
        self._new1.setPlaceholderText("New password (min 6 characters)")

        self._new2 = QLineEdit()
        self._new2.setEchoMode(QLineEdit.EchoMode.Password)
        self._new2.setPlaceholderText("Confirm new password")

        form.addRow("Current password:", self._current)
        form.addRow("New password:",     self._new1)
        form.addRow("Confirm:",          self._new2)
        lay.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def _on_save(self):
        from backend.auth import authenticate, hash_password
        from backend.database import read_csv, write_csv

        current = self._current.text()
        new1    = self._new1.text()
        new2    = self._new2.text()

        if not authenticate(self._username, current):
            QMessageBox.warning(self, "Wrong Password", "Current password is incorrect.")
            return
        if len(new1) < 6:
            QMessageBox.warning(self, "Too Short", "New password must be at least 6 characters.")
            return
        if new1 != new2:
            QMessageBox.warning(self, "Mismatch", "New passwords do not match.")
            self._new2.clear()
            return

        rows = read_csv(USERS_CSV)
        updated = []
        for row in rows:
            if row.get("username") == self._username:
                row = dict(row)
                row["password_hash"] = hash_password(new1)
            updated.append(row)
        write_csv(USERS_CSV, updated, ["username", "password_hash", "role"])

        QMessageBox.information(self, "Success", "Password changed successfully.")
        self.accept()


# ── Dashboard Window ──────────────────────────────────────────────────────────

class DashboardWindow(QMainWindow):

    def __init__(self, username: str, logout_callback=None):
        super().__init__()
        self._username        = username
        self._logout_callback = logout_callback
        self._pages: dict     = {}
        user_data             = find_user(username)
        self._role            = user_data["role"].lower() if user_data else "viewer"
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1100, 700)
        self.showMaximized()
        self.setStyleSheet(DASHBOARD_STYLE)
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sb_lay  = QVBoxLayout(sidebar)
        sb_lay.setContentsMargins(0, 0, 0, 0)
        sb_lay.setSpacing(0)

        # Brand
        brand_w = QWidget()
        brand_w.setObjectName("brand_area")
        b_row = QHBoxLayout(brand_w)
        b_row.setContentsMargins(16, 14, 16, 14)
        b_row.setSpacing(10)
        b_row.addWidget(_BrandIcon(32))

        b_text = QVBoxLayout()
        b_text.setSpacing(1)
        bn = QLabel("Campus Clinic")
        bn.setObjectName("brand_name")
        bs = QLabel("Padre Garcia Polytechnic")
        bs.setObjectName("brand_sub")
        b_text.addWidget(bn)
        b_text.addWidget(bs)
        b_row.addLayout(b_text)
        b_row.addStretch()
        sb_lay.addWidget(brand_w)

        # User row
        user_w = QWidget()
        user_w.setObjectName("user_area")
        u_row = QHBoxLayout(user_w)
        u_row.setContentsMargins(16, 10, 16, 10)
        u_row.setSpacing(9)
        u_row.addWidget(_AvatarCircle(self._username[:1], 26))

        u_text = QVBoxLayout()
        u_text.setSpacing(1)
        un = QLabel(self._username.capitalize())
        un.setObjectName("user_name")
        role_display = {"admin": "Administrator", "staff": "Staff", "viewer": "Viewer"}
        ur = QLabel(role_display.get(self._role, self._role.capitalize()))
        ur.setObjectName("user_role")
        u_text.addWidget(un)
        u_text.addWidget(ur)
        u_row.addLayout(u_text)
        u_row.addStretch()

        chpw_btn = QPushButton("🔑")
        chpw_btn.setToolTip("Change Password")
        chpw_btn.setFixedSize(26, 26)
        chpw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        chpw_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; "
            "color: rgba(255,255,255,0.45); font-size: 13px; }"
            "QPushButton:hover { color: #f0c040; }"
        )
        chpw_btn.clicked.connect(self._on_change_password)
        u_row.addWidget(chpw_btn)
        sb_lay.addWidget(user_w)

        # Nav list
        _ADMIN_ONLY_PAGES   = {"UsersPage"}
        _VIEWER_HIDDEN_PAGES = {"AuditPage", "DispensePage", "UsersPage"}
        self._active_nav_pages = [
            (label, cls_name) for label, cls_name in _NAV_PAGES
            if not (
                (cls_name in _ADMIN_ONLY_PAGES and self._role != "admin") or
                (cls_name in _VIEWER_HIDDEN_PAGES and self._role == "viewer")
            )
        ]

        self._nav_list = QListWidget()
        for label, _ in self._active_nav_pages:
            self._nav_list.addItem(QListWidgetItem(label))
        self._nav_list.currentRowChanged.connect(self._switch_page)
        sb_lay.addWidget(self._nav_list, 1)

        # Backup (admin only)
        backup_btn = QPushButton("💾  Backup Data")
        backup_btn.setObjectName("logout_btn")
        backup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        backup_btn.clicked.connect(self._on_backup)
        if self._role != "admin":
            backup_btn.setVisible(False)
        sb_lay.addWidget(backup_btn)

        # Logout
        logout_btn = QPushButton("⏏   Logout")
        logout_btn.setObjectName("logout_btn")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self._on_logout)
        sb_lay.addWidget(logout_btn)

        root.addWidget(sidebar)

        # ── Right side ────────────────────────────────────────────────────────
        right = QWidget()
        right.setObjectName("content_area")
        r_lay = QVBoxLayout(right)
        r_lay.setContentsMargins(0, 0, 0, 0)
        r_lay.setSpacing(0)

        # Topbar
        topbar = QWidget()
        topbar.setObjectName("topbar")
        tb_row = QHBoxLayout(topbar)
        tb_row.setContentsMargins(20, 0, 20, 0)
        tb_row.setSpacing(10)

        # PGPC badge
        pgpc_badge = QLabel("PGPC")
        pgpc_badge.setObjectName("pgpc_badge")
        tb_row.addWidget(pgpc_badge)

        # Page title / subtitle
        self._title_col = QVBoxLayout()
        self._title_col.setSpacing(0)
        self._page_title_lbl = QLabel("Dashboard")
        self._page_title_lbl.setObjectName("page_title")
        self._page_sub_lbl = QLabel("Welcome to Campus Clinic Management System")
        self._page_sub_lbl.setObjectName("page_subtitle")
        self._title_col.addWidget(self._page_title_lbl)
        self._title_col.addWidget(self._page_sub_lbl)
        tb_row.addLayout(self._title_col)
        tb_row.addStretch()

        date_str  = _dt.now().strftime("%B %d, %Y")
        date_chip = QLabel(f"📅  {date_str}")
        date_chip.setObjectName("date_chip")
        tb_row.addWidget(date_chip)

        refresh_btn = QPushButton("🔄  Refresh")
        refresh_btn.setObjectName("refresh_btn")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setToolTip("Refresh current page data")
        refresh_btn.clicked.connect(self._refresh_current_page)
        tb_row.addWidget(refresh_btn)

        if self._role == "viewer":
            view_badge = QLabel("🔒  View Only")
            view_badge.setObjectName("view_badge")
            tb_row.addWidget(view_badge)

        r_lay.addWidget(topbar)

        # Stacked pages
        self._stack = QStackedWidget()
        r_lay.addWidget(self._stack, 1)
        root.addWidget(right, 1)

        for _ in self._active_nav_pages:
            self._stack.addWidget(QWidget())

        self._nav_list.setCurrentRow(0)

    # ── Page switching ────────────────────────────────────────────────────────

    def _switch_page(self, index: int):
        if not (0 <= index < len(self._active_nav_pages)):
            return
        label, class_name = self._active_nav_pages[index]
        clean_label = label.split("  ", 1)[-1].strip()
        self._page_title_lbl.setText(clean_label)
        sub = "Welcome to Campus Clinic Management System" if index == 0 \
              else f"Manage {clean_label}"
        self._page_sub_lbl.setText(sub)

        if class_name not in self._pages:
            cls = _PAGE_CLASS_MAP.get(class_name)
            if cls and cls is not HomePage:
                try:
                    page = cls(role=self._role, username=self._username)
                except TypeError:
                    try:
                        page = cls(role=self._role)
                    except TypeError:
                        page = cls()
            elif cls:
                page = cls()
            else:
                page = QWidget()
            self._pages[class_name] = page
            self._stack.insertWidget(index, page)
            placeholder = self._stack.widget(index + 1)
            if placeholder and not isinstance(
                placeholder, tuple(_PAGE_CLASS_MAP.values())
            ):
                self._stack.removeWidget(placeholder)
                placeholder.deleteLater()

        page = self._pages[class_name]
        self._stack.setCurrentWidget(page)
        if hasattr(page, "load_data"):
            try:
                page.load_data()
            except Exception:
                pass

    def _refresh_current_page(self):
        index = self._nav_list.currentRow()
        if 0 <= index < len(self._active_nav_pages):
            _, class_name = self._active_nav_pages[index]
            page = self._pages.get(class_name)
            if page and hasattr(page, "load_data"):
                try:
                    page.load_data()
                except Exception:
                    pass

    def _on_change_password(self):
        dlg = _ChangePasswordDialog(self._username, self)
        dlg.exec()

    def _on_backup(self):
        try:
            path = create_backup()
            QMessageBox.information(self, "Backup Complete",
                                    f"All data backed up to:\n{path}")
        except Exception as exc:
            QMessageBox.warning(self, "Backup Failed", str(exc))

    def _on_logout(self):
        self.close()
        if self._logout_callback:
            self._logout_callback()


# =============================================================================
