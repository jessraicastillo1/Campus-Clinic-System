import os, sys, webbrowser, tempfile
import html as html_mod
from datetime import datetime as _dt, date as _date

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QGridLayout,
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
# REFERRALS
# =============================================================================

_REF_PRIORITY = ["Routine", "Urgent", "Emergency"]
_REF_STATUS   = ["Pending", "Sent", "Acknowledged", "Completed"]
_REF_PRI_CLR  = {
    "Routine":   ("#e8edf8", "#1a3a8a"),
    "Urgent":    ("#fdf6e3", "#c9a227"),
    "Emergency": ("#fdecea", "#c0392b"),
}


class ReferralFormDialog(QDialog):

    def __init__(self, parent=None, data: dict | None = None, username: str = ""):
        super().__init__(parent)
        self._data     = data or {}
        self._is_edit  = bool(data)
        self._username = username
        self._fields   = {}
        self.setWindowTitle("Edit Referral" if self._is_edit else "Add Referral")
        self._init_ui()

    def _init_ui(self):
        body_lay, foot_lay, _ = build_modal_shell(
            self,
            title="Edit Referral" if self._is_edit else "Add Referral",
            icon="✎ " if self._is_edit else "↗   ",
        )

        two = QGridLayout()
        two.setHorizontalSpacing(14)
        two.setVerticalSpacing(4)

        two.addWidget(field_lbl("Referral ID"), 0, 0)
        rid = inp(readonly=True, value=self._data.get("referral_id", ""))
        two.addWidget(rid, 1, 0)
        self._fields["referral_id"] = rid

        two.addWidget(field_lbl("Patient ID", required=True), 0, 1)
        pid = inp("e.g. PT-0001", value=self._data.get("patient_id", ""))
        two.addWidget(pid, 1, 1)
        self._fields["patient_id"] = pid
        body_lay.addLayout(two)
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Date", required=True))
        dt = date_edit(self._data.get("date", ""))
        body_lay.addWidget(dt)
        self._fields["date"] = dt
        body_lay.addSpacing(4)

        ref_row = QGridLayout()
        ref_row.setHorizontalSpacing(14)
        ref_row.setVerticalSpacing(4)

        ref_row.addWidget(field_lbl("Referred To", required=True), 0, 0)
        rto = inp("Hospital / Clinic name", value=self._data.get("referred_to", ""))
        ref_row.addWidget(rto, 1, 0)
        self._fields["referred_to"] = rto

        ref_row.addWidget(field_lbl("Department"), 0, 1)
        dept = inp("e.g. Cardiology", value=self._data.get("department", ""))
        ref_row.addWidget(dept, 1, 1)
        self._fields["department"] = dept
        body_lay.addLayout(ref_row)
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Reason", required=True))
        reason = inp("Reason for referral", value=self._data.get("reason", ""))
        body_lay.addWidget(reason)
        self._fields["reason"] = reason
        body_lay.addSpacing(4)

        # Priority pill
        body_lay.addWidget(field_lbl("Priority"))
        pri_row = QHBoxLayout()
        self._pri_cb = combo(_REF_PRIORITY, current=self._data.get("priority", "Routine"))
        self._pri_cb.setFixedWidth(160)
        self._pri_pill = QLabel("Routine")
        self._pri_pill.setStyleSheet(
            "background: #e8edf8; color: #1a3a8a; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )
        self._pri_cb.currentTextChanged.connect(self._upd_pri)
        pri_row.addWidget(self._pri_cb)
        pri_row.addWidget(self._pri_pill)
        pri_row.addStretch()
        body_lay.addLayout(pri_row)
        self._fields["priority"] = self._pri_cb
        self._upd_pri(self._pri_cb.currentText())
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Status"))
        status = combo(_REF_STATUS, current=self._data.get("status", "Pending"))
        body_lay.addWidget(status)
        self._fields["status"] = status
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Notes"))
        notes = inp("Additional notes", value=self._data.get("notes", ""))
        body_lay.addWidget(notes)
        self._fields["notes"] = notes
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Referred By"))
        by = inp(readonly=True, value=self._data.get("referred_by", self._username))
        body_lay.addWidget(by)
        self._fields["referred_by"] = by

        body_lay.addStretch()
        save_btn = add_footer_buttons(foot_lay, self, "💾  Save Referral")
        save_btn.clicked.connect(self._on_accept)

    def _upd_pri(self, text: str):
        bg, fg = _REF_PRI_CLR.get(text, ("#f0f1f5", "#5a6480"))
        self._pri_pill.setText(text)
        self._pri_pill.setStyleSheet(
            f"background: {bg}; color: {fg}; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )

    def _on_accept(self):
        data = self.get_data()
        required = {"patient_id": "Patient ID", "date": "Date",
                    "referred_to": "Referred To", "reason": "Reason"}
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
            elif isinstance(w, QDateEdit):
                result[k] = w.date().toString("yyyy-MM-dd")
            else:
                result[k] = w.text().strip()
        return result


class ReferralsPage(TablePage):
    DEFAULT_HEADERS = [
        "referral_id", "patient_id", "date", "referred_to",
        "department", "reason", "priority", "status", "notes", "referred_by",
    ]
    SENSITIVE_COLUMNS = ["reason", "notes"]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Referrals", REFERRALS_CSV, role, username)

    def on_add(self):
        dlg = ReferralFormDialog(self, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        row = dlg.get_data()
        if not row.get("referral_id"):
            row["referral_id"] = new_id("RF")
        append_csv(REFERRALS_CSV, row, headers=self.DEFAULT_HEADERS)
        log_audit(self._username, "ADD", "Referrals",
                  row["referral_id"], f"patient={row.get('patient_id','')}")
        self.load_data()
        self.show_toast(f"Referral {row['referral_id']} created", "success")

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a referral to edit.")
            return
        dlg = ReferralFormDialog(self, row_data, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dlg.get_data()
        rfid = row_data.get("referral_id")
        ok   = update_row(REFERRALS_CSV,
                          lambda r: r.get("referral_id") == rfid,
                          updated, headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Update Failed",
                                "The selected referral could not be updated.")
            return
        log_audit(self._username, "EDIT", "Referrals", rfid, "")
        self.load_data()
        self.show_toast(f"Referral {rfid} updated", "info")

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a referral to delete.")
            return
        rfid = row_data.get("referral_id", "")
        if not confirm_delete_dialog(self, f"referral {rfid}"):
            return
        ok = delete_rows(REFERRALS_CSV,
                         lambda r: r.get("referral_id") == rfid,
                         headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Delete Failed",
                                "The selected referral could not be deleted.")
            return
        log_audit(self._username, "DELETE", "Referrals", rfid, "")
        self.load_data()
        self.show_toast(f"Referral {rfid} deleted", "error")


# =============================================================================
# CLEARANCES
# =============================================================================

_CLR_PURPOSE = [
    "School Activity", "Sports", "Employment", "Medical", "Other",
]
_CLR_STATUS  = ["Valid", "Expired", "Revoked"]
_CLR_ST_CLR  = {
    "Valid":   ("#e6f4ec", "#1a7a4a"),
    "Expired": ("#fdf6e3", "#c9a227"),
    "Revoked": ("#fdecea", "#c0392b"),
}


def _print_clearance(data: dict):
    content = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #1a1a2e; }}
  h1   {{ color: #0d2260; border-bottom: 3px solid #f0c040; padding-bottom: 8px; }}
  .row {{ display: flex; gap: 12px; margin-bottom: 8px; font-size: 13px; }}
  .label {{ font-weight: 700; color: #5a6480; min-width: 160px; }}
  .badge {{ background: #e6f4ec; color: #1a7a4a; border-radius: 6px;
            padding: 2px 10px; font-weight: 700; font-size: 11px; display:inline-block; }}
  footer {{ margin-top: 40px; font-size: 11px; color: #5a6480; border-top: 1px solid #d0d8ef; padding-top:8px; }}
</style></head><body>
<h1>Campus Clinic — Medical Clearance</h1>
<div class="row"><span class="label">Clearance ID:</span><span>{html_mod.escape(data.get('clearance_id',''))}</span></div>
<div class="row"><span class="label">Patient ID:</span><span>{html_mod.escape(data.get('patient_id',''))}</span></div>
<div class="row"><span class="label">Purpose:</span><span>{html_mod.escape(data.get('purpose',''))}</span></div>
<div class="row"><span class="label">Date Issued:</span><span>{html_mod.escape(data.get('date_issued',''))}</span></div>
<div class="row"><span class="label">Valid Until:</span><span>{html_mod.escape(data.get('valid_until',''))}</span></div>
<div class="row"><span class="label">Status:</span><span class="badge">{html_mod.escape(data.get('status',''))}</span></div>
<div class="row"><span class="label">Remarks:</span><span>{html_mod.escape(data.get('remarks',''))}</span></div>
<div class="row"><span class="label">Issued By:</span><span>{html_mod.escape(data.get('issued_by',''))}</span></div>
<footer>Printed: {_dt.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; Padre Garcia Polytechnic College — Campus Clinic</footer>
</body></html>"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html",
                                     delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name
    webbrowser.open(f"file://{path}")


class ClearanceFormDialog(QDialog):

    def __init__(self, parent=None, data: dict | None = None, username: str = ""):
        super().__init__(parent)
        self._data     = data or {}
        self._is_edit  = bool(data)
        self._username = username
        self._fields   = {}
        self.setWindowTitle("Edit Clearance" if self._is_edit else "Issue Clearance")
        self._init_ui()

    def _init_ui(self):
        # Print button for footer
        self._print_btn = QPushButton("🖨  Print")
        self._print_btn.setObjectName("btn_print_footer")
        self._print_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._print_btn.clicked.connect(self._on_print)

        body_lay, foot_lay, _ = build_modal_shell(
            self,
            title="Edit Clearance" if self._is_edit else "Issue Clearance",
            icon="✎ " if self._is_edit else "✅  ",
        )

        two = QGridLayout()
        two.setHorizontalSpacing(14)
        two.setVerticalSpacing(4)

        two.addWidget(field_lbl("Clearance ID"), 0, 0)
        cid = inp(readonly=True, value=self._data.get("clearance_id", ""))
        two.addWidget(cid, 1, 0)
        self._fields["clearance_id"] = cid

        two.addWidget(field_lbl("Patient ID", required=True), 0, 1)
        pid = inp("e.g. PT-0001", value=self._data.get("patient_id", ""))
        two.addWidget(pid, 1, 1)
        self._fields["patient_id"] = pid
        body_lay.addLayout(two)
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Date Issued", required=True))
        di = date_edit(self._data.get("date_issued", ""))
        body_lay.addWidget(di)
        self._fields["date_issued"] = di
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Purpose", required=True))
        purpose = combo(_CLR_PURPOSE, current=self._data.get("purpose", ""))
        body_lay.addWidget(purpose)
        self._fields["purpose"] = purpose
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Valid Until"))
        self._valid_until = date_edit(self._data.get("valid_until", ""))
        body_lay.addWidget(self._valid_until)
        self._fields["valid_until"] = self._valid_until
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Remarks"))
        remarks = inp("Optional remarks", value=self._data.get("remarks", ""))
        body_lay.addWidget(remarks)
        self._fields["remarks"] = remarks
        body_lay.addSpacing(4)

        # Status pill (auto from valid_until date)
        body_lay.addWidget(field_lbl("Status"))
        status_row = QHBoxLayout()
        self._status_cb = combo(_CLR_STATUS, current=self._data.get("status", "Valid"))
        self._status_cb.setFixedWidth(160)
        self._status_pill = QLabel("Valid")
        self._status_pill.setStyleSheet(
            "background: #e6f4ec; color: #1a7a4a; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )
        self._status_cb.currentTextChanged.connect(self._upd_status)
        status_row.addWidget(self._status_cb)
        status_row.addWidget(self._status_pill)
        status_row.addStretch()
        body_lay.addLayout(status_row)
        self._fields["status"] = self._status_cb
        self._upd_status(self._status_cb.currentText())
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Issued By"))
        by = inp(readonly=True, value=self._data.get("issued_by", self._username))
        body_lay.addWidget(by)
        self._fields["issued_by"] = by

        body_lay.addStretch()
        save_btn = add_footer_buttons(
            foot_lay, self, "💾  Issue Clearance",
            extra_buttons=[self._print_btn],
        )
        save_btn.clicked.connect(self._on_accept)

    def _upd_status(self, text: str):
        bg, fg = _CLR_ST_CLR.get(text, ("#f0f1f5", "#5a6480"))
        self._status_pill.setText(text)
        self._status_pill.setStyleSheet(
            f"background: {bg}; color: {fg}; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )

    def _on_print(self):
        _print_clearance(self.get_data())

    def _on_accept(self):
        data = self.get_data()
        # Auto-set expired
        valid_until = data.get("valid_until", "")
        if valid_until:
            try:
                vu = _date.fromisoformat(valid_until)
                if vu < _date.today():
                    self._status_cb.setCurrentText("Expired")
                    data["status"] = "Expired"
            except Exception:
                pass
        required = {"patient_id": "Patient ID",
                    "date_issued": "Date Issued",
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
            elif isinstance(w, QDateEdit):
                result[k] = w.date().toString("yyyy-MM-dd")
            else:
                result[k] = w.text().strip()
        return result


class ClearancesPage(TablePage):
    DEFAULT_HEADERS = [
        "clearance_id", "patient_id", "date_issued", "purpose",
        "valid_until", "status", "remarks", "issued_by",
    ]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Clearances", CLEARANCE_CSV, role, username)

    def on_add(self):
        dlg = ClearanceFormDialog(self, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        row = dlg.get_data()
        if not row.get("clearance_id"):
            row["clearance_id"] = new_id("CL")
        append_csv(CLEARANCE_CSV, row, headers=self.DEFAULT_HEADERS)
        log_audit(self._username, "ADD", "Clearances",
                  row["clearance_id"], f"patient={row.get('patient_id','')}")
        self.load_data()
        self.show_toast(f"Clearance {row['clearance_id']} issued", "success")

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a clearance to edit.")
            return
        dlg = ClearanceFormDialog(self, row_data, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dlg.get_data()
        cid = row_data.get("clearance_id")
        ok  = update_row(CLEARANCE_CSV,
                         lambda r: r.get("clearance_id") == cid,
                         updated, headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Update Failed",
                                "The selected clearance could not be updated.")
            return
        log_audit(self._username, "EDIT", "Clearances", cid, "")
        self.load_data()
        self.show_toast(f"Clearance {cid} updated", "info")

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select a clearance to delete.")
            return
        cid = row_data.get("clearance_id", "")
        if not confirm_delete_dialog(self, f"clearance {cid}"):
            return
        ok = delete_rows(CLEARANCE_CSV,
                         lambda r: r.get("clearance_id") == cid,
                         headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Delete Failed",
                                "The selected clearance could not be deleted.")
            return
        log_audit(self._username, "DELETE", "Clearances", cid, "")
        self.load_data()
        self.show_toast(f"Clearance {cid} deleted", "error")


# =============================================================================
# ABSENCES
# =============================================================================

_ABS_REASON   = ["Sick", "Injury", "Medical Procedure", "Other"]
_ABS_MED_CERT = ["Submitted", "Not Required", "Pending"]


class AbsenceFormDialog(QDialog):

    def __init__(self, parent=None, data: dict | None = None, username: str = ""):
        super().__init__(parent)
        self._data     = data or {}
        self._is_edit  = bool(data)
        self._username = username
        self._fields   = {}
        self.setWindowTitle("Edit Absence" if self._is_edit else "Record Absence")
        self._init_ui()

    def _init_ui(self):
        body_lay, foot_lay, _ = build_modal_shell(
            self,
            title="Edit Absence" if self._is_edit else "Record Absence",
            icon="✎ " if self._is_edit else "🗓  ",
        )

        two = QGridLayout()
        two.setHorizontalSpacing(14)
        two.setVerticalSpacing(4)

        two.addWidget(field_lbl("Absence ID"), 0, 0)
        abid = inp(readonly=True, value=self._data.get("absence_id", ""))
        two.addWidget(abid, 1, 0)
        self._fields["absence_id"] = abid

        two.addWidget(field_lbl("Patient ID", required=True), 0, 1)
        pid = inp("e.g. PT-0001", value=self._data.get("patient_id", ""))
        two.addWidget(pid, 1, 1)
        self._fields["patient_id"] = pid
        body_lay.addLayout(two)
        body_lay.addSpacing(4)

        # Date From / Date To  (2-col, live total days)
        date_row = QGridLayout()
        date_row.setHorizontalSpacing(14)
        date_row.setVerticalSpacing(4)

        date_row.addWidget(field_lbl("Date From", required=True), 0, 0)
        self._date_from = date_edit(self._data.get("date_from", ""))
        date_row.addWidget(self._date_from, 1, 0)
        self._fields["date_from"] = self._date_from

        date_row.addWidget(field_lbl("Date To", required=True), 0, 1)
        self._date_to = date_edit(self._data.get("date_to", ""))
        date_row.addWidget(self._date_to, 1, 1)
        self._fields["date_to"] = self._date_to
        body_lay.addLayout(date_row)
        body_lay.addSpacing(4)

        # Total days (live, read-only)
        body_lay.addWidget(field_lbl("Total Days (auto)"))
        total_row = QHBoxLayout()
        self._total_pill = QLabel("—")
        self._total_pill.setStyleSheet(
            "background: #e8edf8; color: #1a3a8a; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )
        total_row.addWidget(self._total_pill)
        total_row.addStretch()
        body_lay.addLayout(total_row)
        self._fields["total_days"] = "computed"

        self._date_from.dateChanged.connect(self._calc_days)
        self._date_to.dateChanged.connect(self._calc_days)
        self._calc_days()
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Reason", required=True))
        reason = combo(_ABS_REASON, current=self._data.get("reason", "Sick"))
        body_lay.addWidget(reason)
        self._fields["reason"] = reason
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Medical Certificate"))
        mc = combo(_ABS_MED_CERT, current=self._data.get("medical_certificate", "Pending"))
        body_lay.addWidget(mc)
        self._fields["medical_certificate"] = mc
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Notes"))
        notes = inp("Additional notes", value=self._data.get("notes", ""))
        body_lay.addWidget(notes)
        self._fields["notes"] = notes
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Recorded By"))
        by = inp(readonly=True, value=self._data.get("recorded_by", self._username))
        body_lay.addWidget(by)
        self._fields["recorded_by"] = by

        body_lay.addStretch()
        save_btn = add_footer_buttons(foot_lay, self, "💾  Record Absence")
        save_btn.clicked.connect(self._on_accept)

    def _calc_days(self):
        df = self._date_from.date()
        dt = self._date_to.date()
        if dt < df:
            self._total_pill.setText("⚠ Date To is before Date From")
            self._total_pill.setStyleSheet(
                "background: #fdecea; color: #c0392b; border-radius: 10px;"
                "padding: 4px 14px; font-size: 11px; font-weight: 700;"
            )
            self._fields["_total_days_val"] = ""
            return
        days = df.daysTo(dt) + 1
        self._total_pill.setText(f"{days} day{'s' if days != 1 else ''}")
        self._total_pill.setStyleSheet(
            "background: #e8edf8; color: #1a3a8a; border-radius: 10px;"
            "padding: 4px 14px; font-size: 11px; font-weight: 700;"
        )
        self._fields["_total_days_val"] = str(days)

    def _on_accept(self):
        df = self._date_from.date()
        dt = self._date_to.date()
        if dt < df:
            QMessageBox.warning(self, "Invalid Dates",
                                "Date To cannot be before Date From.")
            return
        data = self.get_data()
        required = {"patient_id": "Patient ID",
                    "date_from":  "Date From",
                    "date_to":    "Date To",
                    "reason":     "Reason"}
        missing = [v for k, v in required.items() if not data.get(k, "").strip()]
        if missing:
            QMessageBox.warning(self, "Required Fields",
                                "Please fill in:\n• " + "\n• ".join(missing))
            return
        self.accept()

    def get_data(self) -> dict:
        result = {}
        for k, w in self._fields.items():
            if k == "total_days":
                result[k] = self._fields.get("_total_days_val", "")
            elif k == "_total_days_val":
                continue
            elif isinstance(w, QComboBox):
                result[k] = w.currentText().strip()
            elif isinstance(w, QDateEdit):
                result[k] = w.date().toString("yyyy-MM-dd")
            elif isinstance(w, str):
                continue
            else:
                result[k] = w.text().strip()
        return result


class AbsencesPage(TablePage):
    DEFAULT_HEADERS = [
        "absence_id", "patient_id", "date_from", "date_to", "total_days",
        "reason", "medical_certificate", "notes", "recorded_by",
    ]
    SENSITIVE_COLUMNS = ["reason", "notes"]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Absences", ABSENCES_CSV, role, username)

    def on_add(self):
        dlg = AbsenceFormDialog(self, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        row = dlg.get_data()
        if not row.get("absence_id"):
            row["absence_id"] = new_id("AB")
        append_csv(ABSENCES_CSV, row, headers=self.DEFAULT_HEADERS)
        log_audit(self._username, "ADD", "Absences",
                  row["absence_id"], f"patient={row.get('patient_id','')}")
        self.load_data()
        self.show_toast(f"Absence {row['absence_id']} recorded", "success")

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select an absence to edit.")
            return
        dlg = AbsenceFormDialog(self, row_data, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dlg.get_data()
        abid = row_data.get("absence_id")
        ok   = update_row(ABSENCES_CSV,
                          lambda r: r.get("absence_id") == abid,
                          updated, headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Update Failed",
                                "The selected absence could not be updated.")
            return
        log_audit(self._username, "EDIT", "Absences", abid, "")
        self.load_data()
        self.show_toast(f"Absence {abid} updated", "info")

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select an absence to delete.")
            return
        abid = row_data.get("absence_id", "")
        if not confirm_delete_dialog(self, f"absence {abid}"):
            return
        ok = delete_rows(ABSENCES_CSV,
                         lambda r: r.get("absence_id") == abid,
                         headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Delete Failed",
                                "The selected absence could not be deleted.")
            return
        log_audit(self._username, "DELETE", "Absences", abid, "")
        self.load_data()
        self.show_toast(f"Absence {abid} deleted", "error")


# =============================================================================
# INCIDENTS
# =============================================================================

_INC_TYPE   = ["Accident", "Illness", "Behavioral", "Facility", "Other"]
_INC_STATUS = ["Open", "Under Review", "Resolved", "Closed"]


class IncidentFormDialog(QDialog):

    def __init__(self, parent=None, data: dict | None = None, username: str = ""):
        super().__init__(parent)
        self._data     = data or {}
        self._is_edit  = bool(data)
        self._username = username
        self._fields   = {}
        self.setWindowTitle("Edit Incident" if self._is_edit else "Report Incident")
        self._init_ui()

    def _init_ui(self):
        body_lay, foot_lay, _ = build_modal_shell(
            self,
            title="Edit Incident" if self._is_edit else "Report Incident",
            icon="✎ " if self._is_edit else "⚠️  ",
            titlebar_id="modal_titlebar_gold",
        )

        two = QGridLayout()
        two.setHorizontalSpacing(14)
        two.setVerticalSpacing(4)

        two.addWidget(field_lbl("Incident ID"), 0, 0)
        incid = inp(readonly=True, value=self._data.get("incident_id", ""))
        two.addWidget(incid, 1, 0)
        self._fields["incident_id"] = incid

        two.addWidget(field_lbl("Patient / Person ID"), 0, 1)
        pid = inp("PT-0001, Staff, or Visitor",
                  value=self._data.get("patient_id", ""))
        two.addWidget(pid, 1, 1)
        self._fields["patient_id"] = pid
        body_lay.addLayout(two)
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Date & Time", required=True))
        dt = inp("e.g. 2025-05-25 14:30",
                 value=self._data.get("date_time",
                                     _dt.now().strftime("%Y-%m-%d %H:%M")))
        body_lay.addWidget(dt)
        self._fields["date_time"] = dt
        body_lay.addSpacing(4)

        loc_row = QGridLayout()
        loc_row.setHorizontalSpacing(14)
        loc_row.setVerticalSpacing(4)

        loc_row.addWidget(field_lbl("Location"), 0, 0)
        loc = inp("e.g. Gymnasium", value=self._data.get("location", ""))
        loc_row.addWidget(loc, 1, 0)
        self._fields["location"] = loc

        loc_row.addWidget(field_lbl("Type", required=True), 0, 1)
        inc_type = combo(_INC_TYPE, current=self._data.get("type", "Accident"))
        loc_row.addWidget(inc_type, 1, 1)
        self._fields["type"] = inc_type
        body_lay.addLayout(loc_row)
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Description", required=True))
        desc = inp("Describe the incident in detail",
                   value=self._data.get("description", ""))
        body_lay.addWidget(desc)
        self._fields["description"] = desc
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Immediate Action Taken"))
        action = inp("Actions taken immediately",
                     value=self._data.get("immediate_action", ""))
        body_lay.addWidget(action)
        self._fields["immediate_action"] = action
        body_lay.addSpacing(4)

        # Follow-up checkbox with conditional date
        fu_row = QHBoxLayout()
        self._fu_cb = QCheckBox("Follow-up Required")
        self._fu_cb.setChecked(self._data.get("followup_required", "") == "Yes")
        self._fu_cb.toggled.connect(self._toggle_followup)
        fu_row.addWidget(self._fu_cb)
        fu_row.addStretch()
        body_lay.addLayout(fu_row)
        self._fields["followup_required"] = "checkbox"

        self._fu_date_label = field_lbl("Follow-up Date")
        self._fu_date = date_edit(self._data.get("followup_date", ""))
        body_lay.addWidget(self._fu_date_label)
        body_lay.addWidget(self._fu_date)
        self._fields["followup_date"] = self._fu_date
        self._toggle_followup(self._fu_cb.isChecked())
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Status"))
        status = combo(_INC_STATUS, current=self._data.get("status", "Open"))
        body_lay.addWidget(status)
        self._fields["status"] = status
        body_lay.addSpacing(4)

        body_lay.addWidget(field_lbl("Reported By"))
        by = inp(readonly=True, value=self._data.get("reported_by", self._username))
        body_lay.addWidget(by)
        self._fields["reported_by"] = by

        body_lay.addStretch()
        save_btn = add_footer_buttons(foot_lay, self, "💾  Report Incident")
        save_btn.clicked.connect(self._on_accept)

    def _toggle_followup(self, checked: bool):
        self._fu_date_label.setVisible(checked)
        self._fu_date.setVisible(checked)

    def _on_accept(self):
        data = self.get_data()
        required = {"date_time": "Date & Time",
                    "type": "Incident Type",
                    "description": "Description"}
        missing = [v for k, v in required.items() if not data.get(k, "").strip()]
        if missing:
            QMessageBox.warning(self, "Required Fields",
                                "Please fill in:\n• " + "\n• ".join(missing))
            return
        self.accept()

    def get_data(self) -> dict:
        result = {}
        for k, w in self._fields.items():
            if k == "followup_required":
                result[k] = "Yes" if self._fu_cb.isChecked() else "No"
            elif isinstance(w, QComboBox):
                result[k] = w.currentText().strip()
            elif isinstance(w, QDateEdit):
                result[k] = w.date().toString("yyyy-MM-dd")
            elif isinstance(w, str):
                continue
            else:
                result[k] = w.text().strip()
        return result


class IncidentsPage(TablePage):
    DEFAULT_HEADERS = [
        "incident_id", "patient_id", "date_time", "location", "type",
        "description", "immediate_action", "followup_required",
        "followup_date", "status", "reported_by",
    ]
    SENSITIVE_COLUMNS = ["description", "immediate_action"]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Incidents", INCIDENTS_CSV, role, username)

    def on_add(self):
        dlg = IncidentFormDialog(self, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        row = dlg.get_data()
        if not row.get("incident_id"):
            row["incident_id"] = new_id("INC")
        append_csv(INCIDENTS_CSV, row, headers=self.DEFAULT_HEADERS)
        log_audit(self._username, "ADD", "Incidents",
                  row["incident_id"], f"type={row.get('type','')}")
        self.load_data()
        self.show_toast(f"Incident {row['incident_id']} reported", "success")

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select an incident to edit.")
            return
        dlg = IncidentFormDialog(self, row_data, username=self._username)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dlg.get_data()
        incid = row_data.get("incident_id")
        ok    = update_row(INCIDENTS_CSV,
                           lambda r: r.get("incident_id") == incid,
                           updated, headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Update Failed",
                                "The selected incident could not be updated.")
            return
        log_audit(self._username, "EDIT", "Incidents", incid, "")
        self.load_data()
        self.show_toast(f"Incident {incid} updated", "info")

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "No Selection", "Please select an incident to delete.")
            return
        incid = row_data.get("incident_id", "")
        if not confirm_delete_dialog(self, f"incident {incid}"):
            return
        ok = delete_rows(INCIDENTS_CSV,
                         lambda r: r.get("incident_id") == incid,
                         headers=self.DEFAULT_HEADERS)
        if not ok:
            QMessageBox.warning(self, "Delete Failed",
                                "The selected incident could not be deleted.")
            return
        log_audit(self._username, "DELETE", "Incidents", incid, "")
        self.load_data()
        self.show_toast(f"Incident {incid} deleted", "error")
