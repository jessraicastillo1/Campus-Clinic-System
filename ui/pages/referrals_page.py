"""referrals_page.py — Referrals CRUD with redesigned Royal Dark form."""

from __future__ import annotations

from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtWidgets import QComboBox, QDialog, QHBoxLayout, QLabel, QMessageBox, QWidget

from backend.config    import REFERRALS_CSV
from backend.utils     import new_id
from backend.database  import append_csv, update_row, delete_rows
from ui.pages.table_page   import TablePage
from ui.pages._dialog_base import _BaseFormDialog

_PRIORITY_COLORS = {
    "Routine":   "#1a3a8a",
    "Urgent":    "#c9a227",
    "Emergency": "#c0392b",
}

# =============================================================================

class ReferralFormDialog(_BaseFormDialog):

    def __init__(self, parent=None, data=None, session_user=""):
        super().__init__(parent, data, session_user)
        self._build_ui("Edit Referral" if data else "Add Referral", bar_color="#1a3a8a")

    def _populate_form(self):
        d = self._data

        self._section("Auto")
        self._f_ref_id = self._ro_field(d.get("ref_id", "") or "Auto-generated")
        self._row("Referral ID", self._f_ref_id)
        self._f_patient = self._patient_combo(d.get("patient_id", ""))
        self._row("Patient ID", self._f_patient, required=True)
        self._spacer()

        self._section("Referral")
        self._f_date = self._date_field(self._date_from_str(d.get("date", "")))
        self._row("Date", self._f_date, required=True)

        self._f_referred_to = self._text_field("e.g. Batangas Medical Center", d.get("referred_to", ""))
        self._row("Referred To", self._f_referred_to, required=True)

        self._f_department = self._text_field("e.g. Cardiology", d.get("department", ""))
        self._row("Department", self._f_department)

        self._f_reason = self._textarea(3, "Reason for referral…")
        self._f_reason.setPlainText(d.get("reason", ""))
        self._row("Reason", self._f_reason, required=True)

        # priority + live pill
        pri_w = QWidget()
        pri_l = QHBoxLayout(pri_w)
        pri_l.setContentsMargins(0, 0, 0, 0)
        pri_l.setSpacing(10)
        self._f_priority = self._combo(list(_PRIORITY_COLORS.keys()), d.get("priority", "Routine"))
        self._priority_pill = QLabel()
        self._priority_pill.setFixedSize(90, 26)
        self._priority_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pri_l.addWidget(self._f_priority, 1)
        pri_l.addWidget(self._priority_pill)
        self._f_priority.currentTextChanged.connect(self._update_priority_pill)
        self._update_priority_pill(self._f_priority.currentText())
        self._row("Priority", pri_w)

        self._f_status = self._combo(
            ["Pending", "Sent", "Acknowledged", "Completed"], d.get("status", "Pending"))
        self._row("Status", self._f_status)
        self._spacer()

        self._section("Notes")
        self._f_notes = self._textarea(2, "Optional notes…")
        self._f_notes.setPlainText(d.get("notes", ""))
        self._row("Notes", self._f_notes)

        self._f_staff = self._ro_field(d.get("staff_user", self._session_user) or self._session_user)
        self._row("Referred By", self._f_staff)

    def _update_priority_pill(self, text):
        color = _PRIORITY_COLORS.get(text, "#1a3a8a")
        self._priority_pill.setText(text)
        self._priority_pill.setStyleSheet(
            f"background:{color}20; color:{color}; border:1px solid {color}60;"
            " border-radius:13px; font-size:11px; font-weight:700;"
        )

    def _on_save(self):
        if not self._patient_id_from_combo(self._f_patient):
            QMessageBox.warning(self, "Required", "Patient ID is required.")
            return
        if not self._f_referred_to.text().strip():
            QMessageBox.warning(self, "Required", "Referred To is required.")
            return
        if not self._f_reason.toPlainText().strip():
            QMessageBox.warning(self, "Required", "Reason is required.")
            return
        rid = self._data.get("ref_id", "") or new_id("REF")
        self._saved_id = rid
        self._show_toast(f"Referral {rid} created successfully")
        QTimer.singleShot(400, self.accept)

    def get_data(self):
        return {
            "ref_id":      self._data.get("ref_id", "") or getattr(self, "_saved_id", new_id("REF")),
            "patient_id":  self._patient_id_from_combo(self._f_patient),
            "date":        self._f_date.date().toString("yyyy-MM-dd"),
            "referred_to": self._f_referred_to.text().strip(),
            "department":  self._f_department.text().strip(),
            "reason":      self._f_reason.toPlainText().strip(),
            "priority":    self._f_priority.currentText(),
            "status":      self._f_status.currentText(),
            "notes":       self._f_notes.toPlainText().strip(),
            "staff_user":  self._f_staff.text().strip(),
        }


# =============================================================================

class ReferralsPage(TablePage):
    DEFAULT_HEADERS = [
        "ref_id", "patient_id", "date", "referred_to", "department",
        "reason", "priority", "status", "notes", "staff_user",
    ]

    def __init__(self, role="viewer", username=""):
        super().__init__("Referrals", REFERRALS_CSV, role, username)

    def on_add(self):
        dialog = ReferralFormDialog(self, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        row = dialog.get_data()
        if not row.get("ref_id"):
            row["ref_id"] = new_id("REF")
        append_csv(REFERRALS_CSV, row, headers=self.DEFAULT_HEADERS)
        self.load_data()

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Referral", "Please select a referral to edit.")
            return
        dialog = ReferralFormDialog(self, row_data, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated_row = dialog.get_data()
        updated = update_row(REFERRALS_CSV,
                             lambda r: r.get("ref_id") == row_data.get("ref_id"),
                             updated_row, headers=self.DEFAULT_HEADERS)
        if not updated:
            QMessageBox.warning(self, "Update Failed", "The selected referral could not be updated.")
            return
        self.load_data()

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Referral", "Please select a referral to delete.")
            return
        answer = QMessageBox.question(self, "Delete Referral",
            f"Delete referral to {row_data.get('referred_to', '')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        deleted = delete_rows(REFERRALS_CSV,
                              lambda r: r.get("ref_id") == row_data.get("ref_id"),
                              headers=self.DEFAULT_HEADERS)
        if not deleted:
            QMessageBox.warning(self, "Delete Failed", "The selected referral could not be deleted.")
            return
        self.load_data()
