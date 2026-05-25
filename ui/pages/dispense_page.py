"""
dispense_page.py  –  Dispensing log UI for the Campus Clinic Record System.

Provides:
  • DispenseFormDialog  – add / edit dialog with inventory dropdown,
                          auto-filled item_id, and allergy warning banner.
  • DispensePage        – table view wired to DISPENSE_CSV with full
                          CRUD and automatic inventory adjustment.
"""

from __future__ import annotations

# stdlib
import datetime

# Qt
from PyQt6.QtCore    import Qt, QDate
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

# backend
from backend.config    import DISPENSE_CSV, INVENTORY_CSV
from backend.utils     import new_id
from backend.database  import append_csv, read_csv, update_row, delete_rows
from backend.database  import log_audit
from backend.inventory import apply_inventory_deduction
from backend.models    import DispenseRecord, Patient   # Patient must be here, not mid-file

# pages
from ui.pages.table_page   import TablePage
from ui.pages.patient_page import get_patient_allergies

# =============================================================================


class DispenseFormDialog(QDialog):
    """Modal form for creating or editing a dispensing record.

    When editing, the form is pre-populated with the existing row data.
    Changing the patient ID triggers a live allergy-alert banner.
    Selecting an item from the dropdown auto-fills the item_id field.
    """

    def __init__(self, parent=None, data: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Dispense" if data else "Add Dispense")
        self._data          = data or {}
        self._fields: dict  = {}
        self._inventory_map: dict = {}   # item_name → inventory row dict
        self._init_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    # ── Shared UI builder (same pattern as all other FormDialogs) ─────────
    @staticmethod
    def _make_title_bar(title: str) -> "QWidget":
        from PyQt6.QtWidgets import QHBoxLayout
        bar = QWidget()
        bar.setObjectName("modal_titlebar")
        bar.setFixedHeight(46)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(18, 0, 18, 0)
        lbl = QLabel(title)
        lbl.setObjectName("modal_title")
        lay.addWidget(lbl)
        return bar

    @staticmethod
    def _form_label(text: str) -> "QLabel":
        lbl = QLabel(text)
        lbl.setMinimumWidth(130)
        lbl.setStyleSheet("font-weight: 600; color: #5a6480; font-size: 12px;")
        return lbl

    def _init_ui(self) -> None:
        from PyQt6.QtWidgets import QHBoxLayout, QScrollArea

        # ── Allergy warning banner ─────────────────────────────────────────
        self._allergy_banner = QLabel("")
        self._allergy_banner.setObjectName("allergyBanner")
        self._allergy_banner.setStyleSheet(
            "background:#7f1d1d; color:#fca5a5; padding:6px 10px;"
            " border-radius:4px; font-weight:bold; margin:8px 20px 0 20px;"
        )
        self._allergy_banner.setWordWrap(True)
        self._allergy_banner.hide()

        # ── Inventory dropdown data ────────────────────────────────────────
        inv_rows            = read_csv(INVENTORY_CSV)
        self._inventory_map = {r["name"]: r for r in inv_rows if r.get("name")}
        inv_names           = [""] + sorted(self._inventory_map.keys())

        # ── Form ──────────────────────────────────────────────────────────
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        for header in DispensePage.DEFAULT_HEADERS:
            field = self._build_field(header, inv_names)
            form.addRow(self._form_label(header.replace("_", " ").title() + ":"), field)
            self._fields[header] = field

        # ── Outer shell ───────────────────────────────────────────────────
        title = "Edit Dispense" if self._data else "Add Dispense"
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._make_title_bar(title))
        outer.addWidget(self._allergy_banner)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(20, 16, 20, 8)
        body_lay.setSpacing(0)
        body_lay.addLayout(form)
        body_lay.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #d0d8ef;")
        outer.addWidget(divider)

        btn_row = QWidget()
        btn_row.setStyleSheet("background: #ffffff;")
        btn_lay = QHBoxLayout(btn_row)
        btn_lay.setContentsMargins(20, 12, 20, 14)
        btn_lay.setSpacing(10)
        btn_lay.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(36)
        cancel_btn.setMinimumWidth(90)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("btn_primary")
        save_btn.setFixedHeight(36)
        save_btn.setMinimumWidth(90)
        save_btn.clicked.connect(self._on_accept)

        btn_lay.addWidget(cancel_btn)
        btn_lay.addWidget(save_btn)
        outer.addWidget(btn_row)

        self.setMinimumWidth(500)
        self.resize(520, 460)

        # Pre-populate allergy banner when editing an existing record
        if self._data.get("patient_id"):
            self._check_allergy(self._data["patient_id"])

    def _build_field(self, header: str, inv_names: list[str]):
        """Create and return the appropriate widget for the given column header."""
        value = self._data.get(header, "")

        if header == "dispense_id":
            field = QLineEdit(value)
            if self._data:           # read-only when editing
                field.setReadOnly(True)

        elif header == "date":
            field = QDateEdit()
            field.setCalendarPopup(True)
            field.setDisplayFormat("MM/dd/yyyy")
            if value:
                try:
                    y, m, d = (int(x) for x in value.split("-"))
                    field.setDate(QDate(y, m, d))
                except (ValueError, AttributeError):
                    field.setDate(QDate.currentDate())
            else:
                field.setDate(QDate.currentDate())

        elif header == "patient_id":
            field = QLineEdit(value)
            field.setPlaceholderText("Enter Patient ID")
            field.textChanged.connect(self._check_allergy)

        elif header == "item_name":
            field = QComboBox()
            field.addItems(inv_names)
            if value in self._inventory_map:
                field.setCurrentText(value)
            elif value:
                field.addItem(value)
                field.setCurrentText(value)
            field.currentTextChanged.connect(self._on_item_selected)

        elif header == "item_id":
            field = QLineEdit(value)
            field.setReadOnly(True)
            field.setPlaceholderText("Auto-filled from item")

        else:
            field = QLineEdit(value)

        return field

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_item_selected(self, name: str) -> None:
        """Auto-fill item_id when a different item is chosen from the dropdown."""
        row = self._inventory_map.get(name)
        if row and "item_id" in self._fields:
            self._fields["item_id"].setText(row.get("item_id", ""))

    def _check_allergy(self, patient_id: str) -> None:
        """Show or hide the allergy alert banner based on the patient's record."""
        if not patient_id.strip():
            self._allergy_banner.hide()
            return

        allergies = get_patient_allergies(patient_id.strip())
        has_allergy = (
            allergies
            and allergies.strip().lower() not in ("none", "n/a", "-", "")
        )
        if has_allergy:
            self._allergy_banner.setText(
                f"⚠️  ALLERGY ALERT: Patient is allergic to — {allergies}"
            )
            self._allergy_banner.show()
        else:
            self._allergy_banner.hide()

    def _on_accept(self) -> None:
        """Validate the form; if an allergy is flagged, require explicit confirmation."""
        data   = self.get_data()
        errors = DispenseRecord(data).validate()
        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return

        if self._allergy_banner.isVisible():
            reply = QMessageBox.question(
                self, "Allergy Warning",
                "This patient has a recorded allergy.\n"
                "Are you sure you want to proceed with dispensing?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.accept()

    # ── Data extraction ───────────────────────────────────────────────────────

    def get_data(self) -> dict:
        """Return form contents as a plain dict keyed by column header."""
        result = {}
        for header in DispensePage.DEFAULT_HEADERS:
            widget = self._fields[header]
            if isinstance(widget, QDateEdit):
                result[header] = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QComboBox):
                result[header] = widget.currentText().strip()
            else:
                result[header] = widget.text().strip()
        return result


