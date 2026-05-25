"""
models.py  –  Domain model classes for the Campus Clinic Record System.

Each class wraps a plain dict (the row from CSV) and exposes typed
attributes plus helper methods.  This gives us a real Model layer so
that business logic is not scattered across the UI.
"""

from __future__ import annotations
import datetime
from backend.config import DATE_FMT, DATETIME_FMT

# ─────────────────────────── base ────────────────────────────────────────────

class BaseModel:
    """Mixin: dict-backed model with to_dict / from_dict helpers."""

    FIELDS: list[str] = []

    def __init__(self, data: dict | None = None):
        self._data: dict = data.copy() if data else {}

    def get(self, key: str, default=""):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value

    def to_dict(self) -> dict:
        return {f: self._data.get(f, "") for f in self.FIELDS}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data)

    def validate(self) -> list[str]:
        """Return a list of validation error strings (empty = valid)."""
        return []

    def is_valid(self) -> bool:
        return len(self.validate()) == 0


# ─────────────────────────── Patient ─────────────────────────────────────────

class Patient(BaseModel):
    FIELDS = [
        "patient_id", "role_type", "first_name", "last_name", "Date of Birth",
        "gender", "blood_type", "allergies", "chronic_conditions",
        "email", "phone", "address",
    ]

    REQUIRED = ["first_name", "last_name"]

    @property
    def patient_id(self) -> str:  return self._data.get("patient_id", "")
    @property
    def full_name(self) -> str:
        return f"{self._data.get('first_name','')} {self._data.get('last_name','')}".strip()
    @property
    def allergies(self) -> str:   return self._data.get("allergies", "")
    @property
    def has_allergies(self) -> bool:
        a = self.allergies.strip().lower()
        return bool(a) and a not in ("none", "n/a", "-", "")

    def validate(self) -> list[str]:
        errors = []
        for f in self.REQUIRED:
            if not self._data.get(f, "").strip():
                errors.append(f"{f.replace('_',' ').title()} is required.")
        return errors


# ─────────────────────────── Vital ───────────────────────────────────────────

# Normal ranges for adult / school-age patients
VITAL_RANGES = {
    "bp_systolic":   (70,  180),
    "bp_diastolic":  (40,  120),
    "temperature_c": (35.0, 38.5),
    "bmi":           (10.0, 40.0),
}

class Vital(BaseModel):
    FIELDS = [
        "record_id", "patient_id", "date_time", "height_cm",
        "weight_kg", "bmi", "bp_systolic", "bp_diastolic", "temperature_c",
    ]

    def out_of_range_fields(self) -> list[str]:
        """Return list of field names whose values fall outside normal range."""
        flagged = []
        for field, (lo, hi) in VITAL_RANGES.items():
            raw = self._data.get(field, "")
            try:
                val = float(raw)
                if val < lo or val > hi:
                    flagged.append(field)
            except (ValueError, TypeError):
                pass
        return flagged

    def alert_message(self) -> str:
        bad = self.out_of_range_fields()
        if not bad:
            return ""
        labels = {
            "bp_systolic":   f"Systolic BP ({self._data.get('bp_systolic')})",
            "bp_diastolic":  f"Diastolic BP ({self._data.get('bp_diastolic')})",
            "temperature_c": f"Temperature ({self._data.get('temperature_c')} °C)",
            "bmi":           f"BMI ({self._data.get('bmi')})",
        }
        items = ", ".join(labels[f] for f in bad if f in labels)
        return f"⚠️ Abnormal vitals detected: {items}"

    def validate(self) -> list[str]:
        errors = []
        if not self._data.get("patient_id", "").strip():
            errors.append("Patient ID is required.")
        return errors


# ─────────────────────────── Inventory Item ──────────────────────────────────

