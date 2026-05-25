"""appointments_page.py — Appointments CRUD with redesigned Royal Dark form."""

from __future__ import annotations
import datetime

from PyQt6.QtCore    import Qt, QDate, QTime, QTimer
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QMessageBox,
    QTimeEdit, QWidget,
)

from backend.config    import APPOINTMENTS_CSV
from backend.utils     import new_id
from backend.database  import append_csv, update_row, delete_rows
from ui.pages.table_page   import TablePage
from ui.pages._dialog_base import _BaseFormDialog

_STATUS_COLORS = {
    "Scheduled":  "#1a3a8a",
    "Confirmed":  "#1a7a4a",
    "Completed":  "#5a6480",
    "Cancelled":  "#c0392b",
}

# =============================================================================

class AppointmentFormDialog(_BaseFormDialog):

    def __init__(self, parent=None, data=None, session_user=""):
        super().__init__(parent, data, session_user)
        self._build_ui("Edit Appointment" if data else "Add Appointment", bar_color="#1a3a8a")

    def _populate_form(self):
        d = self._data

        self._section("Auto")
        self._f_appt_id = self._ro_field(d.get("appt_id", "") or "Auto-generated")
        self._row("Appointment ID", self._f_appt_id)
        self._f_patient = self._patient_combo(d.get("patient_id", ""))
        self._row("Patient ID", self._f_patient, required=True)
        self._spacer()

        self._section("Schedule")

        raw_dt = d.get("date_time", "")
        date_part = raw_dt.split(" ")[0] if raw_dt else ""
        self._f_date = self._date_field(self._date_from_str(date_part) or QDate.currentDate())
        self._row("Appointment Date", self._f_date, required=True)

        self._f_time = QTimeEdit()
        self._f_time.setDisplayFormat("HH:mm")
        self._f_time.setStyleSheet(
            "background:#f5f6fa; border:1px solid #d0d8ef; border-radius:7px;"
            " padding:7px 11px; font-size:12px; color:#1a1a2e; min-height:34px;"
        )
        if " " in raw_dt:
            try:
                tp = raw_dt.split(" ")[1].split(":")
                self._f_time.setTime(QTime(int(tp[0]), int(tp[1])))
            except Exception:
                self._f_time.setTime(QTime(8, 0))
        else:
            self._f_time.setTime(QTime(8, 0))
        self._row("Appointment Time", self._f_time, required=True)

        self._f_purpose = self._text_field("e.g. Follow-up checkup", d.get("reason", ""))
        self._row("Purpose", self._f_purpose, required=True)

        self._f_created_by = self._ro_field(d.get("created_by", self._session_user) or self._session_user)
        self._row("Doctor / Staff", self._f_created_by)
        self._spacer()

        self._section("Status")

        # status + live pill
        status_w = QWidget()
        status_l = QHBoxLayout(status_w)
        status_l.setContentsMargins(0, 0, 0, 0)
        status_l.setSpacing(10)
        self._f_status = self._combo(list(_STATUS_COLORS.keys()), d.get("status", "Scheduled"))
        self._status_pill = QLabel()
        self._status_pill.setFixedSize(90, 26)
        self._status_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_l.addWidget(self._f_status, 1)
        status_l.addWidget(self._status_pill)
        self._f_status.currentTextChanged.connect(self._update_status_pill)
        self._update_status_pill(self._f_status.currentText())
        self._row("Status", status_w)

        self._f_notes = self._textarea(2, "Optional notes…")
        self._f_notes.setPlainText(d.get("notes", ""))
        self._row("Notes", self._f_notes)

    def _update_status_pill(self, text):
        color = _STATUS_COLORS.get(text, "#5a6480")
        self._status_pill.setText(text)
        self._status_pill.setStyleSheet(
            f"background:{color}20; color:{color}; border:1px solid {color}60;"
            " border-radius:13px; font-size:11px; font-weight:700;"
        )

    def _on_save(self):
        if not self._patient_id_from_combo(self._f_patient):
            QMessageBox.warning(self, "Required", "Patient ID is required.")
            return
        if not self._f_purpose.text().strip():
            QMessageBox.warning(self, "Required", "Purpose is required.")
            return
        if self._f_date.date() < QDate.currentDate():
            reply = QMessageBox.question(
                self, "Past Date",
                "The appointment date is in the past. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
        aid = self._data.get("appt_id", "") or new_id("APT")
        self._saved_id = aid
        self._show_toast(f"Appointment {aid} scheduled successfully")
        QTimer.singleShot(400, self.accept)

    def get_data(self):
        date_str = self._f_date.date().toString("yyyy-MM-dd")
        time_str = self._f_time.time().toString("HH:mm")
        return {
            "appt_id":    self._data.get("appt_id", "") or getattr(self, "_saved_id", new_id("APT")),
            "patient_id": self._patient_id_from_combo(self._f_patient),
            "date_time":  f"{date_str} {time_str}",
            "reason":     self._f_purpose.text().strip(),
            "status":     self._f_status.currentText(),
            "created_by": self._f_created_by.text().strip(),
            "notes":      self._f_notes.toPlainText().strip(),
        }


# =============================================================================

class AppointmentsPage(TablePage):
    DEFAULT_HEADERS = ["appt_id", "patient_id", "date_time", "reason", "status", "created_by"]

    def __init__(self, role="viewer", username=""):
        super().__init__("Appointments", APPOINTMENTS_CSV, role, username)

    def on_add(self):
        dialog = AppointmentFormDialog(self, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        row = dialog.get_data()
        if not row.get("appt_id"):
            row["appt_id"] = new_id("APT")
        append_csv(APPOINTMENTS_CSV, row, headers=self.DEFAULT_HEADERS)
        self.load_data()

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Appointment", "Please select an appointment to edit.")
            return
        dialog = AppointmentFormDialog(self, row_data, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated_row = dialog.get_data()
        updated = update_row(APPOINTMENTS_CSV,
                             lambda r: r.get("appt_id") == row_data.get("appt_id"),
                             updated_row, headers=self.DEFAULT_HEADERS)
        if not updated:
            QMessageBox.warning(self, "Update Failed", "The selected appointment could not be updated.")
            return
        self.load_data()

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Appointment", "Please select an appointment to delete.")
            return
        answer = QMessageBox.question(self, "Delete Appointment",
            f"Delete appointment for patient {row_data.get('patient_id', '')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        deleted = delete_rows(APPOINTMENTS_CSV,
                              lambda r: r.get("appt_id") == row_data.get("appt_id"),
                              headers=self.DEFAULT_HEADERS)
        if not deleted:
            QMessageBox.warning(self, "Delete Failed", "The selected appointment could not be deleted.")
            return
        self.load_data()
