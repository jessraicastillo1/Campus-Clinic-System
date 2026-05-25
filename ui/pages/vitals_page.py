import os, sys, csv, datetime
from datetime import datetime as _dt

from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTimeEdit, QVBoxLayout, QWidget,
)

from backend.config import *
from backend.utils import *
from backend.database import *
from backend.auth import *
from backend.inventory import *
from backend.queue_logic import *
from backend.models import Vital
from ui.pages.base_page import BasePage
from ui.pages.table_page import TablePage
from ui.pages.shared_modal import (
    MODAL_STYLE, section_div, field_lbl, inp, combo, date_edit,
    build_modal_shell, add_footer_buttons, confirm_delete_dialog,
)

# =============================================================================


def _bmi_color(bmi_val: float) -> tuple:
    """Returns (bg, fg, label) based on BMI value."""
    if bmi_val < 18.5:
        return "#fdf6e3", "#c9a227", f"{bmi_val:.1f} — Underweight"
    if bmi_val < 25.0:
        return "#e6f4ec", "#1a7a4a", f"{bmi_val:.1f} — Normal"
    return "#fdecea", "#c0392b", f"{bmi_val:.1f} — Overweight"


class VitalFormDialog(QDialog):

    def __init__(self, parent=None, data: dict | None = None, username: str = ""):
        super().__init__(parent)
        self._data     = data or {}
        self._is_edit  = bool(data)
        self._username = username
        self._fields   = {}
        self.setWindowTitle("Edit Vitals" if self._is_edit else "Record Vitals")
        self._init_ui()

    def _init_ui(self):
        body_lay, foot_lay, _ = build_modal_shell(
            self,
            title="Edit Vitals" if self._is_edit else "Record Vitals",
            icon="✎ " if self._is_edit else "❤️  ",
        )

        # ── SECTION: MEASUREMENTS ─────────────────────────────────────────────
        body_lay.addWidget(section_div("MEASUREMENTS"))

        # Record ID + Patient ID  (2-col)
        two = QGridLayout()
        two.setHorizontalSpacing(14)
        two.setVerticalSpacing(4)

        two.addWidget(field_lbl("Record ID"), 0, 0)
        rid = inp(readonly=True, value=self._data.get("record_id", ""))
        two.addWidget(rid, 1, 0)
        self._fields["record_id"] = rid

        two.addWidget(field_lbl("Patient ID", required=True), 0, 1)
        pid = inp("e.g. PT-0001", value=self._data.get("patient_id", ""))
        two.addWidget(pid, 1, 1)
        self._fields["patient_id"] = pid
        body_lay.addLayout(two)
        body_lay.addSpacing(4)

        # Date & Time
        body_lay.addWidget(field_lbl("Date & Time", required=True))
        dt_row = QHBoxLayout()
        dt_row.setSpacing(8)
        raw = self._data.get("date_time", "")
        date_part = raw.split(" ")[0] if raw else ""
        time_part = raw.split(" ")[1] if " " in raw else _dt.now().strftime("%H:%M")
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
        self._fields["date_time"] = "special"

        body_lay.addSpacing(4)

        # Weight / Height  (2-col)
        wh = QGridLayout()
        wh.setHorizontalSpacing(14)
        wh.setVerticalSpacing(4)

        wh.addWidget(field_lbl("Weight (kg)"), 0, 0)
        self._weight = inp("e.g. 65", value=self._data.get("weight_kg", ""))
        wh.addWidget(self._weight, 1, 0)
        self._fields["weight_kg"] = self._weight

        wh.addWidget(field_lbl("Height (cm)"), 0, 1)
        self._height = inp("e.g. 165", value=self._data.get("height_cm", ""))
        wh.addWidget(self._height, 1, 1)
        self._fields["height_cm"] = self._height
        body_lay.addLayout(wh)
        body_lay.addSpacing(4)

        # BMI — live coloured pill
        body_lay.addWidget(field_lbl("BMI (auto-calculated)"))
        self._bmi_row = QHBoxLayout()
        self._bmi_pill = QLabel("—")
        self._bmi_pill.setStyleSheet(
            "background: #f0f1f5; color: #5a6480; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )
        self._bmi_row.addWidget(self._bmi_pill)
        self._bmi_row.addStretch()
        body_lay.addLayout(self._bmi_row)
        self._fields["bmi"] = "pill"

        self._weight.textChanged.connect(self._calc_bmi)
        self._height.textChanged.connect(self._calc_bmi)
        if self._data.get("weight_kg") and self._data.get("height_cm"):
            self._calc_bmi()

        body_lay.addSpacing(4)

        # BP + Heart Rate + Temp + O2  (2-col grid)
        ms = QGridLayout()
        ms.setHorizontalSpacing(14)
        ms.setVerticalSpacing(4)

        ms.addWidget(field_lbl("BP Systolic (mmHg)"), 0, 0)
        bp_sys = inp("e.g. 120", value=self._data.get("bp_systolic", ""))
        ms.addWidget(bp_sys, 1, 0)
        self._fields["bp_systolic"] = bp_sys

        ms.addWidget(field_lbl("BP Diastolic (mmHg)"), 0, 1)
        bp_dia = inp("e.g. 80", value=self._data.get("bp_diastolic", ""))
        ms.addWidget(bp_dia, 1, 1)
        self._fields["bp_diastolic"] = bp_dia

        ms.addWidget(field_lbl("Temperature (°C)"), 2, 0)
        temp = inp("e.g. 36.5", value=self._data.get("temperature_c", ""))
        ms.addWidget(temp, 3, 0)
        self._fields["temperature_c"] = temp

        ms.addWidget(field_lbl("Oxygen Saturation (%)"), 2, 1)
        o2 = inp("e.g. 98", value=self._data.get("oxygen_sat", ""))
        ms.addWidget(o2, 3, 1)
        self._fields["oxygen_sat"] = o2

        body_lay.addLayout(ms)

        # ── SECTION: NOTES ────────────────────────────────────────────────────
        body_lay.addWidget(section_div("NOTES"))

        body_lay.addWidget(field_lbl("Notes"))
        notes = inp("Any additional observations", value=self._data.get("notes", ""))
        body_lay.addWidget(notes)
        self._fields["notes"] = notes

        body_lay.addWidget(field_lbl("Staff User"))
        staff = inp(readonly=True, value=self._data.get("staff_user", self._username))
        body_lay.addWidget(staff)
        self._fields["staff_user"] = staff

        body_lay.addStretch()

        save_btn = add_footer_buttons(foot_lay, self, "💾  Save Vitals")
        save_btn.clicked.connect(self._on_accept)

    # ── Live BMI ──────────────────────────────────────────────────────────────

    def _calc_bmi(self):
        try:
            h = float(self._height.text())
            w = float(self._weight.text())
            if h > 0:
                bmi = round(w / ((h / 100) ** 2), 1)
                bg, fg, label = _bmi_color(bmi)
                self._bmi_pill.setText(label)
                self._bmi_pill.setStyleSheet(
                    f"background: {bg}; color: {fg}; border-radius: 10px;"
                    f"padding: 4px 14px; font-size: 11px; font-weight: 700;"
                )
                self._fields["_bmi_val"] = str(bmi)
        except (ValueError, ZeroDivisionError):
            self._bmi_pill.setText("—")
            self._fields.pop("_bmi_val", None)

    def _on_accept(self):
        data = self.get_data()
        required = {"patient_id": "Patient ID"}
        missing = [v for k, v in required.items() if not data.get(k, "").strip()]
        if missing:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Required Fields",
                                "Please fill in:\n• " + "\n• ".join(missing))
            return
        try:
            vital  = Vital(data)
            errors = vital.validate()
            if errors:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Validation Error", "\n".join(errors))
                return
            alert = vital.alert_message()
            if alert:
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self, "Abnormal Vitals",
                    f"{alert}\n\nSave anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
        except Exception:
            pass
        self.accept()

    def get_data(self) -> dict:
        result = {}
        for k, w in self._fields.items():
            if k == "date_time":
                d = self._date_w.date().toString("yyyy-MM-dd")
                t = self._time_w.time().toString("HH:mm")
                result[k] = f"{d} {t}"
            elif k == "bmi" or k == "_bmi_val":
                continue
            elif isinstance(w, QComboBox):
                result[k] = w.currentText().strip()
            elif isinstance(w, QDateEdit):
                result[k] = w.date().toString("yyyy-MM-dd")
            elif isinstance(w, str):
                continue
            else:
                result[k] = w.text().strip()
        # include calculated BMI
        result["bmi"] = self._fields.get("_bmi_val", "")
        return result


