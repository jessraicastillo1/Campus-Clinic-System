"""emergency_page.py — Emergency Contacts CRUD with redesigned Royal Dark form.

NOTE: This page manages emergency *contacts* (next-of-kin), not emergency incidents.
      Emergency incidents are handled by incidents_page.py.
"""

from __future__ import annotations

from PyQt6.QtCore    import QTimer
from PyQt6.QtWidgets import QDialog, QMessageBox

from backend.config    import EMERGENCY_CSV
from backend.utils     import new_id
from backend.database  import append_csv, update_row, delete_rows
from ui.pages.table_page   import TablePage
from ui.pages._dialog_base import _BaseFormDialog

# =============================================================================

class EmergencyFormDialog(_BaseFormDialog):

    RELATIONSHIP_OPTIONS = [
        "", "Parent", "Sibling", "Spouse", "Child",
        "Relative", "Friend", "Guardian", "Other",
    ]

    def __init__(self, parent=None, data=None, session_user=""):
        super().__init__(parent, data, session_user)
        self._build_ui("Edit Contact" if data else "Add Emergency Contact", bar_color="#1a3a8a")

    def _populate_form(self):
        d = self._data

        self._section("Patient")
        self._f_patient = self._patient_combo(d.get("patient_id", ""))
        self._row("Patient ID", self._f_patient, required=True)
        self._spacer()

        self._section("Contact")
        self._f_name = self._text_field("Full name", d.get("contact_name", ""))
        self._row("Contact Name", self._f_name, required=True)

        self._f_relationship = self._combo(self.RELATIONSHIP_OPTIONS, d.get("relationship", ""))
        self._row("Relationship", self._f_relationship)

        self._f_phone = self._text_field("e.g. 09XX-XXX-XXXX", d.get("phone", ""))
        self._row("Phone", self._f_phone, required=True)

        self._f_alt_phone = self._text_field("e.g. 09XX-XXX-XXXX", d.get("alt_phone", ""))
        self._row("Alt Phone", self._f_alt_phone)

    def _on_save(self):
        if not self._patient_id_from_combo(self._f_patient):
            QMessageBox.warning(self, "Required", "Patient ID is required.")
            return
        if not self._f_name.text().strip():
            QMessageBox.warning(self, "Required", "Contact Name is required.")
            return
        if not self._f_phone.text().strip():
            QMessageBox.warning(self, "Required", "Phone is required.")
            return
        self._show_toast("Emergency contact saved successfully")
        QTimer.singleShot(400, self.accept)

    def get_data(self):
        return {
            "patient_id":   self._patient_id_from_combo(self._f_patient),
            "contact_name": self._f_name.text().strip(),
            "relationship": self._f_relationship.currentText(),
            "phone":        self._f_phone.text().strip(),
            "alt_phone":    self._f_alt_phone.text().strip(),
        }


# =============================================================================

class EmergencyPage(TablePage):
    DEFAULT_HEADERS = ["patient_id", "contact_name", "relationship", "phone", "alt_phone"]
    SENSITIVE_COLUMNS = ["phone", "alt_phone"]

    def __init__(self, role="viewer", username=""):
        super().__init__("Emergency Contacts", EMERGENCY_CSV, role, username)

    def on_add(self):
        dialog = EmergencyFormDialog(self, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        row = dialog.get_data()
        append_csv(EMERGENCY_CSV, row, headers=self.DEFAULT_HEADERS)
        self.load_data()

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Contact", "Please select a contact to edit.")
            return
        dialog = EmergencyFormDialog(self, row_data, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated_row = dialog.get_data()
        updated = update_row(
            EMERGENCY_CSV,
            lambda r: r.get("contact_name") == row_data.get("contact_name")
                   and r.get("patient_id")   == row_data.get("patient_id"),
            updated_row, headers=self.DEFAULT_HEADERS)
        if not updated:
            QMessageBox.warning(self, "Update Failed", "The selected contact could not be updated.")
            return
        self.load_data()

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Contact", "Please select a contact to delete.")
            return
        answer = QMessageBox.question(self, "Delete Contact",
            f"Delete {row_data.get('contact_name', '')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        deleted = delete_rows(
            EMERGENCY_CSV,
            lambda r: r.get("contact_name") == row_data.get("contact_name")
                   and r.get("patient_id")   == row_data.get("patient_id"),
            headers=self.DEFAULT_HEADERS)
        if not deleted:
            QMessageBox.warning(self, "Delete Failed", "The selected contact could not be deleted.")
            return
        self.load_data()
