"""
users_page.py  –  Admin-only user management page.
Shows users.csv in a table (password shown as masked dots).
Admin can: Add, Edit (username / reset password / role), and Delete users.
"""
import csv
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from backend.auth import hash_password, find_user
from backend.config import USERS_CSV, ROLES
from backend.database import read_csv, write_csv
from ui.pages.base_page import BasePage

# =============================================================================
_HEADERS = ["username", "password_hash", "role"]


class _UserDialog(QDialog):
    """Shared dialog for Add and Edit.  Pass existing_user=None for Add."""

    def __init__(self, parent=None, existing_user: dict | None = None,
                 locked_username: str | None = None):
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QFrame, QScrollArea
        super().__init__(parent)
        self._is_edit = existing_user is not None
        title = "Edit User" if self._is_edit else "Add User"
        self.setWindowTitle(title)

        def _lbl(text):
            l = QLabel(text)
            l.setMinimumWidth(160)
            l.setStyleSheet("font-weight: 600; color: #5a6480; font-size: 12px;")
            return l

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # --- Username ---
        self._username_edit = QLineEdit()
        if self._is_edit:
            self._username_edit.setText(existing_user.get("username", ""))
            if locked_username and existing_user.get("username") == locked_username:
                self._username_edit.setReadOnly(True)
                self._username_edit.setToolTip("Cannot rename your own account.")
        form.addRow(_lbl("Username:"), self._username_edit)

        # --- Password ---
        pw_label = "New Password (blank = keep):" if self._is_edit else "Password:"
        self._pw_edit = QLineEdit()
        self._pw_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_edit.setPlaceholderText("min 6 characters")
        form.addRow(_lbl(pw_label), self._pw_edit)

        self._pw2_edit = QLineEdit()
        self._pw2_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw2_edit.setPlaceholderText("repeat password")
        form.addRow(_lbl("Confirm Password:"), self._pw2_edit)

        # --- Role ---
        self._role_combo = QComboBox()
        self._role_combo.addItems(ROLES)
        if self._is_edit:
            cur_role = existing_user.get("role", "viewer")
            idx = self._role_combo.findText(cur_role)
            if idx >= 0:
                self._role_combo.setCurrentIndex(idx)
        form.addRow(_lbl("Role:"), self._role_combo)

        # ── Title bar ─────────────────────────────────────────────────────
        title_bar = QWidget()
        title_bar.setObjectName("modal_titlebar")
        title_bar.setFixedHeight(46)
        tb_lay = QHBoxLayout(title_bar)
        tb_lay.setContentsMargins(18, 0, 18, 0)
        tb_lbl = QLabel(title)
        tb_lbl.setObjectName("modal_title")
        tb_lay.addWidget(tb_lbl)

        # ── Body + scroll ─────────────────────────────────────────────────
        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(20, 16, 20, 8)
        body_lay.addLayout(form)
        body_lay.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(body)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #d0d8ef;")

        # ── Button row ────────────────────────────────────────────────────
        btn_row = QWidget()
        btn_row.setStyleSheet("background: #ffffff;")
        btn_lay = QHBoxLayout(btn_row)
        btn_lay.setContentsMargins(20, 12, 20, 14)
        btn_lay.setSpacing(10)
        btn_lay.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(36)
        cancel_btn.setMinimumWidth(90)
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("Save")
        ok_btn.setObjectName("btn_primary")
        ok_btn.setFixedHeight(36)
        ok_btn.setMinimumWidth(90)
        ok_btn.clicked.connect(self._validate_and_accept)

        btn_lay.addWidget(cancel_btn)
        btn_lay.addWidget(ok_btn)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(title_bar)
        lay.addWidget(scroll, 1)
        lay.addWidget(divider)
        lay.addWidget(btn_row)

        self.setMinimumWidth(460)
        self.resize(460, 340)

    # ------------------------------------------------------------------ #

    def _validate_and_accept(self):
        username = self._username_edit.text().strip()
        pw       = self._pw_edit.text()
        pw2      = self._pw2_edit.text()
        role     = self._role_combo.currentText()

        if not username:
            QMessageBox.warning(self, "Validation", "Username cannot be empty.")
            return

        if not self._is_edit or pw:          # new user, or changing password
            if pw != pw2:
                QMessageBox.warning(self, "Validation", "Passwords do not match.")
                return
            if not self._is_edit and not pw:
                QMessageBox.warning(self, "Validation", "Password is required for a new user.")
                return
            if pw and len(pw) < 6:
                QMessageBox.warning(self, "Validation", "Password must be at least 6 characters.")
                return

        self.accept()

    # ------------------------------------------------------------------ #

    def get_values(self):
        """Return (username, plaintext_password_or_None, role)."""
        pw = self._pw_edit.text() or None
        return (
            self._username_edit.text().strip(),
            pw,
            self._role_combo.currentText(),
        )


# =============================================================================


