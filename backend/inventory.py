from backend.config import INVENTORY_CSV
from backend.utils import is_low_stock, is_expiring_soon
from backend.database import read_csv, write_csv

# =============================================================================

INVENTORY_HEADERS = ["item_id", "name", "quantity", "unit", "expiry_date", "reorder_level", "batch_lot"]


def apply_inventory_deduction(item_id, qty_str):
    try:
        qty = float(qty_str)
    except (ValueError, TypeError):
        qty = 0
    rows = read_csv(INVENTORY_CSV)
    changed = False
    for row in rows:
        if row["item_id"] == item_id:
            try:
                current_qty = float(row.get("quantity", "0"))
            except (ValueError, TypeError):
                current_qty = 0
            row["quantity"] = str(max(0.0, current_qty - qty))
            changed = True
    if changed:
        write_csv(INVENTORY_CSV, rows, headers=INVENTORY_HEADERS)


def sanitize_inventory_quantities():
    rows = read_csv(INVENTORY_CSV)
    for row in rows:
        try:
            qty = float(row.get("quantity", "0"))
        except (ValueError, TypeError):
            qty = 0
        row["quantity"] = str(max(0.0, qty))
    write_csv(INVENTORY_CSV, rows, headers=INVENTORY_HEADERS)


def get_inventory_alerts():
    alerts = []
    for row in read_csv(INVENTORY_CSV):
        name     = row.get("name", "")
        quantity = float(row.get("quantity", "0") or 0)
        reorder  = float(row.get("reorder_level", "0") or 0)
        expiry   = row.get("expiry_date", "")
        if is_low_stock(quantity, reorder):
            alerts.append(f"Low stock: {name} (qty {quantity} <= reorder {reorder})")
        expiring, days_left = is_expiring_soon(expiry)
        if expiring:
            alerts.append(f"Expiry soon: {name} (in {days_left} days on {expiry})")
    return alerts

# =============================================================================