class InventoryItem(BaseModel):
    FIELDS = ["item_id", "name", "quantity", "unit", "expiry_date", "reorder_level", "batch_lot"]

    @property
    def quantity(self) -> float:
        try: return float(self._data.get("quantity", 0))
        except (ValueError, TypeError): return 0.0

    @property
    def reorder_level(self) -> float:
        try: return float(self._data.get("reorder_level", 0))
        except (ValueError, TypeError): return 0.0

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.reorder_level

    @property
    def days_to_expiry(self) -> int | None:
        raw = self._data.get("expiry_date", "")
        if not raw:
            return None
        try:
            exp = datetime.datetime.strptime(raw, DATE_FMT).date()
            return (exp - datetime.date.today()).days
        except ValueError:
            return None

    @property
    def is_expiring_soon(self) -> bool:
        d = self.days_to_expiry
        return d is not None and d <= 30

    def validate(self) -> list[str]:
        errors = []
        if not self._data.get("name", "").strip():
            errors.append("Name is required.")
        try:
            qty = float(self._data.get("quantity", ""))
            if qty < 0:
                errors.append("Quantity cannot be negative.")
        except (ValueError, TypeError):
            errors.append("Quantity must be a number.")
        try:
            rl = float(self._data.get("reorder_level", ""))
            if rl < 0:
                errors.append("Reorder level cannot be negative.")
        except (ValueError, TypeError):
            errors.append("Reorder level must be a number.")
        return errors


# ─────────────────────────── Appointment ─────────────────────────────────────

class Appointment(BaseModel):
    FIELDS = ["appt_id", "patient_id", "date_time", "reason", "status", "created_by"]

    STATUS_OPTIONS   = ["pending", "confirmed", "waiting", "completed", "cancelled"]
    STATUS_CONFIRMED = "confirmed"
    STATUS_PENDING   = "pending"
    STATUS_CANCELLED = "cancelled"

    def validate(self) -> list[str]:
        errors = []
        if not self._data.get("patient_id", "").strip():
            errors.append("Patient ID is required.")
        if not self._data.get("date_time", "").strip():
            errors.append("Date/Time is required.")
        if not self._data.get("reason", "").strip():
            errors.append("Reason is required.")
        return errors


# ─────────────────────────── QueueEntry ──────────────────────────────────────

class QueueEntry(BaseModel):
    FIELDS = ["queue_id", "patient_id", "checkin_time", "status", "priority"]

    STATUS_WAITING    = "waiting"
    STATUS_INPROGRESS = "in-progress"
    STATUS_DONE       = "done"
    STATUS_CANCELLED  = "cancelled"
    STATUS_OPTIONS    = [STATUS_WAITING, STATUS_INPROGRESS, STATUS_DONE, STATUS_CANCELLED]

    PRIORITY_NORMAL   = "normal"
    PRIORITY_URGENT   = "urgent"
    PRIORITY_EMERGENCY= "emergency"
    PRIORITY_OPTIONS  = [PRIORITY_NORMAL, PRIORITY_URGENT, PRIORITY_EMERGENCY]

    def validate(self) -> list[str]:
        errors = []
        if not self._data.get("patient_id", "").strip():
            errors.append("Patient ID is required.")
        return errors


# ─────────────────────────── Prescription ────────────────────────────────────

class Prescription(BaseModel):
    FIELDS = [
        "rx_id", "patient_id", "date", "drug_name", "dosage",
        "frequency", "duration_days", "instructions", "prescribed_by",
    ]

    def validate(self) -> list[str]:
        errors = []
        if not self._data.get("patient_id", "").strip():
            errors.append("Patient ID is required.")
        if not self._data.get("drug_name", "").strip():
            errors.append("Drug name is required.")
        return errors


# ─────────────────────────── Dispense ────────────────────────────────────────

class DispenseRecord(BaseModel):
    FIELDS = [
        "dispense_id", "date", "patient_id", "item_id",
        "item_name", "quantity", "dose_info", "staff_user",
    ]

    def validate(self) -> list[str]:
        errors = []
        if not self._data.get("patient_id", "").strip():
            errors.append("Patient ID is required.")
        if not self._data.get("item_id", "").strip():
            errors.append("Item ID is required.")
        try:
            qty = float(self._data.get("quantity", ""))
            if qty <= 0:
                errors.append("Quantity must be greater than zero.")
        except (ValueError, TypeError):
            errors.append("Quantity must be a number.")
        return errors