class UsersPage(BasePage):
    """Admin-only page to view, add, edit, and delete user accounts."""

    # Visible columns: password shown as masked dots
    _DISPLAY_HEADERS = ["Username", "Password", "Role"]

    def __init__(self, role: str = "viewer", username: str = ""):
        self._role     = role.lower()
        self._username = username          # currently logged-in user
        super().__init__("User Management")
        self._init_content()
        self.load_data()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    def _init_content(self):
        # Search bar
        search_row = QHBoxLayout()
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("🔍  Search users…")
        self._search_box.setClearButtonEnabled(True)
        self._search_box.textChanged.connect(self._apply_filter)
        search_row.addWidget(self._search_box)
        self.body_layout.addLayout(search_row)

        # Action buttons
        btn_row = QHBoxLayout()

        self._add_btn = QPushButton("➕  Add User")
        self._add_btn.clicked.connect(self._on_add)
        btn_row.addWidget(self._add_btn)

        self._edit_btn = QPushButton("✏️  Edit User")
        self._edit_btn.clicked.connect(self._on_edit)
        btn_row.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("🗑  Delete User")
        self._delete_btn.clicked.connect(self._on_delete)
        btn_row.addWidget(self._delete_btn)

        btn_row.addStretch()
        self.body_layout.addLayout(btn_row)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(len(self._DISPLAY_HEADERS))
        self._table.setHorizontalHeaderLabels(self._DISPLAY_HEADERS)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self.body_layout.addWidget(self._table)

        self._all_rows: list[dict] = []

    # ------------------------------------------------------------------ #
    # Data helpers
    # ------------------------------------------------------------------ #

    def load_data(self):
        self._all_rows = read_csv(USERS_CSV)
        self._populate_table(self._all_rows)

    def _populate_table(self, rows: list[dict]):
        self._table.setRowCount(0)
        for row in rows:
            r = self._table.rowCount()
            self._table.insertRow(r)
            # col 0 – username
            self._table.setItem(r, 0, QTableWidgetItem(str(row.get("username", ""))))
            # col 1 – password (always masked; hash stored, plaintext unknown)
            pw_item = QTableWidgetItem("••••••••")
            pw_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(r, 1, pw_item)
            # col 2 – role
            self._table.setItem(r, 2, QTableWidgetItem(str(row.get("role", ""))))

    def _apply_filter(self, text: str):
        text = text.lower().strip()
        if not text:
            self._populate_table(self._all_rows)
            return
        filtered = [
            row for row in self._all_rows
            if any(text in str(v).lower() for v in row.values())
        ]
        self._populate_table(filtered)

    def _selected_username(self) -> str | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.text() if item else None

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def _on_add(self):
        dlg = _UserDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        username, password, role = dlg.get_values()

        # Duplicate check
        all_users = read_csv(USERS_CSV)
        if any(u.get("username") == username for u in all_users):
            QMessageBox.warning(self, "Duplicate", f"Username '{username}' already exists.")
            return

        new_row = {
            "username":      username,
            "password_hash": hash_password(password),
            "role":          role,
        }
        all_users.append(new_row)
        write_csv(USERS_CSV, all_users, _HEADERS)
        QMessageBox.information(self, "Added", f"User '{username}' has been added.")
        self.load_data()

    def _on_edit(self):
        target = self._selected_username()
        if not target:
            QMessageBox.warning(self, "No Selection", "Please select a user to edit.")
            return

        all_users = read_csv(USERS_CSV)
        existing  = next((u for u in all_users if u.get("username") == target), None)
        if not existing:
            QMessageBox.warning(self, "Not Found", f"User '{target}' not found.")
            return

        dlg = _UserDialog(parent=self, existing_user=existing,
                          locked_username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        new_username, new_password, new_role = dlg.get_values()

        # Username uniqueness check (skip if unchanged)
        if new_username != target:
            if any(u.get("username") == new_username for u in all_users):
                QMessageBox.warning(self, "Duplicate",
                                    f"Username '{new_username}' already exists.")
                return

        updated_users = []
        for u in all_users:
            if u.get("username") == target:
                u["username"] = new_username
                if new_password:                        # only update if supplied
                    u["password_hash"] = hash_password(new_password)
                u["role"] = new_role
            updated_users.append(u)

        write_csv(USERS_CSV, updated_users, _HEADERS)
        QMessageBox.information(self, "Updated", f"User '{new_username}' has been updated.")
        self.load_data()

    def _on_delete(self):
        target = self._selected_username()
        if not target:
            QMessageBox.warning(self, "No Selection", "Please select a user to delete.")
            return

        if target == self._username:
            QMessageBox.warning(
                self, "Cannot Delete",
                "You cannot delete your own account while you are logged in.",
            )
            return

        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the user '{target}'?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        all_users = read_csv(USERS_CSV)
        updated   = [u for u in all_users if u.get("username") != target]

        if len(updated) == len(all_users):
            QMessageBox.warning(self, "Not Found", f"User '{target}' was not found.")
            return

        write_csv(USERS_CSV, updated, _HEADERS)
        QMessageBox.information(self, "Deleted", f"User '{target}' has been deleted.")
        self.load_data()

# =============================================================================
