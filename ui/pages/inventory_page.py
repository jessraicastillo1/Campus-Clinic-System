"""inventory_page.py — Inventory CRUD with redesigned Royal Dark form."""

from __future__ import annotations

from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QColor
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QMessageBox, QWidget

from backend.config    import INVENTORY_CSV
from backend.utils     import new_id
from backend.database  import append_csv, update_row, delete_rows, log_audit
from backend.inventory import is_expiring_soon
from backend.models    import InventoryItem
from ui.pages.table_page   import TablePage
from ui.pages._dialog_base import _BaseFormDialog

# =============================================================================

class InventoryFormDialog(_BaseFormDialog):

    CATEGORY_OPTIONS = ["Medicine", "Supplies", "Equipment"]
    UNIT_OPTIONS     = ["Tablet", "Capsule", "Bottle", "Box", "Piece", "Pack", "Vial", "Sachet"]

    def __init__(self, parent=None, data=None, session_user=""):
        super().__init__(parent, data, session_user)
        self._build_ui("Edit Inventory Item" if data else "Add Inventory Item", bar_color="#1a3a8a")

    def _populate_form(self):
        d = self._data

        self._section("Auto")
        self._f_item_id = self._ro_field(d.get("item_id", "") or "Auto-generated")
        self._row("Item ID", self._f_item_id)
        self._spacer()

        self._section("Item")
        self._f_name = self._text_field("e.g. Biogesic 500mg", d.get("name", ""))
        self._row("Item Name", self._f_name, required=True)

        self._f_category = self._combo(self.CATEGORY_OPTIONS, d.get("category", ""))
        self._row("Category", self._f_category, required=True)

        self._f_unit = self._combo(self.UNIT_OPTIONS, d.get("unit", ""))
        self._row("Unit", self._f_unit, required=True)

        try:
            qty_val = int(float(d.get("quantity", 0) or 0))
        except Exception:
            qty_val = 0
        self._f_qty = self._spinbox(0, 99999, qty_val)
        self._row("Quantity", self._f_qty, required=True)

        try:
            reorder_val = int(float(d.get("reorder_level", 10) or 10))
        except Exception:
            reorder_val = 10
        self._f_reorder = self._spinbox(0, 99999, reorder_val)
        self._row("Reorder Level", self._f_reorder)

        self._f_expiry = self._date_field(self._date_from_str(d.get("expiry_date", "")))
        self._row("Expiry Date", self._f_expiry)

        self._f_supplier = self._text_field("e.g. PhilHealth Supplies", d.get("supplier", ""))
        self._row("Supplier", self._f_supplier)

        self._f_batch = self._text_field("e.g. BL-2025-001", d.get("batch_lot", ""))
        self._row("Batch / Lot", self._f_batch)
        self._spacer()

        self._section("Status")
        # live status pill
        status_w = QWidget()
        status_l = QHBoxLayout(status_w)
        status_l.setContentsMargins(0, 0, 0, 0)
        status_l.setSpacing(10)
        self._status_pill = QLabel("—")
        self._status_pill.setFixedHeight(28)
        self._status_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_pill.setStyleSheet(
            "border-radius:14px; padding:0 16px; font-size:12px; font-weight:700;"
        )
        status_l.addWidget(self._status_pill)
        status_l.addStretch()
        self._body_layout.addWidget(status_w)

        self._f_qty.valueChanged.connect(self._update_status_pill)
        self._f_reorder.valueChanged.connect(self._update_status_pill)
        self._update_status_pill()

    def _update_status_pill(self, _=None):
        qty     = self._f_qty.value()
        reorder = self._f_reorder.value()
        if qty == 0:
            text, color = "Out of Stock", "#c0392b"
        elif qty <= reorder:
            text, color = "Low Stock", "#c9a227"
        else:
            text, color = "Healthy", "#1a7a4a"
        self._status_pill.setText(text)
        self._status_pill.setStyleSheet(
            f"background:{color}20; color:{color}; border:1px solid {color}60;"
            " border-radius:14px; padding:0 16px; font-size:12px; font-weight:700;"
        )

    def _on_save(self):
        if not self._f_name.text().strip():
            QMessageBox.warning(self, "Required", "Item Name is required.")
            return
        data = self.get_data()
        item = InventoryItem(data)
        errors = item.validate()
        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return
        iid  = self._data.get("item_id", "") or new_id("INV")
        name = self._f_name.text().strip()
        self._saved_id = iid
        self._show_toast(f"{iid} {name} added to inventory")
        QTimer.singleShot(400, self.accept)

    def get_data(self):
        return {
            "item_id":      self._data.get("item_id", "") or getattr(self, "_saved_id", new_id("INV")),
            "name":         self._f_name.text().strip(),
            "category":     self._f_category.currentText(),
            "quantity":     str(self._f_qty.value()),
            "unit":         self._f_unit.currentText(),
            "expiry_date":  self._f_expiry.date().toString("yyyy-MM-dd"),
            "reorder_level":str(self._f_reorder.value()),
            "supplier":     self._f_supplier.text().strip(),
            "batch_lot":    self._f_batch.text().strip(),
        }


