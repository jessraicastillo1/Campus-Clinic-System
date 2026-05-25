import os, csv, datetime, hashlib
from backend.config import *
from backend.auth import add_user

# =============================================================================

def init_csv(path, headers):
    """Create the CSV with headers if it does not exist OR if it is empty/headerless."""
    needs_header = False
    if not os.path.exists(path):
        needs_header = True
    else:
        # File exists — check it actually has a valid header row
        try:
            with open(path, encoding="utf-8") as f:
                first = next(csv.reader(f), None)
            if not first:          # file is blank
                needs_header = True
            elif first != headers: # header is wrong or missing columns
                needs_header = True
        except (IOError, StopIteration):
            needs_header = True
    if needs_header:
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(headers)


def read_csv(path):
    try:
        with open(path, encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except (FileNotFoundError, IOError):
        return []


def write_csv(path, rows, headers=None):
    if headers is None and rows:
        headers = list(rows[0].keys())
    elif headers is None and not rows:
        # No headers supplied and no rows to infer from — read the existing
        # header row from disk so we never wipe the column names.
        try:
            with open(path, encoding="utf-8") as f:
                headers = next(csv.reader(f), None)
        except (FileNotFoundError, StopIteration):
            headers = None
    if not headers:
        # Truly nothing to work with — leave the file untouched.
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def append_csv(path, row, headers=None):
    file_exists = os.path.exists(path) and os.path.getsize(path) > 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        if not file_exists and headers:
            csv.DictWriter(f, fieldnames=headers).writeheader()
        writer = csv.DictWriter(f, fieldnames=(headers if headers else row.keys()))
        if not file_exists and not headers:
            writer.writeheader()
        writer.writerow(row)


def delete_rows(path, match_fn, headers=None):
    rows = read_csv(path)
    filtered = [row for row in rows if not match_fn(row)]
    write_csv(path, filtered, headers=headers or (list(rows[0].keys()) if rows else None))
    return len(rows) - len(filtered)


def update_row(path, match_fn, updated_row, headers=None):
    rows = read_csv(path)
    updated = 0
    results = []
    for row in rows:
        if not updated and match_fn(row):
            results.append(updated_row)
            updated = 1
        else:
            results.append(row)
    write_csv(path, results, headers=headers or list(updated_row.keys()))
    return updated


# ── Audit log ─────────────────────────────────────────────────────────────────

AUDIT_HEADERS = ["timestamp", "user", "action", "module", "record_id", "details"]

def log_audit(user: str, action: str, module: str, record_id: str = "", details: str = ""):
    """Append an immutable audit trail entry."""
    row = {
        "timestamp": datetime.datetime.now().strftime(DATETIME_FMT),
        "user":      user or "system",
        "action":    action,
        "module":    module,
        "record_id": record_id,
        "details":   details,
    }
    append_csv(AUDIT_CSV, row, headers=AUDIT_HEADERS)


# ── Backup ────────────────────────────────────────────────────────────────────

def create_backup() -> str:
    """Copy all CSV data files into a timestamped backup folder. Returns path."""
    import shutil
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(DATA_DIR, "backups", stamp)
    os.makedirs(backup_dir, exist_ok=True)
    count = 0
    for fname in os.listdir(DATA_DIR):
        if fname.endswith(".csv"):
            shutil.copy2(os.path.join(DATA_DIR, fname), backup_dir)
            count += 1
    return backup_dir


# ── Init ──────────────────────────────────────────────────────────────────────

def ensure_data_dir_and_files():
    os.makedirs(DATA_DIR, exist_ok=True)

    init_csv(USERS_CSV,         ["username", "password_hash", "role"])
    init_csv(PATIENTS_CSV,      ["patient_id", "role_type", "first_name", "last_name", "Date of Birth", "gender",
                                  "blood_type", "allergies", "chronic_conditions", "email", "phone", "address"])
    init_csv(HISTORY_CSV,       ["record_id", "patient_id", "visit_date", "complaint", "diagnosis", "treatment", "notes", "staff_user"])
    init_csv(EMERGENCY_CSV,     ["patient_id", "contact_name", "relationship", "phone", "alt_phone"])
    init_csv(VACCINES_CSV,      ["record_id", "patient_id", "vaccine_name", "dose", "date_given", "next_due"])
    init_csv(VITALS_CSV,        ["record_id", "patient_id", "date_time", "height_cm", "weight_kg", "bmi", "bp_systolic", "bp_diastolic", "temperature_c"])
    init_csv(PRESCRIPTIONS_CSV, ["rx_id", "patient_id", "date", "drug_name", "dosage", "frequency", "duration_days", "instructions", "prescribed_by"])
    init_csv(REFERRALS_CSV,     ["ref_id", "patient_id", "date", "referred_to", "reason", "notes", "staff_user"])
    init_csv(INVENTORY_CSV,     ["item_id", "name", "quantity", "unit", "expiry_date", "reorder_level", "batch_lot"])
    init_csv(DISPENSE_CSV,      ["dispense_id", "date", "patient_id", "item_id", "item_name", "quantity", "dose_info", "staff_user"])
    init_csv(APPOINTMENTS_CSV,  ["appt_id", "patient_id", "date_time", "reason", "status", "created_by"])
    init_csv(QUEUE_CSV,         ["queue_id", "patient_id", "checkin_time", "status", "priority"])
    init_csv(CLEARANCE_CSV,     ["clearance_id", "patient_id", "type", "date", "status", "notes", "staff_user"])
    init_csv(ABSENCES_CSV,      ["cert_id", "patient_id", "issue_date", "from_date", "to_date", "reason", "staff_user"])
    init_csv(INCIDENTS_CSV,     ["incident_id", "date", "location", "patient_id", "description", "actions_taken", "reported_by"])
    init_csv(AUDIT_CSV,         AUDIT_HEADERS)

    with open(USERS_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        # If no users exist, do NOT auto-create admin here.
        # main.py will call needs_first_run_setup() and show the setup dialog.


def needs_first_run_setup() -> bool:
    """Return True if the users file is empty (no accounts created yet)."""
    rows = read_csv(USERS_CSV)
    return len(rows) == 0

# =============================================================================