# =============================================================================


class DispensePage(TablePage):
    """Table view for the dispensing log with inventory-aware CRUD."""

    DEFAULT_HEADERS = [
        "dispense_id", "date", "patient_id",
        "item_id", "item_name", "quantity",
        "dose_info", "staff_user",
    ]

    def __init__(self, role: str = "viewer", username: str = ""):
        super().__init__("Dispensing Logs", DISPENSE_CSV, role, username)

    # ── CRUD handlers ─────────────────────────────────────────────────────────

    def on_add(self) -> None:
        dialog = DispenseFormDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        row = dialog.get_data()
        if not row.get("dispense_id"):
            row["dispense_id"] = new_id("D")

        if row.get("item_id") and row.get("quantity"):
            apply_inventory_deduction(row["item_id"], row["quantity"])

        append_csv(DISPENSE_CSV, row, headers=self.DEFAULT_HEADERS)
        log_audit(
            self._username, "DISPENSE", "Inventory", row.get("item_id", ""),
            f"patient={row.get('patient_id', '')} qty={row.get('quantity', '')}",
        )
        self.load_data()

    def on_edit(self) -> None:
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Record", "Please select a record to edit.")
            return

        dialog = DispenseFormDialog(self, row_data)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        updated_row = dialog.get_data()
        did         = row_data.get("dispense_id")
        old_item_id = row_data.get("item_id", "")
        new_item_id = updated_row.get("item_id", "")

        try:
            old_qty = float(row_data.get("quantity") or 0)
        except (ValueError, TypeError):
            old_qty = 0.0
        try:
            new_qty = float(updated_row.get("quantity") or 0)
        except (ValueError, TypeError):
            new_qty = 0.0

        # Adjust inventory to reflect the change:
        #   • same item  → deduct only the difference (may be negative = return)
        #   • item swapped → return full old qty, deduct full new qty
        if old_item_id and old_item_id == new_item_id:
            delta = new_qty - old_qty
            if delta != 0:
                apply_inventory_deduction(new_item_id, str(delta))
        else:
            if old_item_id and old_qty:
                apply_inventory_deduction(old_item_id, str(-old_qty))  # return stock
            if new_item_id and new_qty:
                apply_inventory_deduction(new_item_id, str(new_qty))   # deduct stock

        updated = update_row(
            DISPENSE_CSV,
            lambda row: row.get("dispense_id") == did,
            updated_row,
            headers=self.DEFAULT_HEADERS,
        )
        if not updated:
            QMessageBox.warning(self, "Update Failed", "The selected record could not be updated.")
            return

        log_audit(
            self._username, "EDIT", "Dispense", did,
            f"qty_delta={new_qty - old_qty:+g}",
        )
        self.load_data()

    def on_delete(self) -> None:
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Record", "Please select a record to delete.")
            return

        answer = QMessageBox.question(
            self, "Delete Record",
            f"Delete dispensing record for '{row_data.get('item_name', '')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        did     = row_data.get("dispense_id")
        deleted = delete_rows(
            DISPENSE_CSV,
            lambda row: row.get("dispense_id") == did,
            headers=self.DEFAULT_HEADERS,
        )
        if not deleted:
            QMessageBox.warning(self, "Delete Failed", "The selected record could not be deleted.")
            return

        log_audit(self._username, "DELETE", "Dispense", did, "")
        self.load_data()


# =============================================================================