# =============================================================================

class InventoryPage(TablePage):
    DEFAULT_HEADERS = [
        "item_id", "name", "category", "quantity", "unit",
        "expiry_date", "reorder_level", "supplier", "batch_lot",
    ]

    def __init__(self, role="viewer", username=""):
        super().__init__("Inventory", INVENTORY_CSV, role, username)

    def load_data(self):
        super().load_data()
        self._highlight_alerts()

    def _highlight_alerts(self):
        if not self._headers:
            return
        qty_col    = self._headers.index("quantity")     if "quantity"     in self._headers else -1
        reord_col  = self._headers.index("reorder_level")if "reorder_level"in self._headers else -1
        expiry_col = self._headers.index("expiry_date")  if "expiry_date"  in self._headers else -1

        for row_idx in range(self._table.rowCount()):
            def cell(c):
                i = self._table.item(row_idx, c)
                return i.text() if i else ""

            is_low = False
            if qty_col >= 0 and reord_col >= 0:
                try:
                    is_low = float(cell(qty_col)) <= float(cell(reord_col))
                except Exception:
                    pass

            is_expiring = False
            if expiry_col >= 0:
                expiring, _ = is_expiring_soon(cell(expiry_col))
                is_expiring = expiring

            color = None
            if is_expiring:
                color = "#ef4444"
            elif is_low:
                color = "#f59e0b"

            if color:
                for c in range(self._table.columnCount()):
                    item = self._table.item(row_idx, c)
                    if item:
                        item.setForeground(QColor(color))
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)

    def on_add(self):
        dialog = InventoryFormDialog(self, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        row = dialog.get_data()
        if not row.get("item_id"):
            row["item_id"] = new_id("INV")
        append_csv(INVENTORY_CSV, row, headers=self.DEFAULT_HEADERS)
        log_audit(self._username, "ADD", "Inventory", row["item_id"], row.get("name", ""))
        self.load_data()

    def on_edit(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Item", "Please select an item to edit.")
            return
        dialog = InventoryFormDialog(self, row_data, session_user=self._username)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated_row = dialog.get_data()
        iid = row_data.get("item_id")
        updated = update_row(INVENTORY_CSV, lambda r: r.get("item_id") == iid,
                             updated_row, headers=self.DEFAULT_HEADERS)
        if not updated:
            QMessageBox.warning(self, "Update Failed", "The selected item could not be updated.")
            return
        log_audit(self._username, "EDIT", "Inventory", iid, "")
        self.load_data()

    def on_delete(self):
        row_data = self.selected_row_data()
        if not row_data:
            QMessageBox.warning(self, "Select Item", "Please select an item to delete.")
            return
        answer = QMessageBox.question(self, "Delete Item",
            f"Delete {row_data.get('name', '')} from inventory?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        iid = row_data.get("item_id")
        deleted = delete_rows(INVENTORY_CSV, lambda r: r.get("item_id") == iid,
                              headers=self.DEFAULT_HEADERS)
        if not deleted:
            QMessageBox.warning(self, "Delete Failed", "The selected item could not be deleted.")
            return
        log_audit(self._username, "DELETE", "Inventory", iid, row_data.get("name", ""))
        self.load_data()
