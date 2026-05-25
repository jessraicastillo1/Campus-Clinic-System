import os, sys, csv, datetime
from datetime import datetime as _dt

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from backend.config import *
from backend.utils import *
from backend.database import *
from backend.auth import *
from backend.inventory import *
from backend.queue_logic import *
from ui.pages.base_page import BasePage
from ui.pages.table_page import TablePage
from ui.pages.shared_modal import (
    MODAL_STYLE, section_div, field_lbl, inp, combo, date_edit,
    build_modal_shell, add_footer_buttons, confirm_delete_dialog,
)

# =============================================================================


class HistoryFormDialog(QDialog):

    def __init__(self, parent=None, data: dict | None = None, username: str = ""):
        super().__init__(parent)
        self._data     = data or {}
        self._is_edit  = bool(data)
        self._username = username
        self._fields   = {}
        self.setWindowTitle("Edit Medical Record" if self._is_edit else "Add Medical Record")
        self._init_ui()

    def _init_ui(self):
        body_lay, foot_lay, _ = build_modal_shell(
            self,
            title="Edit Medical Record" if self._is_edit else "Add Medical Record",
            icon="✎ " if self._is_edit else "＋ ",
        )

        # ── SECTION: VISIT ────────────────────────────────────────────────────
        body_lay.addWidget(section_div("VISIT INFORMATION"))

        # Record ID (auto)
        body_lay.addWidget(field_lbl("Record ID"))
        rid = inp(readonly=True, value=self._data.get("record_id", ""))
        body_lay.addWidget(rid)
        self._fields["record_id"] = rid

        body_lay.addSpacing(4)
        body_lay.addWidget(field_lbl("Patient ID", required=True))
        pid = inp("e.g. PT-0001", value=self._data.get("patient_id", ""))
        body_lay.addWidget(pid)
        self._fields["patient_id"] = pid

        body_lay.addSpacing(4)
        body_lay.addWidget(field_lbl("Visit Date", required=True))
        vd = date_edit(self._data.get("visit_date", ""))
        body_lay.addWidget(vd)
        self._fields["visit_date"] = vd

        body_lay.addSpacing(4)
        body_lay.addWidget(field_lbl("Chief Complaint", required=True))
        complaint = inp("Describe the patient's complaint",
                        value=self._data.get("complaint", ""))
        body_lay.addWidget(complaint)
        self._fields["complaint"] = complaint

        body_lay.addSpacing(4)
        body_lay.addWidget(field_lbl("Diagnosis", required=True))
        diagnosis = inp("Clinical diagnosis", value=self._data.get("diagnosis", ""))
        body_lay.addWidget(diagnosis)
        self._fields["diagnosis"] = diagnosis

        body_lay.addSpacing(4)
        body_lay.addWidget(field_lbl("Treatment"))
        treatment = inp("Treatment administered", value=self._data.get("treatment", ""))
        body_lay.addWidget(treatment)
        self._fields["treatment"] = treatment

        body_lay.addSpacing(4)
        body_lay.addWidget(field_lbl("Notes"))
        notes = inp("Additional notes", value=self._data.get("notes", ""))
        body_lay.addWidget(notes)
        self._fields["notes"] = notes

        # ── SECTION: STAFF ────────────────────────────────────────────────────
        body_lay.addWidget(section_div("STAFF"))

        body_lay.addWidget(field_lbl("Staff User"))
        staff = inp(readonly=True, value=self._data.get("staff_user", self._username))
        body_lay.addWidget(staff)
        self._fields["staff_user"] = staff

        body_lay.addStretch()

        # Footer
        save_btn = add_footer_buttons(foot_lay, self, "💾  Save Record")
        save_btn.clicked.connect(self._on_accept)

    def _on_accept(self):
        data = self.get_data()
        required = {"patient_id": "Patient ID", "visit_date": "Visit Date",
                    "complaint": "Chief Complaint", "diagnosis": "Diagnosis"}
        missing = [v for k, v in required.items() if not data.get(k, "").strip()]
        if missing:
            QMessageBox.warning(self, "Required Fields",
                                "Please fill in:\n• " + "\n• ".join(missing))
            return
        self.accept()

    def get_data(self) -> dict:
        result = {}
        for k, w in self._fields.items():
            if isinstance(w, QDateEdit):
                result[k] = w.date().toString("yyyy-MM-dd")
            elif isinstance(w, QComboBox):
                result[k] = w.currentText().strip()
            else:
                result[k] = w.text().strip()
        return result


class HistoryPage(TablePage):
    DEFAULT_HEADERS = [
        "record_id", "patient_id", "visit_date", "complaint",
        "diagnosis", "treatment", "notes", "staff_user",
    ]
    SENSITIVE_COLUMNS = ["complaint", "diagnosis", "treatment", "notes"]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Medical History", HISTORY_CSV, role, username)

    def on_add(self):
        dlg = HistoryFormDialog(self, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        row = dlg.get_data()
        if not row.get("record_id"):
            row["record_id"] = new_id("H")
        append_csv(HISTORY_CSV, row, headers=self.DEFAULT_HEADERS)
        log_audit(self._username, "ADD", "History", row["record_id"],
                  f"patient={row.get('patient_id','')}")
        self.load_data()
        self.show_toast(f"Medical record {row['record_id']} saved", "success")

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a record to edit.")
            return
        dlg = HistoryFormDialog(self, row_data, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dlg.get_data()
        rid = row_data.get("record_id")
        ok = update_row(HISTORY_CSV, lambda r: r.get("record_id") == rid,
                        updated, headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Update Failed",
                                "The selected record could not be updated.")
            return
        log_audit(self._username, "EDIT", "History", rid, "")
        self.load_data()
        self.show_toast(f"Record {rid} updated", "info")

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a record to delete.")
            return
        rid = row_data.get("record_id", "")
        if not confirm_delete_dialog(self, f"record {rid}"):
            return
        ok = delete_rows(HISTORY_CSV, lambda r: r.get("record_id") == rid,
                         headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Delete Failed",
                                "The selected record could not be deleted.")
            return
        log_audit(self._username, "DELETE", "History", rid, "")
        self.load_data()
        self.show_toast(f"Record {rid} deleted", "error")
