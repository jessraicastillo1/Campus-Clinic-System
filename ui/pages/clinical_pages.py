import os, sys
from datetime import datetime as _dt

from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTimeEdit, QVBoxLayout, QWidget,
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
# APPOINTMENTS
# =============================================================================

_APPT_STATUS  = ["Scheduled", "Confirmed", "Completed", "Cancelled"]
_APPT_PURPOSE = [
    "", "Consultation", "Vaccination", "Prescription Pickup",
    "Clearance", "Dental", "Physical Exam", "Follow-up", "Other",
]
_APPT_STATUS_COLOURS = {
    "Scheduled":  ("#e8edf8", "#1a3a8a"),
    "Confirmed":  ("#e6f4ec", "#1a7a4a"),
    "Completed":  ("#e6f4ec", "#1a7a4a"),
    "Cancelled":  ("#fdecea", "#c0392b"),
}


class AppointmentFormDialog(QDialog):

    def __init__(self, parent=None, data: dict | None = None, username: str = ""):
        super().__init__(parent)
        self._data     = data or {}
        self._is_edit  = bool(data)
        self._username = username
        self._fields   = {}
        self.setWindowTitle("Edit Appointment" if self._is_edit else "Add Appointment")
        self._init_ui()

    def _init_ui(self):
        body_lay, foot_lay, _ = build_modal_shell(
            self,
            title="Edit Appointment" if self._is_edit else "Schedule Appointment",
            icon="✎ " if self._is_edit else "📅  ",
        )

        two = QGridLayout()
        two.setHorizontalSpacing(14)
        two.setVerticalSpacing(4)

        two.addWidget(field_lbl("Appointment ID"), 0, 0)
        aid = inp(readonly=True, value=self._data.get("appt_id", ""))
        two.addWidget(aid, 1, 0)
        self._fields["appt_id"] = aid

        two.addWidget(field_lbl("Patient ID", required=True), 0, 1)
        pid = inp("e.g. PT-0001", value=self._data.get("patient_id", ""))
        two.addWidget(pid, 1, 1)
        self._fields["patient_id"] = pid
        body_lay.addLayout(two)
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Date & Time", required=True))
        dt_row = QHBoxLayout()
        dt_row.setSpacing(8)
        raw = self._data.get("date_time", "")
        date_part = raw.split(" ")[0] if raw else ""
        time_part = raw.split(" ")[1] if " " in raw else "08:00"
        self._date_w = date_edit(date_part)
        self._time_w = QTimeEdit()
        self._time_w.setDisplayFormat("HH:mm")
        self._time_w.setFixedHeight(36)
        try:
            tp = time_part.split(":")
            self._time_w.setTime(QTime(int(tp[0]), int(tp[1])))
        except Exception:
            self._time_w.setTime(QTime(8, 0))
        dt_row.addWidget(self._date_w)
        dt_row.addWidget(self._time_w)
        body_lay.addLayout(dt_row)
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Purpose", required=True))
        purpose = combo(_APPT_PURPOSE, current=self._data.get("reason", ""))
        body_lay.addWidget(purpose)
        self._fields["reason"] = purpose
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Status"))
        status_row = QHBoxLayout()
        self._status_cb = combo(_APPT_STATUS,
                                current=self._data.get("status", "Scheduled"))
        self._status_cb.setFixedWidth(180)
        self._status_pill = QLabel("Scheduled")
        self._status_pill.setStyleSheet(
            "background: #e8edf8; color: #1a3a8a; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )
        self._status_cb.currentTextChanged.connect(self._update_pill)
        status_row.addWidget(self._status_cb)
        status_row.addWidget(self._status_pill)
        status_row.addStretch()
        body_lay.addLayout(status_row)
        self._fields["status"] = self._status_cb
        self._update_pill(self._status_cb.currentText())

        body_lay.addSpacing(4)
        body_lay.addWidget(field_lbl("Notes"))
        notes = inp("Additional notes", value=self._data.get("notes", ""))
        body_lay.addWidget(notes)
        self._fields["notes"] = notes

        body_lay.addSpacing(4)
        body_lay.addWidget(field_lbl("Doctor / Staff"))
        staff = inp(readonly=True, value=self._data.get("created_by", self._username))
        body_lay.addWidget(staff)
        self._fields["created_by"] = staff

        body_lay.addStretch()
        save_btn = add_footer_buttons(foot_lay, self, "💾  Save Appointment")
        save_btn.clicked.connect(self._on_accept)

    def _update_pill(self, text: str):
        bg, fg = _APPT_STATUS_COLOURS.get(text, ("#f0f1f5", "#5a6480"))
        self._status_pill.setText(text)
        self._status_pill.setStyleSheet(
            f"background: {bg}; color: {fg}; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )

    def _on_accept(self):
        data = self.get_data()
        # Validate date not in past
        if self._date_w.date() < QDate.currentDate():
            QMessageBox.warning(self, "Invalid Date",
                                "Appointment Date cannot be in the past.")
            return
        required = {"patient_id": "Patient ID", "reason": "Purpose"}
        missing = [v for k, v in required.items() if not data.get(k, "").strip()]
        if missing:
            QMessageBox.warning(self, "Required Fields",
                                "Please fill in:\n• " + "\n• ".join(missing))
            return
        self.accept()

    def get_data(self) -> dict:
        result = {}
        d = self._date_w.date().toString("yyyy-MM-dd")
        t = self._time_w.time().toString("HH:mm")
        result["date_time"] = f"{d} {t}"
        for k, w in self._fields.items():
            if isinstance(w, QComboBox):
                result[k] = w.currentText().strip()
            elif isinstance(w, QDateEdit):
                result[k] = w.date().toString("yyyy-MM-dd")
            else:
                result[k] = w.text().strip()
        return result


class AppointmentsPage(TablePage):
    DEFAULT_HEADERS = [
        "appt_id", "patient_id", "date_time", "reason",
        "status", "notes", "created_by",
    ]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Appointments", APPOINTMENTS_CSV, role, username)

    def on_add(self):
        dlg = AppointmentFormDialog(self, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        row = dlg.get_data()
        if not row.get("appt_id"):
            row["appt_id"] = new_id("AP")
        append_csv(APPOINTMENTS_CSV, row, headers=self.DEFAULT_HEADERS)
        log_audit(self._username, "ADD", "Appointments", row["appt_id"],
                  f"patient={row.get('patient_id','')}")
        self.load_data()
        self.show_toast(f"Appointment {row['appt_id']} scheduled", "success")

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select an appointment to edit.")
            return
        dlg = AppointmentFormDialog(self, row_data, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dlg.get_data()
        aid = row_data.get("appt_id")
        ok  = update_row(APPOINTMENTS_CSV,
                         lambda r: r.get("appt_id") == aid,
                         updated, headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Update Failed",
                                "The selected appointment could not be updated.")
            return
        log_audit(self._username, "EDIT", "Appointments", aid, "")
        self.load_data()
        self.show_toast(f"Appointment {aid} updated", "info")

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection",
                                "Please select an appointment to delete.")
            return
        aid = row_data.get("appt_id", "")
        if not confirm_delete_dialog(self, f"appointment {aid}"):
            return
        ok = delete_rows(APPOINTMENTS_CSV,
                         lambda r: r.get("appt_id") == aid,
                         headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Delete Failed",
                                "The selected appointment could not be deleted.")
            return
        log_audit(self._username, "DELETE", "Appointments", aid, "")
        self.load_data()
        self.show_toast(f"Appointment {aid} deleted", "error")


# =============================================================================
# QUEUE
# =============================================================================

_PRIORITY_COLOURS = {
    "Normal":    ("#e8edf8", "#1a3a8a"),
    "Urgent":    ("#fdf6e3", "#c9a227"),
    "Emergency": ("#fdecea", "#c0392b"),
}
_STATUS_Q_COLOURS = {
    "Waiting":     ("#fdf6e3", "#c9a227"),
    "In Progress": ("#e8edf8", "#1a3a8a"),
    "Done":        ("#e6f4ec", "#1a7a4a"),
    "No Show":     ("#fdecea", "#c0392b"),
}


class QueueFormDialog(QDialog):

    def __init__(self, parent=None, data: dict | None = None, username: str = ""):
        super().__init__(parent)
        self._data     = data or {}
        self._is_edit  = bool(data)
        self._username = username
        self._fields   = {}
        self.setWindowTitle("Edit Queue Entry" if self._is_edit else "Add to Queue")
        self._init_ui()

    def _init_ui(self):
        body_lay, foot_lay, _ = build_modal_shell(
            self,
            title="Edit Queue Entry" if self._is_edit else "Add to Queue",
            icon="✎ " if self._is_edit else "🔢  ",
        )

        two = QGridLayout()
        two.setHorizontalSpacing(14)
        two.setVerticalSpacing(4)

        two.addWidget(field_lbl("Queue ID"), 0, 0)
        qid = inp(readonly=True, value=self._data.get("queue_id", ""))
        two.addWidget(qid, 1, 0)
        self._fields["queue_id"] = qid

        two.addWidget(field_lbl("Patient ID", required=True), 0, 1)
        pid = inp("e.g. PT-0001", value=self._data.get("patient_id", ""))
        two.addWidget(pid, 1, 1)
        self._fields["patient_id"] = pid
        body_lay.addLayout(two)
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Check-in Time", required=True))
        ci = inp("e.g. 08:30",
                 value=self._data.get("checkin_time",
                                     _dt.now().strftime("%Y-%m-%d %H:%M")))
        body_lay.addWidget(ci)
        self._fields["checkin_time"] = ci
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Purpose", required=True))
        purpose = combo(
            ["Consultation", "Vaccination", "Prescription Pickup", "Clearance", "Emergency"],
            current=self._data.get("purpose", "Consultation"),
        )
        body_lay.addWidget(purpose)
        self._fields["purpose"] = purpose
        body_lay.addSpacing(4)

        # Priority with pill
        body_lay.addWidget(field_lbl("Priority"))
        pri_row = QHBoxLayout()
        self._pri_cb = combo(["Normal", "Urgent", "Emergency"],
                             current=self._data.get("priority", "Normal"))
        self._pri_cb.setFixedWidth(180)
        self._pri_pill = QLabel("Normal")
        self._pri_pill.setStyleSheet(
            "background: #e8edf8; color: #1a3a8a; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )
        self._pri_cb.currentTextChanged.connect(self._update_pri_pill)
        pri_row.addWidget(self._pri_cb)
        pri_row.addWidget(self._pri_pill)
        pri_row.addStretch()
        body_lay.addLayout(pri_row)
        self._fields["priority"] = self._pri_cb
        self._update_pri_pill(self._pri_cb.currentText())

        body_lay.addSpacing(4)
        body_lay.addWidget(field_lbl("Status"))
        status = combo(["Waiting", "In Progress", "Done", "No Show"],
                       current=self._data.get("status", "Waiting"))
        body_lay.addWidget(status)
        self._fields["status"] = status

        body_lay.addSpacing(4)
        body_lay.addWidget(field_lbl("Notes"))
        notes = inp("Additional notes", value=self._data.get("notes", ""))
        body_lay.addWidget(notes)
        self._fields["notes"] = notes

        body_lay.addStretch()
        save_btn = add_footer_buttons(foot_lay, self, "💾  Add to Queue")
        save_btn.clicked.connect(self._on_accept)

    def _update_pri_pill(self, text: str):
        bg, fg = _PRIORITY_COLOURS.get(text, ("#f0f1f5", "#5a6480"))
        self._pri_pill.setText(text)
        self._pri_pill.setStyleSheet(
            f"background: {bg}; color: {fg}; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )
        # Auto-set status to In Progress if Emergency
        if hasattr(self, "_fields") and "status" in self._fields:
            if text == "Emergency":
                self._fields["status"].setCurrentText("In Progress")

    def _on_accept(self):
        data = self.get_data()
        required = {"patient_id": "Patient ID",
                    "checkin_time": "Check-in Time",
                    "purpose": "Purpose"}
        missing = [v for k, v in required.items() if not data.get(k, "").strip()]
        if missing:
            QMessageBox.warning(self, "Required Fields",
                                "Please fill in:\n• " + "\n• ".join(missing))
            return
        self.accept()

    def get_data(self) -> dict:
        result = {}
        for k, w in self._fields.items():
            if isinstance(w, QComboBox):
                result[k] = w.currentText().strip()
            else:
                result[k] = w.text().strip()
        return result


class QueuePage(TablePage):
    DEFAULT_HEADERS = [
        "queue_id", "patient_id", "checkin_time",
        "purpose", "priority", "status", "notes",
    ]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Queue", QUEUE_CSV, role, username)

    def load_data(self):
        super().load_data()
        self._colour_by_priority()

    def _colour_by_priority(self):
        if "priority" not in self._headers:
            return
        col = self._headers.index("priority")
        _fg = {
            "Emergency": "#c0392b",
            "Urgent":    "#c9a227",
        }
        for row_idx in range(self._table.rowCount()):
            item = self._table.item(row_idx, col)
            if not item:
                continue
            fg = _fg.get(item.text())
            if fg:
                for c in range(self._table.columnCount()):
                    i = self._table.item(row_idx, c)
                    if i:
                        i.setForeground(QColor(fg))

    def on_add(self):
        dlg = QueueFormDialog(self, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        row = dlg.get_data()
        pid      = row.get("patient_id", "").strip()
        priority = row.get("priority", "Normal")
        added    = add_to_queue(pid, priority)
        if not added:
            QMessageBox.warning(self, "Already in Queue",
                                f"Patient '{pid}' already has an active queue entry.")
            return
        log_audit(self._username, "ADD", "Queue", pid, f"priority={priority}")
        self.load_data()
        self.show_toast(f"Patient {pid} added to queue", "success")

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a queue entry to edit.")
            return
        dlg = QueueFormDialog(self, row_data, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dlg.get_data()
        qid = row_data.get("queue_id")
        ok  = update_row(QUEUE_CSV, lambda r: r.get("queue_id") == qid,
                         updated, headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Update Failed",
                                "The selected entry could not be updated.")
            return
        log_audit(self._username, "EDIT", "Queue", qid, "")
        self.load_data()
        self.show_toast(f"Queue entry {qid} updated", "info")

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select an entry to delete.")
            return
        qid = row_data.get("queue_id", "")
        if not confirm_delete_dialog(self, f"queue entry {qid}"):
            return
        ok = delete_rows(QUEUE_CSV, lambda r: r.get("queue_id") == qid,
                         headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Delete Failed",
                                "The selected entry could not be deleted.")
            return
        log_audit(self._username, "DELETE", "Queue", qid, "")
        self.load_data()
        self.show_toast(f"Queue entry {qid} deleted", "error")


# =============================================================================
# EMERGENCY CONTACTS
# =============================================================================

_REL = ["", "Parent", "Sibling", "Spouse", "Child",
        "Relative", "Friend", "Guardian", "Other"]


class EmergencyFormDialog(QDialog):

    def __init__(self, parent=None, data: dict | None = None, username: str = ""):
        super().__init__(parent)
        self._data     = data or {}
        self._is_edit  = bool(data)
        self._username = username
        self._fields   = {}
        self.setWindowTitle("Edit Contact" if self._is_edit else "Add Emergency Contact")
        self._init_ui()

    def _init_ui(self):
        body_lay, foot_lay, _ = build_modal_shell(
            self,
            title="Edit Emergency Contact" if self._is_edit else "Add Emergency Contact",
            icon="✎ " if self._is_edit else "🚨  ",
            titlebar_id="modal_titlebar_red",
        )

        two = QGridLayout()
        two.setHorizontalSpacing(14)
        two.setVerticalSpacing(4)

        two.addWidget(field_lbl("Patient ID", required=True), 0, 0)
        pid = inp("e.g. PT-0001", value=self._data.get("patient_id", ""))
        two.addWidget(pid, 1, 0)
        self._fields["patient_id"] = pid

        two.addWidget(field_lbl("Relationship"), 0, 1)
        rel = combo(_REL, current=self._data.get("relationship", ""))
        two.addWidget(rel, 1, 1)
        self._fields["relationship"] = rel
        body_lay.addLayout(two)
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Contact Name", required=True))
        cn = inp("Full name of emergency contact",
                 value=self._data.get("contact_name", ""))
        body_lay.addWidget(cn)
        self._fields["contact_name"] = cn
        body_lay.addSpacing(4)

        ph_row = QGridLayout()
        ph_row.setHorizontalSpacing(14)
        ph_row.setVerticalSpacing(4)

        ph_row.addWidget(field_lbl("Primary Phone", required=True), 0, 0)
        ph = inp("e.g. 09XX-XXX-XXXX", value=self._data.get("phone", ""))
        ph_row.addWidget(ph, 1, 0)
        self._fields["phone"] = ph

        ph_row.addWidget(field_lbl("Alternate Phone"), 0, 1)
        ap = inp("e.g. 09XX-XXX-XXXX", value=self._data.get("alt_phone", ""))
        ph_row.addWidget(ap, 1, 1)
        self._fields["alt_phone"] = ap
        body_lay.addLayout(ph_row)

        body_lay.addStretch()
        save_btn = add_footer_buttons(foot_lay, self, "💾  Save Contact")
        save_btn.clicked.connect(self._on_accept)

    def _on_accept(self):
        data = self.get_data()
        required = {"patient_id": "Patient ID",
                    "contact_name": "Contact Name",
                    "phone": "Primary Phone"}
        missing = [v for k, v in required.items() if not data.get(k, "").strip()]
        if missing:
            QMessageBox.warning(self, "Required Fields",
                                "Please fill in:\n• " + "\n• ".join(missing))
            return
        self.accept()

    def get_data(self) -> dict:
        result = {}
        for k, w in self._fields.items():
            if isinstance(w, QComboBox):
                result[k] = w.currentText().strip()
            else:
                result[k] = w.text().strip()
        return result


class EmergencyPage(TablePage):
    DEFAULT_HEADERS = [
        "patient_id", "contact_name", "relationship", "phone", "alt_phone",
    ]
    SENSITIVE_COLUMNS = ["phone", "alt_phone"]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Emergency Contacts", EMERGENCY_CSV, role, username)

    def on_add(self):
        dlg = EmergencyFormDialog(self, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        row = dlg.get_data()
        append_csv(EMERGENCY_CSV, row, headers=self.DEFAULT_HEADERS)
        self.load_data()
        self.show_toast("Emergency contact saved", "success")

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a contact to edit.")
            return
        dlg = EmergencyFormDialog(self, row_data, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dlg.get_data()
        ok = update_row(
            EMERGENCY_CSV,
            lambda r: (r.get("contact_name") == row_data.get("contact_name") and
                       r.get("patient_id")   == row_data.get("patient_id")),
            updated, headers=self.DEFAULT_HEADERS,
        )
        if not ok:
            QMessageBox.warning(self, "Update Failed",
                                "The selected contact could not be updated.")
            return
        self.load_data()
        self.show_toast("Contact updated", "info")

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a contact to delete.")
            return
        name = row_data.get("contact_name", "this contact")
        if not confirm_delete_dialog(self, name):
            return
        ok = delete_rows(
            EMERGENCY_CSV,
            lambda r: (r.get("contact_name") == row_data.get("contact_name") and
                       r.get("patient_id")   == row_data.get("patient_id")),
            headers=self.DEFAULT_HEADERS,
        )
        if not ok:
            QMessageBox.warning(self, "Delete Failed",
                                "The selected contact could not be deleted.")
            return
        self.load_data()
        self.show_toast(f"Contact {name} deleted", "error")


# =============================================================================
# INVENTORY
# =============================================================================

_UNIT      = ["", "Tablet", "Capsule", "Bottle", "Box", "Piece", "Pack", "Vial", "Sachet"]
_CATEGORY  = ["Medicine", "Supplies", "Equipment"]
_INV_STATUS_COLOURS = {
    "Healthy": ("#e6f4ec", "#1a7a4a"),
    "Low":     ("#fdf6e3", "#c9a227"),
    "Out":     ("#fdecea", "#c0392b"),
}


def _inv_status(qty: str, reorder: str) -> str:
    try:
        q, r = float(qty), float(reorder)
        if q <= 0:
            return "Out"
        if q <= r:
            return "Low"
        return "Healthy"
    except (ValueError, TypeError):
        return "Healthy"


class InventoryFormDialog(QDialog):

    def __init__(self, parent=None, data: dict | None = None, username: str = ""):
        super().__init__(parent)
        self._data     = data or {}
        self._is_edit  = bool(data)
        self._username = username
        self._fields   = {}
        self.setWindowTitle("Edit Item" if self._is_edit else "Add Inventory Item")
        self._init_ui()

    def _init_ui(self):
        body_lay, foot_lay, _ = build_modal_shell(
            self,
            title="Edit Inventory Item" if self._is_edit else "Add Inventory Item",
            icon="✎ " if self._is_edit else "📦  ",
        )

        two = QGridLayout()
        two.setHorizontalSpacing(14)
        two.setVerticalSpacing(4)

        two.addWidget(field_lbl("Item ID"), 0, 0)
        iid = inp(readonly=True, value=self._data.get("item_id", ""))
        two.addWidget(iid, 1, 0)
        self._fields["item_id"] = iid

        two.addWidget(field_lbl("Category", required=True), 0, 1)
        cat = combo(_CATEGORY, current=self._data.get("category", "Medicine"))
        two.addWidget(cat, 1, 1)
        self._fields["category"] = cat
        body_lay.addLayout(two)
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Item Name", required=True))
        name = inp("e.g. Paracetamol 500mg", value=self._data.get("name", ""))
        body_lay.addWidget(name)
        self._fields["name"] = name
        body_lay.addSpacing(4)

        qty_row = QGridLayout()
        qty_row.setHorizontalSpacing(14)
        qty_row.setVerticalSpacing(4)

        qty_row.addWidget(field_lbl("Quantity", required=True), 0, 0)
        self._qty_inp = inp("e.g. 100", value=self._data.get("quantity", ""))
        qty_row.addWidget(self._qty_inp, 1, 0)
        self._fields["quantity"] = self._qty_inp

        qty_row.addWidget(field_lbl("Unit", required=True), 0, 1)
        unit = combo(_UNIT, current=self._data.get("unit", ""))
        qty_row.addWidget(unit, 1, 1)
        self._fields["unit"] = unit
        body_lay.addLayout(qty_row)
        body_lay.addSpacing(4)

        reord_row = QGridLayout()
        reord_row.setHorizontalSpacing(14)
        reord_row.setVerticalSpacing(4)

        reord_row.addWidget(field_lbl("Reorder Level"), 0, 0)
        self._reord_inp = inp("e.g. 20", value=self._data.get("reorder_level", ""))
        reord_row.addWidget(self._reord_inp, 1, 0)
        self._fields["reorder_level"] = self._reord_inp

        # Live status pill
        reord_row.addWidget(field_lbl("Status (auto)"), 0, 1)
        self._status_pill = QLabel("Healthy")
        self._status_pill.setStyleSheet(
            "background: #e6f4ec; color: #1a7a4a; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )
        reord_row.addWidget(self._status_pill, 1, 1)
        body_lay.addLayout(reord_row)

        self._qty_inp.textChanged.connect(self._update_status)
        self._reord_inp.textChanged.connect(self._update_status)
        self._update_status()

        body_lay.addSpacing(4)

        exp_row = QGridLayout()
        exp_row.setHorizontalSpacing(14)
        exp_row.setVerticalSpacing(4)

        exp_row.addWidget(field_lbl("Expiry Date"), 0, 0)
        exp = date_edit(self._data.get("expiry_date", ""))
        exp_row.addWidget(exp, 1, 0)
        self._fields["expiry_date"] = exp

        exp_row.addWidget(field_lbl("Supplier"), 0, 1)
        sup = inp("Supplier name", value=self._data.get("supplier", ""))
        exp_row.addWidget(sup, 1, 1)
        self._fields["supplier"] = sup
        body_lay.addLayout(exp_row)

        body_lay.addSpacing(4)
        body_lay.addWidget(field_lbl("Batch / Lot #"))
        batch = inp("e.g. BL-2025-001", value=self._data.get("batch_lot", ""))
        body_lay.addWidget(batch)
        self._fields["batch_lot"] = batch

        body_lay.addStretch()
        save_btn = add_footer_buttons(foot_lay, self, "💾  Save Item")
        save_btn.clicked.connect(self._on_accept)

    def _update_status(self):
        status = _inv_status(self._qty_inp.text(), self._reord_inp.text())
        bg, fg = _INV_STATUS_COLOURS.get(status, ("#f0f1f5", "#5a6480"))
        self._status_pill.setText(status)
        self._status_pill.setStyleSheet(
            f"background: {bg}; color: {fg}; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )

    def _on_accept(self):
        data = self.get_data()
        required = {"name": "Item Name", "category": "Category",
                    "unit": "Unit", "quantity": "Quantity"}
        missing = [v for k, v in required.items() if not data.get(k, "").strip()]
        if missing:
            QMessageBox.warning(self, "Required Fields",
                                "Please fill in:\n• " + "\n• ".join(missing))
            return
        try:
            from backend.models import InventoryItem
            item   = InventoryItem(data)
            errors = item.validate()
            if errors:
                QMessageBox.warning(self, "Validation Error", "\n".join(errors))
                return
        except Exception:
            pass
        self.accept()

    def get_data(self) -> dict:
        result = {}
        for k, w in self._fields.items():
            if isinstance(w, QComboBox):
                result[k] = w.currentText().strip()
            elif isinstance(w, QDateEdit):
                result[k] = w.date().toString("yyyy-MM-dd")
            else:
                result[k] = w.text().strip()
        result["status"] = _inv_status(result.get("quantity", ""),
                                       result.get("reorder_level", ""))
        return result


class InventoryPage(TablePage):
    DEFAULT_HEADERS = [
        "item_id", "name", "category", "quantity", "unit",
        "reorder_level", "status", "expiry_date", "supplier", "batch_lot",
    ]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Inventory", INVENTORY_CSV, role, username)

    def load_data(self):
        super().load_data()
        self._highlight_alerts()

    def _highlight_alerts(self):
        if not self._headers:
            return
        qty_col    = self._headers.index("quantity")      if "quantity"      in self._headers else -1
        reord_col  = self._headers.index("reorder_level") if "reorder_level" in self._headers else -1
        expiry_col = self._headers.index("expiry_date")   if "expiry_date"   in self._headers else -1

        for row_idx in range(self._table.rowCount()):
            def cell(c):
                i = self._table.item(row_idx, c)
                return i.text() if i else ""

            is_low = False
            if qty_col >= 0 and reord_col >= 0:
                try:
                    is_low = float(cell(qty_col)) <= float(cell(reord_col))
                except (ValueError, TypeError):
                    pass

            is_expiring = False
            if expiry_col >= 0:
                try:
                    expiring, _ = is_expiring_soon(cell(expiry_col))
                    is_expiring = expiring
                except Exception:
                    pass

            color = None
            if is_expiring:
                color = "#c0392b"
            elif is_low:
                color = "#c9a227"

            if color:
                for c in range(self._table.columnCount()):
                    item = self._table.item(row_idx, c)
                    if item:
                        item.setForeground(QColor(color))

    def on_add(self):
        dlg = InventoryFormDialog(self, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        row = dlg.get_data()
        if not row.get("item_id"):
            row["item_id"] = new_id("INV")
        append_csv(INVENTORY_CSV, row, headers=self.DEFAULT_HEADERS)
        log_audit(self._username, "ADD", "Inventory",
                  row["item_id"], row.get("name", ""))
        self.load_data()
        self.show_toast(f"{row['item_id']} {row.get('name','')} added to inventory",
                        "success")

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select an item to edit.")
            return
        dlg = InventoryFormDialog(self, row_data, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dlg.get_data()
        iid = row_data.get("item_id")
        ok  = update_row(INVENTORY_CSV,
                         lambda r: r.get("item_id") == iid,
                         updated, headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Update Failed",
                                "The selected item could not be updated.")
            return
        log_audit(self._username, "EDIT", "Inventory", iid, "")
        self.load_data()
        self.show_toast(f"Inventory {iid} updated", "info")

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select an item to delete.")
            return
        iid  = row_data.get("item_id", "")
        name = row_data.get("name", iid)
        if not confirm_delete_dialog(self, f"{name} ({iid})"):
            return
        ok = delete_rows(INVENTORY_CSV,
                         lambda r: r.get("item_id") == iid,
                         headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Delete Failed",
                                "The selected item could not be deleted.")
            return
        log_audit(self._username, "DELETE", "Inventory", iid, name)
        self.load_data()
        self.show_toast(f"Item {iid} deleted", "error")
