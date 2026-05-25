"""incidents_page.py — Incident Reports CRUD with redesigned Royal Dark form.
Gold-amber #c9a227 title bar to distinguish from Emergency (red).
"""

from __future__ import annotations
import datetime

from PyQt6.QtCore    import Qt, QDate, QDateTime, QTimer
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QHBoxLayout,
    QLabel, QMessageBox, QTimeEdit, QWidget,
)

from backend.config    import INCIDENTS_CSV
from backend.utils     import new_id
from backend.database  import append_csv, update_row, delete_rows
from ui.pages.table_page   import TablePage
from ui.pages._dialog_base import _BaseFormDialog

# =============================================================================

class IncidentFormDialog(_BaseFormDialog):

    TYPE_OPTIONS   = ["Accident", "Illness", "Behavioral", "Facility", "Other"]
    STATUS_OPTIONS = ["Open", "Under Review", "Resolved", "Closed"]

    def __init__(self, parent=None, data=None, session_user=""):
        super().__init__(parent, data, session_user)
        self._build_ui("Edit Incident" if data else "Add Incident", bar_color="#c9a227")

    def _populate_form(self):
        d = self._data
        now = datetime.datetime.now()

        self._section("Auto")
        self._f_inc_id = self._ro_field(d.get("incident_id", "") or "Auto-generated")
        self._row("Incident ID", self._f_inc_id)
        self._f_patient = self._patient_combo(d.get("patient_id", ""))
        self._row("Patient ID", self._f_patient)
        self._spacer()

        self._section("Incident")

        # date + time side by side
        raw_dt = d.get("date", "") or now.strftime("%Y-%m-%d")
        raw_time = d.get("time", now.strftime("%H:%M"))

        dt_w = QWidget()
        dt_l = QHBoxLayout(dt_w)
        dt_l.setContentsMargins(0, 0, 0, 0)
        dt_l.setSpacing(8)
        self._f_date = self._date_field(self._date_from_str(raw_dt))
        self._f_time = QTimeEdit()
        self._f_time.setDisplayFormat("HH:mm")
        self._f_time.setStyleSheet(
            "background:#f5f6fa; border:1px solid #d0d8ef; border-radius:7px;"
            " padding:7px 11px; font-size:12px; color:#1a1a2e; min-height:34px;"
        )
        try:
            tp = raw_time.split(":")
            from PyQt6.QtCore import QTime
            self._f_time.setTime(QTime(int(tp[0]), int(tp[1])))
        except Exception:
            from PyQt6.QtCore import QTime
            self._f_time.setTime(QTime.currentTime())
        dt_l.addWidget(self._f_date, 2)
        dt_l.addWidget(QLabel("Time:"))
        dt_l.addWidget(self._f_time, 1)
        self._row("Date & Time", dt_w, required=True)

        self._f_location = self._text_field("e.g. Gymnasium, Room 204", d.get("location", ""))
        self._row("Location", self._f_location)

        self._f_type = self._combo(self.TYPE_OPTIONS, d.get("type", ""))
        self._row("Type", self._f_type, required=True)

        self._f_description = self._textarea(3, "Describe what happened…")
        self._f_description.setPlainText(d.get("description", ""))
        self._row("Description", self._f_description, required=True)

        self._f_action = self._textarea(2, "Immediate action taken…")
        self._f_action.setPlainText(d.get("actions_taken", ""))
        self._row("Immediate Action", self._f_action)
        self._spacer()

        self._section("Follow-Up")

        # follow-up checkbox
        self._f_followup_chk = QCheckBox("Follow-up Required")
        self._f_followup_chk.setStyleSheet(
            "font-size:12px; font-weight:600; color:#1a1a2e;"
        )
        self._f_followup_chk.setChecked(bool(d.get("followup_required", False)))
        self._body_layout.addWidget(self._f_followup_chk)

        self._f_followup_date = self._date_field(
            self._date_from_str(d.get("followup_date", "")))
        self._f_followup_date.setVisible(self._f_followup_chk.isChecked())
        self._row("Follow-up Date", self._f_followup_date)
        self._f_followup_chk.toggled.connect(self._f_followup_date.setVisible)

        self._f_status = self._combo(self.STATUS_OPTIONS, d.get("status", "Open"))
        self._row("Status", self._f_status)

        self._f_reported_by = self._ro_field(
            d.get("reported_by", self._session_user) or self._session_user)
        self._row("Reported By", self._f_reported_by)

    def _on_save(self):
        if not self._f_description.toPlainText().strip():
            QMessageBox.warning(self, "Required", "Description is required.")
            return
        if not self._f_type.currentText():
            QMessageBox.warning(self, "Required", "Type is required.")
            return
        iid = self._data.get("incident_id", "") or new_id("INC")
        self._saved_id = iid
        self._show_toast(f"Incident {iid} reported successfully", color="#c9a227")
        QTimer.singleShot(400, self.accept)

    def get_data(self):
        from PyQt6.QtCore import QTime
        return {
            "incident_id":       self._data.get("incident_id", "") or getattr(self, "_saved_id", new_id("INC")),
            "patient_id":        self._patient_id_from_combo(self._f_patient),
            "date":              self._f_date.date().toString("yyyy-MM-dd"),
            "time":              self._f_time.time().toString("HH:mm"),
            "location":          self._f_location.text().strip(),
            "type":              self._f_type.currentText(),
            "description":       self._f_description.toPlainText().strip(),
            "actions_taken":     self._f_action.toPlainText().strip(),
            "followup_required": str(self._f_followup_chk.isChecked()),
            "followup_date":     self._f_followup_date.date().toString("yyyy-MM-dd")
                                 if self._f_followup_chk.isChecked() else "",
            "status":            self._f_status.currentText(),
            "reported_by":       self._f_reported_by.text().strip(),
        }


# =============================================================================

class IncidentsPage(TablePage):
    DEFAULT_HEADERS = [
        "incident_id", "patient_id", "date", "time", "location",
        "type", "description", "actions_taken",
        "followup_required", "followup_date", "status", "reported_by",
    ]

    def __init__(self, role="viewer", username=""):
        super().__init__("Incident Reports", INCIDENTS_CSV, role, username)

    def on_add(self):
        dialog = IncidentFormDialog(self, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        row = dialog.get_data()
        if not row.get("incident_id"):
            row["incident_id"] = new_id("INC")
        append_csv(INCIDENTS_CSV, row, headers=self.DEFAULT_HEADERS)
        self.load_data()

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Incident", "Please select an incident to edit.")
            return
        dialog = IncidentFormDialog(self, row_data, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated_row = dialog.get_data()
        iid = row_data.get("incident_id")
        updated = update_row(INCIDENTS_CSV, lambda r: r.get("incident_id") == iid,
                             updated_row, headers=self.DEFAULT_HEADERS)
        if not updated:
            QMessageBox.warning(self, "Update Failed", "The selected incident could not be updated.")
            return
        self.load_data()

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Incident", "Please select an incident to delete.")
            return
        answer = QMessageBox.question(self, "Delete Incident",
            f"Delete incident report from {row_data.get('date', '')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        iid = row_data.get("incident_id")
        deleted = delete_rows(INCIDENTS_CSV, lambda r: r.get("incident_id") == iid,
                              headers=self.DEFAULT_HEADERS)
        if not deleted:
            QMessageBox.warning(self, "Delete Failed", "The selected incident could not be deleted.")
            return
        self.load_data()
