import os, sys
from datetime import datetime as _dt

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
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

_VACCINE_LIST = [
    "", "COVID-19", "Flu (Influenza)", "Tetanus (TD/Tdap)",
    "Hepatitis A", "Hepatitis B", "MMR", "Varicella (Chickenpox)",
    "HPV", "Meningococcal", "Pneumococcal",
    "Typhoid", "Rabies", "Other",
]
_DOSE_LIST   = ["1st Dose", "2nd Dose", "3rd Dose", "Booster", "Annual"]
_STATUS_LIST = ["Complete", "Pending", "Missed"]

_STATUS_COLOURS = {
    "Complete": ("#e6f4ec", "#1a7a4a"),
    "Pending":  ("#fdf6e3", "#c9a227"),
    "Missed":   ("#fdecea", "#c0392b"),
}


class VaccineFormDialog(QDialog):

    def __init__(self, parent=None, data: dict | None = None, username: str = ""):
        super().__init__(parent)
        self._data     = data or {}
        self._is_edit  = bool(data)
        self._username = username
        self._fields   = {}
        self.setWindowTitle("Edit Vaccination" if self._is_edit else "Add Vaccination")
        self._init_ui()

    def _init_ui(self):
        body_lay, foot_lay, _ = build_modal_shell(
            self,
            title="Edit Vaccination" if self._is_edit else "Add Vaccination",
            icon="✎ " if self._is_edit else "💉  ",
        )

        # ── SECTION: VACCINE ──────────────────────────────────────────────────
        body_lay.addWidget(section_div("VACCINE INFORMATION"))

        two = QGridLayout()
        two.setHorizontalSpacing(14)
        two.setVerticalSpacing(4)

        two.addWidget(field_lbl("Vaccination ID"), 0, 0)
        vid = inp(readonly=True, value=self._data.get("record_id", ""))
        two.addWidget(vid, 1, 0)
        self._fields["record_id"] = vid

        two.addWidget(field_lbl("Patient ID", required=True), 0, 1)
        pid = inp("e.g. PT-0001", value=self._data.get("patient_id", ""))
        two.addWidget(pid, 1, 1)
        self._fields["patient_id"] = pid
        body_lay.addLayout(two)
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Vaccine Name", required=True))
        vn = combo(_VACCINE_LIST, current=self._data.get("vaccine_name", ""))
        body_lay.addWidget(vn)
        self._fields["vaccine_name"] = vn

        body_lay.addSpacing(4)

        three = QGridLayout()
        three.setHorizontalSpacing(14)
        three.setVerticalSpacing(4)

        three.addWidget(field_lbl("Dose Number"), 0, 0)
        dose = combo(_DOSE_LIST, current=self._data.get("dose", "1st Dose"))
        three.addWidget(dose, 1, 0)
        self._fields["dose"] = dose

        three.addWidget(field_lbl("Date Administered", required=True), 0, 1)
        da = date_edit(self._data.get("date_given", ""))
        three.addWidget(da, 1, 1)
        self._fields["date_given"] = da

        body_lay.addLayout(three)
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Next Due Date"))
        nd = date_edit(self._data.get("next_due", ""))
        body_lay.addWidget(nd)
        self._fields["next_due"] = nd

        # ── SECTION: STATUS ───────────────────────────────────────────────────
        body_lay.addWidget(section_div("STATUS"))

        body_lay.addWidget(field_lbl("Status"))
        status_row = QHBoxLayout()
        self._status_cb = combo(_STATUS_LIST, current=self._data.get("status", "Pending"))
        self._status_cb.setFixedWidth(180)
        self._status_pill = QLabel("Pending")
        self._status_pill.setStyleSheet(
            "background: #fdf6e3; color: #c9a227; border-radius: 10px;"
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
        body_lay.addWidget(field_lbl("Administered By"))
        ab = inp(readonly=True, value=self._data.get("administered_by", self._username))
        body_lay.addWidget(ab)
        self._fields["administered_by"] = ab

        body_lay.addSpacing(4)
        body_lay.addWidget(field_lbl("Notes"))
        notes = inp("Additional notes", value=self._data.get("notes", ""))
        body_lay.addWidget(notes)
        self._fields["notes"] = notes

        body_lay.addStretch()
        save_btn = add_footer_buttons(foot_lay, self, "💾  Save Vaccination")
        save_btn.clicked.connect(self._on_accept)

    def _update_pill(self, text: str):
        bg, fg = _STATUS_COLOURS.get(text, ("#f0f1f5", "#5a6480"))
        self._status_pill.setText(text)
        self._status_pill.setStyleSheet(
            f"background: {bg}; color: {fg}; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )

    def _on_accept(self):
        data = self.get_data()
        required = {"patient_id": "Patient ID",
                    "vaccine_name": "Vaccine Name",
                    "date_given": "Date Administered"}
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

class VaccinesPage(TablePage):
    DEFAULT_HEADERS = [
        "record_id", "patient_id", "vaccine_name", "dose",
        "date_given", "next_due", "status", "administered_by", "notes",
    ]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Vaccinations", VACCINES_CSV, role, username)

    def load_data(self):
        super().load_data()
        self._colour_by_status()

    def _colour_by_status(self):
        if "status" not in self._headers:
            return
        col = self._headers.index("status")
        for row_idx in range(self._table.rowCount()):
            item = self._table.item(row_idx, col)
            if not item:
                continue
            status = item.text()
            if status == "Missed":
                for c in range(self._table.columnCount()):
                    i = self._table.item(row_idx, c)
                    if i:
                        i.setForeground(QColor("#c0392b"))
            elif status == "Pending":
                for c in range(self._table.columnCount()):
                    i = self._table.item(row_idx, c)
                    if i:
                        i.setForeground(QColor("#c9a227"))

    def on_add(self):
        dlg = VaccineFormDialog(self, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        row = dlg.get_data()
        if not row.get("record_id"):
            row["record_id"] = new_id("VC")
        append_csv(VACCINES_CSV, row, headers=self.DEFAULT_HEADERS)
        log_audit(self._username, "ADD", "Vaccines", row["record_id"],
                  f"patient={row.get('patient_id','')}")
        self.load_data()
        self.show_toast("Vaccination record saved", "success")

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a record to edit.")
            return
        dlg = VaccineFormDialog(self, row_data, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dlg.get_data()
        rid = row_data.get("record_id")
        ok  = update_row(VACCINES_CSV, lambda r: r.get("record_id") == rid,
                         updated, headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Update Failed",
                                "The selected record could not be updated.")
            return
        log_audit(self._username, "EDIT", "Vaccines", rid, "")
        self.load_data()
        self.show_toast(f"Vaccination {rid} updated", "info")

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a record to delete.")
            return
        rid = row_data.get("record_id", "")
        vn  = row_data.get("vaccine_name", rid)
        if not confirm_delete_dialog(self, f"{vn} ({rid})"):
            return
        ok = delete_rows(VACCINES_CSV, lambda r: r.get("record_id") == rid,
                         headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Delete Failed",
                                "The selected record could not be deleted.")
            return
        log_audit(self._username, "DELETE", "Vaccines", rid, vn)
        self.load_data()
        self.show_toast(f"Vaccination {rid} deleted", "error")
