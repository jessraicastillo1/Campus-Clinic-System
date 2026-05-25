"""absences_page.py — Excused Absences CRUD with redesigned Royal Dark form."""

from __future__ import annotations

from PyQt6.QtCore    import QDate, QTimer
from PyQt6.QtWidgets import QDialog, QMessageBox

from backend.config    import ABSENCES_CSV
from backend.utils     import new_id
from backend.database  import append_csv, update_row, delete_rows
from ui.pages.table_page   import TablePage
from ui.pages._dialog_base import _BaseFormDialog

# =============================================================================

class AbsenceFormDialog(_BaseFormDialog):

    REASON_OPTIONS = ["Sick", "Injury", "Medical Procedure", "Other"]
    CERT_OPTIONS   = ["Submitted", "Not Required", "Pending"]

    def __init__(self, parent=None, data=None, session_user=""):
        super().__init__(parent, data, session_user)
        self._build_ui("Edit Absence" if data else "Add Absence", bar_color="#1a3a8a")

    def _populate_form(self):
        d = self._data

        self._section("Auto")
        self._f_cert_id = self._ro_field(d.get("cert_id", "") or "Auto-generated")
        self._row("Absence ID", self._f_cert_id)
        self._f_patient = self._patient_combo(d.get("patient_id", ""))
        self._row("Patient ID", self._f_patient, required=True)
        self._spacer()

        self._section("Absence")
        self._f_from = self._date_field(self._date_from_str(d.get("from_date", "")))
        self._row("Date From", self._f_from, required=True)

        self._f_to = self._date_field(self._date_from_str(d.get("to_date", "")))
        self._row("Date To", self._f_to, required=True)

        self._f_total = self._ro_field("")
        self._row("Total Days", self._f_total)

        self._f_from.dateChanged.connect(self._calc_total)
        self._f_to.dateChanged.connect(self._calc_total)
        self._calc_total()

        self._f_reason = self._combo(self.REASON_OPTIONS, d.get("reason", ""))
        self._row("Reason", self._f_reason, required=True)

        self._f_cert = self._combo(self.CERT_OPTIONS, d.get("medical_cert", ""))
        self._row("Medical Certificate", self._f_cert)

        self._f_notes = self._textarea(2, "Optional notes…")
        self._f_notes.setPlainText(d.get("notes", ""))
        self._row("Notes", self._f_notes)

        self._f_recorded_by = self._ro_field(
            d.get("staff_user", self._session_user) or self._session_user)
        self._row("Recorded By", self._f_recorded_by)

    def _calc_total(self, _=None):
        from_date = self._f_from.date()
        to_date   = self._f_to.date()
        if to_date >= from_date:
            days = from_date.daysTo(to_date) + 1
            self._f_total.setText(f"{days} day{'s' if days != 1 else ''}")
        else:
            self._f_total.setText("⚠ Date To is before Date From")

    def _on_save(self):
        if not self._patient_id_from_combo(self._f_patient):
            QMessageBox.warning(self, "Required", "Patient ID is required.")
            return
        if self._f_to.date() < self._f_from.date():
            QMessageBox.warning(self, "Invalid Dates", "Date To cannot be before Date From.")
            return
        aid = self._data.get("cert_id", "") or new_id("ABS")
        self._saved_id = aid
        self._show_toast(f"Absence {aid} recorded successfully")
        QTimer.singleShot(400, self.accept)

    def get_data(self):
        return {
            "cert_id":      self._data.get("cert_id", "") or getattr(self, "_saved_id", new_id("ABS")),
            "patient_id":   self._patient_id_from_combo(self._f_patient),
            "from_date":    self._f_from.date().toString("yyyy-MM-dd"),
            "to_date":      self._f_to.date().toString("yyyy-MM-dd"),
            "reason":       self._f_reason.currentText(),
            "medical_cert": self._f_cert.currentText(),
            "notes":        self._f_notes.toPlainText().strip(),
            "staff_user":   self._f_recorded_by.text().strip(),
        }


# =============================================================================

class AbsencesPage(TablePage):
    DEFAULT_HEADERS = [
        "cert_id", "patient_id", "from_date", "to_date",
        "reason", "medical_cert", "notes", "staff_user",
    ]

    def __init__(self, role="viewer", username=""):
        super().__init__("Excused Absences", ABSENCES_CSV, role, username)

    def on_add(self):
        dialog = AbsenceFormDialog(self, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        row = dialog.get_data()
        if not row.get("cert_id"):
            row["cert_id"] = new_id("ABS")
        append_csv(ABSENCES_CSV, row, headers=self.DEFAULT_HEADERS)
        self.load_data()

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Certificate", "Please select a certificate to edit.")
            return
        dialog = AbsenceFormDialog(self, row_data, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated_row = dialog.get_data()
        updated = update_row(ABSENCES_CSV,
                             lambda r: r.get("cert_id") == row_data.get("cert_id"),
                             updated_row, headers=self.DEFAULT_HEADERS)
        if not updated:
            QMessageBox.warning(self, "Update Failed", "The selected certificate could not be updated.")
            return
        self.load_data()

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Certificate", "Please select a certificate to delete.")
            return
        answer = QMessageBox.question(self, "Delete Certificate",
            f"Delete absence certificate for patient {row_data.get('patient_id', '')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        deleted = delete_rows(ABSENCES_CSV,
                              lambda r: r.get("cert_id") == row_data.get("cert_id"),
                              headers=self.DEFAULT_HEADERS)
        if not deleted:
            QMessageBox.warning(self, "Delete Failed", "The selected certificate could not be deleted.")
            return
        self.load_data()
