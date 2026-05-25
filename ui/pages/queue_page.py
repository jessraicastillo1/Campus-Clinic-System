"""queue_page.py — Queue CRUD with redesigned Royal Dark form."""

from __future__ import annotations
import datetime

from PyQt6.QtCore    import Qt, QDate, QTime, QTimer
from PyQt6.QtGui     import QColor
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QMessageBox,
    QTimeEdit, QWidget,
)

from backend.config    import QUEUE_CSV
from backend.utils     import new_id
from backend.database  import append_csv, update_row, delete_rows, log_audit
from backend.queue_logic import add_to_queue, QueueStatus, QueuePriority
from ui.pages.table_page   import TablePage
from ui.pages._dialog_base import _BaseFormDialog

_PRIORITY_COLORS = {
    QueuePriority.NORMAL:    "#1a3a8a",
    QueuePriority.URGENT:    "#c9a227",
    QueuePriority.EMERGENCY: "#c0392b",
}
_PURPOSE_OPTIONS = [
    "Consultation", "Vaccination", "Prescription Pickup", "Clearance", "Emergency",
]

# =============================================================================

class QueueFormDialog(_BaseFormDialog):

    def __init__(self, parent=None, data=None, session_user=""):
        super().__init__(parent, data, session_user)
        self._build_ui("Edit Queue Entry" if data else "Add to Queue", bar_color="#1a3a8a")

    def _populate_form(self):
        d = self._data

        self._section("Auto")
        self._f_queue_id = self._ro_field(d.get("queue_id", "") or "Auto-generated")
        self._row("Queue Number", self._f_queue_id)
        self._f_patient = self._patient_combo(d.get("patient_id", ""))
        self._row("Patient ID", self._f_patient, required=True)
        self._spacer()

        self._section("Queue")

        raw_dt = d.get("checkin_time", "")
        date_part = raw_dt.split(" ")[0] if raw_dt else ""
        self._f_date = self._date_field(self._date_from_str(date_part))
        self._row("Date", self._f_date, required=True)

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
                self._f_time.setTime(QTime.currentTime())
        else:
            self._f_time.setTime(QTime.currentTime())
        self._row("Time In", self._f_time, required=True)

        self._f_purpose = self._combo(_PURPOSE_OPTIONS, d.get("reason", ""))
        self._row("Purpose", self._f_purpose, required=True)

        # priority + live pill
        pri_w = QWidget()
        pri_l = QHBoxLayout(pri_w)
        pri_l.setContentsMargins(0, 0, 0, 0)
        pri_l.setSpacing(10)
        self._f_priority = self._combo(list(QueuePriority.ALL), d.get("priority", QueuePriority.NORMAL))
        self._priority_pill = QLabel()
        self._priority_pill.setFixedSize(100, 26)
        self._priority_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pri_l.addWidget(self._f_priority, 1)
        pri_l.addWidget(self._priority_pill)
        self._f_priority.currentTextChanged.connect(self._update_priority_pill)
        self._update_priority_pill(self._f_priority.currentText())
        self._row("Priority", pri_w)

        self._f_status = self._combo(list(QueueStatus.ALL), d.get("status", QueueStatus.WAITING))
        self._f_priority.currentTextChanged.connect(self._on_priority_changed)
        self._row("Status", self._f_status)

        self._f_notes = self._textarea(2, "Optional notes…")
        self._f_notes.setPlainText(d.get("notes", ""))
        self._row("Notes", self._f_notes)

    def _update_priority_pill(self, text):
        color = _PRIORITY_COLORS.get(text, "#1a3a8a")
        self._priority_pill.setText(text)
        self._priority_pill.setStyleSheet(
            f"background:{color}20; color:{color}; border:1px solid {color}60;"
            " border-radius:13px; font-size:11px; font-weight:700;"
        )

    def _on_priority_changed(self, text):
        if text == QueuePriority.EMERGENCY:
            self._f_status.setCurrentText(QueueStatus.IN_PROGRESS)

    def _on_save(self):
        if not self._patient_id_from_combo(self._f_patient):
            QMessageBox.warning(self, "Required", "Patient ID is required.")
            return
        qid = self._data.get("queue_id", "") or new_id("Q")
        self._saved_id = qid
        self._show_toast(f"Patient added to queue as {qid}")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(400, self.accept)

    def get_data(self):
        date_str = self._f_date.date().toString("yyyy-MM-dd")
        time_str = self._f_time.time().toString("HH:mm")
        return {
            "queue_id":     self._data.get("queue_id", "") or getattr(self, "_saved_id", new_id("Q")),
            "patient_id":   self._patient_id_from_combo(self._f_patient),
            "checkin_time": f"{date_str} {time_str}",
            "status":       self._f_status.currentText(),
            "priority":     self._f_priority.currentText(),
            "reason":       self._f_purpose.currentText(),
            "notes":        self._f_notes.toPlainText().strip(),
        }


