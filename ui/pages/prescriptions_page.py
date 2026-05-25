import os, sys
from datetime import datetime as _dt

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from backend.config import *
from backend.utils import *
from backend.database import *
from backend.auth import *
from backend.inventory import *
from backend.queue_logic import *
from ui.pages.table_page import TablePage
from ui.pages.shared_modal import (
    MODAL_STYLE, section_div, field_lbl, inp, combo, date_edit,
    build_modal_shell, add_footer_buttons, confirm_delete_dialog,
)

# =============================================================================

_FREQ = [
    "", "Once daily", "Twice daily", "Three times daily", "Four times daily",
    "Every 4 hours", "Every 6 hours", "Every 8 hours", "Every 12 hours",
    "As needed", "Weekly", "Bi-weekly", "Monthly",
]


class PrescriptionFormDialog(QDialog):

    def __init__(self, parent=None, data: dict | None = None, username: str = ""):
        super().__init__(parent)
        self._data     = data or {}
        self._is_edit  = bool(data)
        self._username = username
        self._fields   = {}
        self.setWindowTitle("Edit Prescription" if self._is_edit else "Add Prescription")
        self._init_ui()

    def _init_ui(self):
        body_lay, foot_lay, _ = build_modal_shell(
            self,
            title="Edit Prescription" if self._is_edit else "Add Prescription",
            icon="✎ " if self._is_edit else "💊  ",
        )

        # ── SECTION: PRESCRIPTION ─────────────────────────────────────────────
        body_lay.addWidget(section_div("PRESCRIPTION"))

        two = QGridLayout()
        two.setHorizontalSpacing(14)
        two.setVerticalSpacing(4)

        two.addWidget(field_lbl("Prescription ID"), 0, 0)
        rxid = inp(readonly=True, value=self._data.get("rx_id", ""))
        two.addWidget(rxid, 1, 0)
        self._fields["rx_id"] = rxid

        two.addWidget(field_lbl("Patient ID", required=True), 0, 1)
        pid = inp("e.g. PT-0001", value=self._data.get("patient_id", ""))
        two.addWidget(pid, 1, 1)
        self._fields["patient_id"] = pid
        body_lay.addLayout(two)
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Date Issued", required=True))
        dt = date_edit(self._data.get("date", ""))
        body_lay.addWidget(dt)
        self._fields["date"] = dt
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Medicine Name", required=True))
        med = inp("e.g. Amoxicillin 500mg",
                  value=self._data.get("drug_name", ""))
        body_lay.addWidget(med)
        self._fields["drug_name"] = med
        body_lay.addSpacing(4)

        dos_row = QGridLayout()
        dos_row.setHorizontalSpacing(14)
        dos_row.setVerticalSpacing(4)

        dos_row.addWidget(field_lbl("Dosage", required=True), 0, 0)
        dosage = inp("e.g. 500mg", value=self._data.get("dosage", ""))
        dos_row.addWidget(dosage, 1, 0)
        self._fields["dosage"] = dosage

        dos_row.addWidget(field_lbl("Quantity"), 0, 1)
        qty = inp("e.g. 30 tablets", value=self._data.get("quantity", ""))
        dos_row.addWidget(qty, 1, 1)
        self._fields["quantity"] = qty
        body_lay.addLayout(dos_row)
        body_lay.addSpacing(4)

        freq_row = QGridLayout()
        freq_row.setHorizontalSpacing(14)
        freq_row.setVerticalSpacing(4)

        freq_row.addWidget(field_lbl("Frequency"), 0, 0)
        freq = combo(_FREQ, current=self._data.get("frequency", ""))
        freq_row.addWidget(freq, 1, 0)
        self._fields["frequency"] = freq

        freq_row.addWidget(field_lbl("Duration (days)"), 0, 1)
        dur = inp("e.g. 7", value=self._data.get("duration_days", ""))
        freq_row.addWidget(dur, 1, 1)
        self._fields["duration_days"] = dur
        body_lay.addLayout(freq_row)

        # ── SECTION: NOTES ────────────────────────────────────────────────────
        body_lay.addWidget(section_div("NOTES"))

        body_lay.addWidget(field_lbl("Instructions"))
        instructions = inp("e.g. Take after meals",
                           value=self._data.get("instructions", ""))
        body_lay.addWidget(instructions)
        self._fields["instructions"] = instructions
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Prescribed By"))
        by = inp(readonly=True, value=self._data.get("prescribed_by", self._username))
        body_lay.addWidget(by)
        self._fields["prescribed_by"] = by

        body_lay.addStretch()
        save_btn = add_footer_buttons(foot_lay, self, "💾  Issue Prescription")
        save_btn.clicked.connect(self._on_accept)

    def _on_accept(self):
        data = self.get_data()
        required = {"patient_id": "Patient ID",
                    "date": "Date Issued",
                    "drug_name": "Medicine Name",
                    "dosage": "Dosage"}
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


# =============================================================================

class PrescriptionsPage(TablePage):
    DEFAULT_HEADERS = [
        "rx_id", "patient_id", "date", "drug_name", "dosage",
        "frequency", "duration_days", "quantity", "instructions", "prescribed_by",
    ]
    SENSITIVE_COLUMNS = ["drug_name", "dosage", "frequency",
                         "duration_days", "quantity", "instructions"]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Prescriptions", PRESCRIPTIONS_CSV, role, username)

    def on_add(self):
        dlg = PrescriptionFormDialog(self, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        row = dlg.get_data()
        if not row.get("rx_id"):
            row["rx_id"] = new_id("RX")
        append_csv(PRESCRIPTIONS_CSV, row, headers=self.DEFAULT_HEADERS)
        log_audit(self._username, "ADD", "Prescriptions", row["rx_id"],
                  f"patient={row.get('patient_id','')}")
        self.load_data()
        self.show_toast(f"Prescription {row['rx_id']} issued", "success")

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a prescription to edit.")
            return
        dlg = PrescriptionFormDialog(self, row_data, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dlg.get_data()
        rxid = row_data.get("rx_id")
        ok   = update_row(PRESCRIPTIONS_CSV,
                          lambda r: r.get("rx_id") == rxid,
                          updated, headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Update Failed",
                                "The selected prescription could not be updated.")
            return
        log_audit(self._username, "EDIT", "Prescriptions", rxid, "")
        self.load_data()
        self.show_toast(f"Prescription {rxid} updated", "info")

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection",
                                "Please select a prescription to delete.")
            return
        rxid = row_data.get("rx_id", "")
        drug = row_data.get("drug_name", rxid)
        if not confirm_delete_dialog(self, f"{drug} ({rxid})"):
            return
        ok = delete_rows(PRESCRIPTIONS_CSV,
                         lambda r: r.get("rx_id") == rxid,
                         headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Delete Failed",
                                "The selected prescription could not be deleted.")
            return
        log_audit(self._username, "DELETE", "Prescriptions", rxid, drug)
        self.load_data()
        self.show_toast(f"Prescription {rxid} deleted", "error")
