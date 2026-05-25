"""clearances_page.py — Clearances CRUD with redesigned Royal Dark form."""

from __future__ import annotations
import datetime

from PyQt6.QtCore    import Qt, QDate, QTimer
from PyQt6.QtWidgets import QComboBox, QDialog, QHBoxLayout, QLabel, QMessageBox, QWidget

from backend.config    import CLEARANCE_CSV
from backend.utils     import new_id
from backend.database  import append_csv, update_row, delete_rows
from ui.pages.table_page   import TablePage
from ui.pages._dialog_base import _BaseFormDialog

_STATUS_COLORS = {
    "Valid":    "#1a7a4a",
    "Expired":  "#c0392b",
    "Revoked":  "#5a6480",
}
_PURPOSE_OPTIONS = [
    "School Activity", "Sports", "Employment", "Medical", "Other",
]

# =============================================================================

class ClearanceFormDialog(_BaseFormDialog):

    def __init__(self, parent=None, data=None, session_user=""):
        super().__init__(parent, data, session_user)
        self._build_ui("Edit Clearance" if data else "Add Clearance", bar_color="#1a3a8a")

    def _populate_form(self):
        d = self._data

        self._section("Auto")
        self._f_clr_id = self._ro_field(d.get("clearance_id", "") or "Auto-generated")
        self._row("Clearance ID", self._f_clr_id)
        self._f_patient = self._patient_combo(d.get("patient_id", ""))
        self._row("Patient ID", self._f_patient, required=True)
        self._spacer()

        self._section("Clearance")
        self._f_date = self._date_field(self._date_from_str(d.get("date", "")))
        self._row("Date Issued", self._f_date, required=True)

        self._f_purpose = self._combo(_PURPOSE_OPTIONS, d.get("type", ""))
        self._row("Purpose", self._f_purpose, required=True)

        self._f_valid_until = self._date_field(
            self._date_from_str(d.get("valid_until", "")) or QDate.currentDate().addMonths(1))
        self._row("Valid Until", self._f_valid_until)

        self._f_remarks = self._textarea(2, "Optional remarks…")
        self._f_remarks.setPlainText(d.get("notes", ""))
        self._row("Remarks", self._f_remarks)

        self._f_issued_by = self._ro_field(d.get("staff_user", self._session_user) or self._session_user)
        self._row("Issued By", self._f_issued_by)
        self._spacer()

        self._section("Status")
        # auto-determine status based on valid_until
        initial_status = d.get("status", "Valid")
        valid_until_raw = d.get("valid_until", "")
        if valid_until_raw:
            try:
                parts = valid_until_raw.split("-")
                vu = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                if vu < QDate.currentDate():
                    initial_status = "Expired"
            except Exception:
                pass

        status_w = QWidget()
        status_l = QHBoxLayout(status_w)
        status_l.setContentsMargins(0, 0, 0, 0)
        status_l.setSpacing(10)
        self._f_status = self._combo(list(_STATUS_COLORS.keys()), initial_status)
        self._status_pill = QLabel()
        self._status_pill.setFixedSize(80, 26)
        self._status_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_l.addWidget(self._f_status, 1)
        status_l.addWidget(self._status_pill)
        self._f_status.currentTextChanged.connect(self._update_status_pill)
        self._f_valid_until.dateChanged.connect(self._auto_status)
        self._update_status_pill(self._f_status.currentText())
        self._row("Status", status_w)

    def _update_status_pill(self, text):
        color = _STATUS_COLORS.get(text, "#5a6480")
        self._status_pill.setText(text)
        self._status_pill.setStyleSheet(
            f"background:{color}20; color:{color}; border:1px solid {color}60;"
            " border-radius:13px; font-size:11px; font-weight:700;"
        )

    def _auto_status(self, date: QDate):
        if date < QDate.currentDate():
            self._f_status.setCurrentText("Expired")
        elif self._f_status.currentText() == "Expired":
            self._f_status.setCurrentText("Valid")

    def _on_save(self):
        if not self._patient_id_from_combo(self._f_patient):
            QMessageBox.warning(self, "Required", "Patient ID is required.")
            return
        cid = self._data.get("clearance_id", "") or new_id("CLR")
        self._saved_id = cid
        self._show_toast(f"Clearance {cid} issued successfully")
        QTimer.singleShot(400, self.accept)

    def get_data(self):
        return {
            "clearance_id": self._data.get("clearance_id", "") or getattr(self, "_saved_id", new_id("CLR")),
            "patient_id":   self._patient_id_from_combo(self._f_patient),
            "type":         self._f_purpose.currentText(),
            "date":         self._f_date.date().toString("yyyy-MM-dd"),
            "valid_until":  self._f_valid_until.date().toString("yyyy-MM-dd"),
            "status":       self._f_status.currentText(),
            "notes":        self._f_remarks.toPlainText().strip(),
            "staff_user":   self._f_issued_by.text().strip(),
        }


# =============================================================================

class ClearancesPage(TablePage):
    DEFAULT_HEADERS = [
        "clearance_id", "patient_id", "type", "date",
        "valid_until", "status", "notes", "staff_user",
    ]

    def __init__(self, role="viewer", username=""):
        super().__init__("Clearances", CLEARANCE_CSV, role, username)

    def on_add(self):
        dialog = ClearanceFormDialog(self, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        row = dialog.get_data()
        if not row.get("clearance_id"):
            row["clearance_id"] = new_id("CLR")
        append_csv(CLEARANCE_CSV, row, headers=self.DEFAULT_HEADERS)
        self.load_data()

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Clearance", "Please select a clearance to edit.")
            return
        dialog = ClearanceFormDialog(self, row_data, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated_row = dialog.get_data()
        updated = update_row(CLEARANCE_CSV,
                             lambda r: r.get("clearance_id") == row_data.get("clearance_id"),
                             updated_row, headers=self.DEFAULT_HEADERS)
        if not updated:
            QMessageBox.warning(self, "Update Failed", "The selected clearance could not be updated.")
            return
        self.load_data()

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Clearance", "Please select a clearance to delete.")
            return
        answer = QMessageBox.question(self, "Delete Clearance",
            f"Delete clearance for patient {row_data.get('patient_id', '')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        deleted = delete_rows(CLEARANCE_CSV,
                              lambda r: r.get("clearance_id") == row_data.get("clearance_id"),
                              headers=self.DEFAULT_HEADERS)
        if not deleted:
            QMessageBox.warning(self, "Delete Failed", "The selected clearance could not be deleted.")
            return
        self.load_data()