# =============================================================================

class QueuePage(TablePage):
    DEFAULT_HEADERS = ["queue_id", "patient_id", "checkin_time", "status", "priority"]
    _PRIORITY_ORDER = {QueuePriority.EMERGENCY: 0, QueuePriority.URGENT: 1, QueuePriority.NORMAL: 2}

    def __init__(self, role="viewer", username=""):
        super().__init__("Queue", QUEUE_CSV, role, username)

    def load_data(self):
        super().load_data()
        self._color_by_priority()

    def _color_by_priority(self):
        priority_col = self._headers.index("priority") if "priority" in self._headers else -1
        if priority_col < 0:
            return
        colors = {QueuePriority.EMERGENCY: "#ef4444", QueuePriority.URGENT: "#f59e0b", QueuePriority.NORMAL: None}
        for row_idx in range(self._table.rowCount()):
            pri_item = self._table.item(row_idx, priority_col)
            if not pri_item:
                continue
            color = colors.get(pri_item.text())
            if color:
                for c in range(self._table.columnCount()):
                    item = self._table.item(row_idx, c)
                    if item:
                        item.setForeground(QColor(color))
                        font = item.font()
                        font.setBold(pri_item.text() == QueuePriority.EMERGENCY)
                        item.setFont(font)

    def on_add(self):
        dialog = QueueFormDialog(self, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        row = dialog.get_data()
        patient_id = row.get("patient_id", "").strip()
        priority   = row.get("priority", QueuePriority.NORMAL)
        added = add_to_queue(patient_id, priority)
        if not added:
            QMessageBox.warning(self, "Already in Queue",
                f"Patient '{patient_id}' already has an active queue entry.")
            return
        log_audit(self._username, "ADD", "Queue", patient_id, f"priority={priority}")
        self.load_data()

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Queue", "Please select a queue entry to edit.")
            return
        dialog = QueueFormDialog(self, row_data, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated_row = dialog.get_data()
        qid = row_data.get("queue_id")
        updated = update_row(QUEUE_CSV, lambda r: r.get("queue_id") == qid,
                             updated_row, headers=self.DEFAULT_HEADERS)
        if not updated:
            QMessageBox.warning(self, "Update Failed", "The selected entry could not be updated.")
            return
        log_audit(self._username, "EDIT", "Queue", qid, "")
        self.load_data()

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Queue", "Please select a queue entry to delete.")
            return
        answer = QMessageBox.question(self, "Delete Entry",
            f"Delete queue entry for patient {row_data.get('patient_id', '')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        qid = row_data.get("queue_id")
        deleted = delete_rows(QUEUE_CSV, lambda r: r.get("queue_id") == qid,
                              headers=self.DEFAULT_HEADERS)
        if not deleted:
            QMessageBox.warning(self, "Delete Failed", "The selected entry could not be deleted.")
            return
        log_audit(self._username, "DELETE", "Queue", qid, "")
        self.load_data()
