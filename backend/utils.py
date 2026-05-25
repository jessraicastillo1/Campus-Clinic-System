"""
utils.py  –  Shared utility functions for the Campus Clinic Record System.
"""

from __future__ import annotations
import datetime
import secrets

from backend.config import DATE_FMT

# =============================================================================


def new_id(prefix: str) -> str:
    """Return a collision-safe unique ID: PREFIX + ms-timestamp + 4 random hex chars.

    Example: new_id('P') → 'P17165201234561a3f'

    The millisecond timestamp preserves rough chronological ordering.
    The 4-character hex suffix (65 536 possibilities) makes same-millisecond
    collisions astronomically unlikely even under rapid double-click entry.
    The prefix is always uppercased for consistency.
    """
    ts   = int(datetime.datetime.now().timestamp() * 1000)
    rand = secrets.token_hex(2)   # 4 lowercase hex characters
    return f"{prefix.upper()}{ts}{rand}"


def calc_bmi(height_cm, weight_kg) -> float | str:
    """Return BMI rounded to 1 decimal place, or '' on invalid input."""
    try:
        height_m = float(height_cm) / 100.0
        weight   = float(weight_kg)
        if height_m <= 0:
            return ""
        return round(weight / (height_m ** 2), 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return ""


def is_low_stock(quantity, reorder_level) -> bool:
    """Return True when quantity is at or below the reorder level."""
    return quantity <= reorder_level


def is_expiring_soon(expiry_str: str, days_threshold: int = 30) -> tuple[bool, int]:
    """Return (is_expiring, days_left).  Both are False/0 on parse failure."""
    try:
        expiry_date = datetime.datetime.strptime(expiry_str, DATE_FMT).date()
        days_left   = (expiry_date - datetime.date.today()).days
        return days_left <= days_threshold, days_left
    except (ValueError, AttributeError):
        return False, 0


# =============================================================================