# =============================================================================

class VitalsPage(TablePage):
    DEFAULT_HEADERS = [
        "record_id", "patient_id", "date_time",
        "height_cm", "weight_kg", "bmi",
        "bp_systolic", "bp_diastolic", "temperature_c",
        "oxygen_sat", "notes", "staff_user",
    ]
    SENSITIVE_COLUMNS = [
        "height_cm", "weight_kg", "bmi",
        "bp_systolic", "bp_diastolic", "temperature_c", "oxygen_sat",
    ]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Vitals", VITALS_CSV, role, username)

    def load_data(self):
        super().load_data()
        self._highlight_abnormal()

    def _highlight_abnormal(self):
        if not self._all_rows:
            return
        for row_idx in range(self._table.rowCount()):
            row_data = {
                self._headers[c]: self._table.item(row_idx, c).text()
                for c in range(self._table.columnCount())
            }
            try:
                vital = Vital(row_data)
                if vital.out_of_range_fields():
                    for c in range(self._table.columnCount()):
                        item = self._table.item(row_idx, c)
                        if item:
                            item.setForeground(QColor("#c0392b"))
            except Exception:
                pass

    def on_add(self):
        dlg = VitalFormDialog(self, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        row = dlg.get_data()
        if not row.get("record_id"):
            row["record_id"] = new_id("VT")
        append_csv(VITALS_CSV, row, headers=self.DEFAULT_HEADERS)
        log_audit(self._username, "ADD", "Vitals", row["record_id"],
                  f"patient={row.get('patient_id','')}")
        self.load_data()
        pt = row.get("patient_id", "")
        self.show_toast(f"Vitals for {pt} recorded", "success")

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a record to edit.")
            return
        dlg = VitalFormDialog(self, row_data, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dlg.get_data()
        rid = row_data.get("record_id")
        ok  = update_row(VITALS_CSV, lambda r: r.get("record_id") == rid,
                         updated, headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Update Failed",
                                "The selected record could not be updated.")
            return
        log_audit(self._username, "EDIT", "Vitals", rid, "")
        self.load_data()
        self.show_toast(f"Vitals {rid} updated", "info")

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a record to delete.")
            return
        rid = row_data.get("record_id", "")
        if not confirm_delete_dialog(self, f"vitals record {rid}"):
            return
        ok = delete_rows(VITALS_CSV, lambda r: r.get("record_id") == rid,
                         headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Delete Failed",
                                "The selected record could not be deleted.")
            return
        log_audit(self._username, "DELETE", "Vitals", rid, "")
        self.load_data()
        self.show_toast(f"Vitals {rid} deleted", "error")
