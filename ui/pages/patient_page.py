import os
import sys
import csv
import datetime
from datetime import datetime as _dt

from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtGui import QColor, QFont, QIcon, QLinearGradient, QBrush, QPainter, QPen
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
from backend.models import Patient
from ui.pages.base_page import BasePage
from ui.pages.table_page import TablePage

# =============================================================================

PATIENT_DIALOG_STYLE = """
/* ── Dialog shell ─────────────────────────────── */
QDialog {
    background: #ffffff;
}

/* ── Titlebar ─────────────────────────────────── */
#modal_titlebar {
    background: #1a3a8a;
}
#modal_title {
    color: #ffffff;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: -0.2px;
}

/* ── Body ─────────────────────────────────────── */
#modal_body_widget { background: #ffffff; }
QScrollArea { background: #ffffff; border: none; }

/* ── Section labels ───────────────────────────── */
#section_lbl {
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 1.2px;
    color: #5a6480;
    text-transform: uppercase;
}

/* ── Field labels ─────────────────────────────── */
#field_lbl {
    font-size: 11px;
    font-weight: 700;
    color: #5a6480;
}
#req_star { color: #c0392b; font-size: 11px; font-weight: 700; }

/* ── Inputs ───────────────────────────────────── */
#form_input {
    background: #f5f6fa;
    border: 1px solid #d0d8ef;
    border-radius: 7px;
    padding: 0px 11px;
    font-size: 12px;
    color: #1a1a2e;
}
#form_input:focus { border: 2px solid #1a3a8a; background: #ffffff; }

#form_input_ro {
    background: #eef0f7;
    border: 1px dashed #b0bdd8;
    border-radius: 7px;
    padding: 0px 11px;
    font-size: 12px;
    color: #7a87a8;
}

QComboBox {
    background: #f5f6fa;
    border: 1px solid #d0d8ef;
    border-radius: 7px;
    padding: 0px 11px;
    font-size: 12px;
    color: #1a1a2e;
    min-height: 36px;
    max-height: 36px;
}
QComboBox:focus { border: 2px solid #1a3a8a; background: #ffffff; }
QComboBox::drop-down {
    border: none;
    padding-right: 10px;
    subcontrol-position: right center;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #d0d8ef;
    selection-background-color: #e8edf8;
    selection-color: #1a3a8a;
    color: #1a1a2e;
    font-size: 12px;
    outline: none;
}

QDateEdit {
    background: #f5f6fa;
    border: 1px solid #d0d8ef;
    border-radius: 7px;
    padding: 0px 11px;
    font-size: 12px;
    color: #1a1a2e;
    min-height: 36px;
    max-height: 36px;
}
QDateEdit:focus { border: 2px solid #1a3a8a; background: #ffffff; }
QDateEdit::drop-down { border: none; padding-right: 10px; }
QCalendarWidget { font-size: 12px; }

/* ── Footer ───────────────────────────────────── */
#modal_footer {
    background: #f5f6fa;
    border-top: 1px solid #d0d8ef;
}

/* ── Footer buttons ───────────────────────────── */
#btn_save {
    background: #f0c040;
    color: #0d2260;
    border: none;
    border-radius: 6px;
    padding: 9px 22px;
    font-size: 12px;
    font-weight: 800;
    min-height: 36px;
}
#btn_save:hover   { background: #e5b830; }
#btn_save:pressed { background: #d4a820; }

#btn_cancel {
    background: #ffffff;
    color: #1a3a8a;
    border: 1.5px solid #1a3a8a;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 12px;
    font-weight: 700;
    min-height: 36px;
}
#btn_cancel:hover   { background: #e8edf8; }
#btn_cancel:pressed { background: #d0d8ef; }

/* Scroll bars */
QScrollBar:vertical { background: #f0f1f5; width: 4px; border-radius: 2px; }
QScrollBar::handle:vertical { background: #c0cce0; border-radius: 2px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


def _section_divider(title: str) -> QWidget:
    """Creates a gold-underlined section header row."""
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 16, 0, 8)
    lay.setSpacing(10)

    lbl = QLabel(title)
    lbl.setObjectName("section_lbl")
    lay.addWidget(lbl)

    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet("background: #f0c040; max-height: 2px; border: none;")
    lay.addWidget(line, 1)
    return w


def _field_label(text: str, required: bool = False) -> QWidget:
    """Creates a compact field label (optionally with red asterisk)."""
    w = QWidget()
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


def _styled_input(placeholder: str = "", readonly: bool = False,
                  value: str = "") -> QLineEdit:
    edit = QLineEdit()
    edit.setObjectName("form_input_ro" if readonly else "form_input")
    edit.setFixedHeight(36)
    edit.setPlaceholderText(placeholder)
    edit.setReadOnly(readonly)
    if value:
        edit.setText(value)
    return edit


def _styled_combo(items: list, current: str = "") -> QComboBox:
    cb = QComboBox()
    cb.addItems(items)
    if current and current in items:
        cb.setCurrentText(current)
    elif current:
        cb.addItem(current)
        cb.setCurrentText(current)
    return cb


def _styled_date(value: str = "") -> QDateEdit:
    de = QDateEdit()
    de.setCalendarPopup(True)
    de.setDisplayFormat("MM/dd/yyyy")
    de.setFixedHeight(36)
    if value:
        try:
            parts = value.split("-")
            if len(parts) == 3:
                de.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
            else:
                de.setDate(QDate(2000, 1, 1))
        except (ValueError, IndexError):
            de.setDate(QDate(2000, 1, 1))
    else:
        de.setDate(QDate(2000, 1, 1))
    return de


# =============================================================================

class PatientFormDialog(QDialog):

    ROLE_TYPE_OPTIONS  = ["Student", "Faculty", "Staff", "Other"]
    GENDER_OPTIONS     = ["Male", "Female", "Other"]
    BLOOD_TYPE_OPTIONS = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"]

    def __init__(self, parent=None, data: dict | None = None):
        super().__init__(parent)
        self._data      = data or {}
        self._is_edit   = bool(data)
        self._fields    = {}

        self.setWindowTitle("Edit Patient" if self._is_edit else "Add New Patient")
        self.setFixedWidth(580)
        self.setMinimumHeight(540)
        self.setMaximumHeight(720)
        self.setStyleSheet(PATIENT_DIALOG_STYLE)
        self._init_ui()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Titlebar ──────────────────────────────────────────────────────────
        titlebar = QWidget()
        titlebar.setObjectName("modal_titlebar")
        titlebar.setFixedHeight(52)
        tb_lay = QHBoxLayout(titlebar)
        tb_lay.setContentsMargins(20, 0, 20, 0)

        icon_lbl = QLabel("✎ " if self._is_edit else "＋ ")
        icon_lbl.setStyleSheet("color: #f0c040; font-size: 16px; font-weight: 800;")
        tb_lay.addWidget(icon_lbl)

        title_lbl = QLabel("Edit Patient" if self._is_edit else "Add New Patient")
        title_lbl.setObjectName("modal_title")
        tb_lay.addWidget(title_lbl)
        tb_lay.addStretch()

        root.addWidget(titlebar)

        # ── Scrollable body ───────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        body.setObjectName("modal_body_widget")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(20, 4, 20, 12)
        body_lay.setSpacing(0)

        # Manual patient ID (must start with P, user enters suffix)
        pid = self._data.get("patient_id", "") or "P"

        # ──────────────────────────────────────────────────────────────────────
        # SECTION: PERSONAL
        # ──────────────────────────────────────────────────────────────────────
        body_lay.addWidget(_section_divider("PERSONAL INFORMATION"))

        grid_p = QGridLayout()
        grid_p.setHorizontalSpacing(14)
        grid_p.setVerticalSpacing(6)

        # Row 0: Patient ID (manual entry, P is pre-filled)
        body_lay.addWidget(_field_label("Patient ID", required=True))
        id_field = _styled_input(readonly=False, value=pid, placeholder="P001")
        body_lay.addWidget(id_field)
        self._fields["patient_id"] = id_field

        # 2-column grid: role_type | (spacer for alignment)
        two_col = QGridLayout()
        two_col.setHorizontalSpacing(14)
        two_col.setVerticalSpacing(4)

        # Role Type
        two_col.addWidget(_field_label("Role Type", required=True), 0, 0)
        role_field = _styled_combo(self.ROLE_TYPE_OPTIONS,
                                   self._data.get("role_type", "Student"))
        role_field.setFixedHeight(36)
        two_col.addWidget(role_field, 1, 0)
        self._fields["role_type"] = role_field

        # Gender
        two_col.addWidget(_field_label("Gender", required=True), 0, 1)
        gender_field = _styled_combo(self.GENDER_OPTIONS,
                                     self._data.get("gender", "Male"))
        gender_field.setFixedHeight(36)
        two_col.addWidget(gender_field, 1, 1)
        self._fields["gender"] = gender_field

        body_lay.addLayout(two_col)
        body_lay.addSpacing(4)

        two_col2 = QGridLayout()
        two_col2.setHorizontalSpacing(14)
        two_col2.setVerticalSpacing(4)

        # First Name
        two_col2.addWidget(_field_label("First Name", required=True), 0, 0)
        fname = _styled_input("Enter first name", value=self._data.get("first_name", ""))
        two_col2.addWidget(fname, 1, 0)
        self._fields["first_name"] = fname

        # Last Name
        two_col2.addWidget(_field_label("Last Name", required=True), 0, 1)
        lname = _styled_input("Enter last name", value=self._data.get("last_name", ""))
        two_col2.addWidget(lname, 1, 1)
        self._fields["last_name"] = lname

        body_lay.addLayout(two_col2)
        body_lay.addSpacing(4)

        two_col3 = QGridLayout()
        two_col3.setHorizontalSpacing(14)
        two_col3.setVerticalSpacing(4)

        # Date of Birth
        two_col3.addWidget(_field_label("Date of Birth", required=True), 0, 0)
        dob_field = _styled_date(self._data.get("Date of Birth", ""))
        two_col3.addWidget(dob_field, 1, 0)
        self._fields["Date of Birth"] = dob_field

        # Blood Type
        two_col3.addWidget(_field_label("Blood Type"), 0, 1)
        blood_field = _styled_combo(self.BLOOD_TYPE_OPTIONS,
                                    self._data.get("blood_type", ""))
        blood_field.setFixedHeight(36)
        two_col3.addWidget(blood_field, 1, 1)
        self._fields["blood_type"] = blood_field

        body_lay.addLayout(two_col3)

        # ──────────────────────────────────────────────────────────────────────
        # SECTION: MEDICAL
        # ──────────────────────────────────────────────────────────────────────
        body_lay.addWidget(_section_divider("MEDICAL INFORMATION"))

        body_lay.addWidget(_field_label("Allergies"))
        allergies_field = _styled_input(
            "e.g. Penicillin, Aspirin  (or 'None')",
            value=self._data.get("allergies", "")
        )
        body_lay.addWidget(allergies_field)
        self._fields["allergies"] = allergies_field

        body_lay.addSpacing(4)
        body_lay.addWidget(_field_label("Chronic Conditions"))
        chronic_field = _styled_input(
            "e.g. Asthma, Hypertension  (or 'None')",
            value=self._data.get("chronic_conditions", "")
        )
        body_lay.addWidget(chronic_field)
        self._fields["chronic_conditions"] = chronic_field

        # ──────────────────────────────────────────────────────────────────────
        # SECTION: CONTACT
        # ──────────────────────────────────────────────────────────────────────
        body_lay.addWidget(_section_divider("CONTACT INFORMATION"))

        two_col4 = QGridLayout()
        two_col4.setHorizontalSpacing(14)
        two_col4.setVerticalSpacing(4)

        two_col4.addWidget(_field_label("Email"), 0, 0)
        email_field = _styled_input("e.g. juan@email.com", value=self._data.get("email", ""))
        two_col4.addWidget(email_field, 1, 0)
        self._fields["email"] = email_field

        two_col4.addWidget(_field_label("Phone"), 0, 1)
        phone_field = _styled_input("e.g. 09XX-XXX-XXXX", value=self._data.get("phone", ""))
        two_col4.addWidget(phone_field, 1, 1)
        self._fields["phone"] = phone_field

        body_lay.addLayout(two_col4)
        body_lay.addSpacing(4)

        body_lay.addWidget(_field_label("Address"))
        address_field = _styled_input(
            "Street, Barangay, City", value=self._data.get("address", "")
        )
        body_lay.addWidget(address_field)
        self._fields["address"] = address_field

        body_lay.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        # ── Footer ────────────────────────────────────────────────────────────
        footer = QWidget()
        footer.setObjectName("modal_footer")
        footer.setFixedHeight(60)
        foot_lay = QHBoxLayout(footer)
        foot_lay.setContentsMargins(20, 0, 20, 0)
        foot_lay.setSpacing(10)

        req_note = QLabel("<span style='color:#c0392b;font-weight:700'>*</span>"
                          "<span style='color:#5a6480;font-size:11px'> Required fields</span>")
        req_note.setTextFormat(Qt.TextFormat.RichText)
        foot_lay.addWidget(req_note)
        foot_lay.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btn_cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        foot_lay.addWidget(cancel_btn)

        save_btn = QPushButton("💾  Save Patient")
        save_btn.setObjectName("btn_save")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_accept)
        foot_lay.addWidget(save_btn)

        root.addWidget(footer)

    # ── Validation & data ─────────────────────────────────────────────────────

    def _on_accept(self):
        data = self.get_data()
        # Required field check
        required = {
            "patient_id": "Patient ID",
            "role_type":  "Role Type",
            "first_name": "First Name",
            "last_name":  "Last Name",
            "dob":        "Date of Birth",
            "gender":     "Gender",
        }
        missing = [label for key, label in required.items() if not data.get(key, "").strip()]
        if missing:
            QMessageBox.warning(
                self, "Required Fields",
                "Please fill in the following required fields:\n• " + "\n• ".join(missing)
            )
            return
        # Validate patient ID starts with P
        patient_id = data.get("patient_id", "").strip()
        if not patient_id.startswith("P"):
            QMessageBox.warning(
                self, "Invalid Patient ID",
                "Patient ID must start with 'P' (e.g., P001, P123)."
            )
            return
        # Model validation (if available)
        try:
            patient = Patient(data)
            errors  = patient.validate()
            if errors:
                QMessageBox.warning(self, "Validation Error", "\n".join(errors))
                return
        except Exception:
            pass
        self.accept()

    def get_data(self) -> dict:
        result = {}
        for key, widget in self._fields.items():
            if isinstance(widget, QComboBox):
                result[key] = widget.currentText().strip()
            elif isinstance(widget, QDateEdit):
                result[key] = widget.date().toString("yyyy-MM-dd")
            else:
                result[key] = widget.text().strip()
        return result


# =============================================================================

class PatientPage(TablePage):

    DEFAULT_HEADERS = [
        "patient_id", "role_type", "first_name", "last_name", "Date of Birth", "gender",
        "blood_type", "allergies", "chronic_conditions", "email", "phone", "address",
    ]
    SENSITIVE_COLUMNS = [
        "Date of Birth", "blood_type", "allergies", "chronic_conditions", "email", "phone", "address",
    ]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Patients", PATIENTS_CSV, role, username)

    # ── CRUD actions ──────────────────────────────────────────────────────────

    def on_add(self):
        dialog = PatientFormDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        row = dialog.get_data()
        append_csv(PATIENTS_CSV, row, headers=self.DEFAULT_HEADERS)
        log_audit(self._username, "ADD", "Patients",
                  row["patient_id"],
                  row.get("first_name", "") + " " + row.get("last_name", ""))
        self.load_data()
        self.show_toast(f"Patient {row['patient_id']} added successfully", "success")

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a patient to edit.")
            return

        dialog = PatientFormDialog(self, row_data)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        updated_row = dialog.get_data()
        pid = row_data.get("patient_id")
        updated = update_row(
            PATIENTS_CSV,
            lambda r: r.get("patient_id") == pid,
            updated_row,
            headers=self.DEFAULT_HEADERS,
        )
        if not updated:
            QMessageBox.warning(self, "Update Failed",
                                "The selected patient could not be updated.")
            return

        log_audit(self._username, "EDIT", "Patients", pid, "")
        self.load_data()
        self.show_toast(f"Patient {pid} updated", "info")

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a patient to delete.")
            return

        name = f"{row_data.get('first_name', '')} {row_data.get('last_name', '')}".strip()
        pid  = row_data.get("patient_id", "")

        # ── Confirmation dialog ───────────────────────────────────────────────
        confirm = QDialog(self)
        confirm.setWindowTitle("Confirm Delete")
        confirm.setFixedWidth(380)
        confirm.setStyleSheet("""
            QDialog  { background: #fff; }
            QLabel   { color: #1a1a2e; }
        """)
        c_lay = QVBoxLayout(confirm)
        c_lay.setContentsMargins(0, 0, 0, 0)
        c_lay.setSpacing(0)

        # Icon area
        icon_area = QWidget()
        icon_area.setStyleSheet("background: #fff;")
        ia_lay = QVBoxLayout(icon_area)
        ia_lay.setContentsMargins(28, 28, 28, 10)
        ia_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_circle = QLabel("🗑")
        icon_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_circle.setStyleSheet("""
            background: #fdecea;
            border-radius: 27px;
            min-width: 54px; max-width: 54px;
            min-height: 54px; max-height: 54px;
            font-size: 22px;
            padding: 8px;
        """)
        ia_lay.addWidget(icon_circle, alignment=Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel("Delete Patient Record?")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #1a1a2e; margin-top: 12px;")
        ia_lay.addWidget(title_lbl)

        sub_lbl = QLabel(
            f"This will permanently delete <b>{name} ({pid})</b> "
            "and all related records.<br>This action <b>cannot be undone</b>."
        )
        sub_lbl.setWordWrap(True)
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setTextFormat(Qt.TextFormat.RichText)
        sub_lbl.setStyleSheet("font-size: 12px; color: #5a6480; line-height: 1.5; margin-top: 6px;")
        ia_lay.addWidget(sub_lbl)
        c_lay.addWidget(icon_area)

        # Footer buttons
        c_foot = QWidget()
        c_foot.setStyleSheet(
            "background: #f5f6fa; border-top: 1px solid #d0d8ef;"
            "border-bottom-left-radius: 4px; border-bottom-right-radius: 4px;"
        )
        cf_lay = QHBoxLayout(c_foot)
        cf_lay.setContentsMargins(20, 12, 20, 12)
        cf_lay.setSpacing(10)
        cf_lay.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            background: #fff; color: #1a3a8a;
            border: 1.5px solid #1a3a8a; border-radius: 6px;
            padding: 8px 20px; font-weight: 700; font-size: 12px;
        """)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(confirm.reject)
        cf_lay.addWidget(cancel_btn)

        del_btn = QPushButton("🗑  Delete Permanently")
        del_btn.setStyleSheet("""
            background: #c0392b; color: #fff;
            border: none; border-radius: 6px;
            padding: 8px 20px; font-weight: 800; font-size: 12px;
        """)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(confirm.accept)
        cf_lay.addWidget(del_btn)
        c_lay.addWidget(c_foot)

        if confirm.exec() != QDialog.DialogCode.Accepted:
            return

        deleted = delete_rows(
            PATIENTS_CSV,
            lambda r: r.get("patient_id") == pid,
            headers=self.DEFAULT_HEADERS,
        )
        if not deleted:
            QMessageBox.warning(self, "Delete Failed",
                                "The selected patient could not be deleted.")
            return

        log_audit(self._username, "DELETE", "Patients", pid, name)
        self.load_data()
        self.show_toast(f"Patient {pid} deleted", "error")


# ── Helper: get patient allergies by ID ──────────────────────────────────────

def get_patient_allergies(patient_id: str) -> str:
    for row in read_csv(PATIENTS_CSV):
        if row.get("patient_id") == patient_id:
            return row.get("allergies", "")
    return ""


# =============================================================================
