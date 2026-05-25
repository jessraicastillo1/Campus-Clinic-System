import os, sys

APP_TITLE = "Campus Clinic Record System"
_BASE     = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(_BASE, "data")

USERS_CSV         = os.path.join(DATA_DIR, "users.csv")
PATIENTS_CSV      = os.path.join(DATA_DIR, "patients.csv")
HISTORY_CSV       = os.path.join(DATA_DIR, "medical_history.csv")
EMERGENCY_CSV     = os.path.join(DATA_DIR, "emergency_contacts.csv")
VACCINES_CSV      = os.path.join(DATA_DIR, "vaccinations.csv")
VITALS_CSV        = os.path.join(DATA_DIR, "vitals.csv")
PRESCRIPTIONS_CSV = os.path.join(DATA_DIR, "prescriptions.csv")
REFERRALS_CSV     = os.path.join(DATA_DIR, "referrals.csv")
INVENTORY_CSV     = os.path.join(DATA_DIR, "inventory.csv")
DISPENSE_CSV      = os.path.join(DATA_DIR, "dispensing_log.csv")
APPOINTMENTS_CSV  = os.path.join(DATA_DIR, "appointments.csv")
QUEUE_CSV         = os.path.join(DATA_DIR, "queue.csv")
CLEARANCE_CSV     = os.path.join(DATA_DIR, "clearances.csv")
ABSENCES_CSV      = os.path.join(DATA_DIR, "excused_absences.csv")
INCIDENTS_CSV     = os.path.join(DATA_DIR, "incidents.csv")
AUDIT_CSV         = os.path.join(DATA_DIR, "audit_log.csv")

DATE_FMT     = "%Y-%m-%d"
DATETIME_FMT = "%Y-%m-%d %H:%M"

ROLES = ["admin", "staff", "viewer"]

# ── Status constants (use these instead of hard-coded strings) ────────────────
class AppointmentStatus:
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    WAITING   = "waiting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ALL = [PENDING, CONFIRMED, WAITING, COMPLETED, CANCELLED]

class QueueStatus:
    WAITING    = "waiting"
    IN_PROGRESS = "in-progress"
    DONE       = "done"
    CANCELLED  = "cancelled"
    ALL = [WAITING, IN_PROGRESS, DONE, CANCELLED]

class QueuePriority:
    NORMAL    = "normal"
    URGENT    = "urgent"
    EMERGENCY = "emergency"
    ALL = [NORMAL, URGENT, EMERGENCY]

class ClearanceStatus:
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ALL = ["", PENDING, APPROVED, REJECTED]

# ── Vital normal ranges ───────────────────────────────────────────────────────
VITAL_NORMAL_RANGES = {
    "bp_systolic":   (70,  180, "mmHg"),
    "bp_diastolic":  (40,  120, "mmHg"),
    "temperature_c": (35.0, 38.5, "°C"),
    "bmi":           (10.0, 40.0, ""),
}
