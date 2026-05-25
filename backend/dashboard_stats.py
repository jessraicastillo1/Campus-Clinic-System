"""
dashboard_stats.py  –  Statistics layer for the clinic dashboard.

All data-counting logic lives here so that HomePage remains a pure
presentation class with no business logic of its own.
"""

from __future__ import annotations
import csv
import datetime

from backend.config import (
    PATIENTS_CSV, APPOINTMENTS_CSV, INVENTORY_CSV,
    QUEUE_CSV, CLEARANCE_CSV, INCIDENTS_CSV,
    QueueStatus, ClearanceStatus,
)

# =============================================================================


class DashboardStats:
    """Compute every dashboard metric from the underlying CSV files."""

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def week_range(weeks_ago: int = 0) -> tuple[datetime.date, datetime.date]:
        """Return (start, end) for the ISO week that is `weeks_ago` weeks back."""
        today            = datetime.date.today()
        start_this_week  = today - datetime.timedelta(days=today.weekday())
        start = start_this_week - datetime.timedelta(weeks=weeks_ago)
        end   = start + datetime.timedelta(days=6)
        return start, end

    @staticmethod
    def fmt_change(current: int, previous: int, unit: str = "") -> str:
        """Human-readable week-over-week change string, e.g. '+12.5% vs last week'."""
        diff = current - previous
        if previous == 0:
            if diff == 0:
                return "No change vs last week"
            label = f"+{diff}{unit}" if diff > 0 else f"{diff}{unit}"
            return f"{label} vs last week"
        pct  = (diff / previous) * 100
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:.1f}% vs last week"

    @staticmethod
    def _read(path: str) -> list[dict]:
        """Read a CSV file and return its rows as dicts; return [] on any IO error."""
        try:
            with open(path, encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except (FileNotFoundError, IOError):
            return []

    # ── Patients ──────────────────────────────────────────────────────────────

    def count_patients(self) -> int:
        return len(self._read(PATIENTS_CSV))

    def patients_change(self) -> str:
        # No creation timestamp in current schema — leave the subtitle blank.
        return ""

    def get_patient_name(self, pid: str) -> str:
        """Resolve a patient_id to 'First Last', falling back to the raw ID."""
        for row in self._read(PATIENTS_CSV):
            if row.get("patient_id") == pid:
                return (
                    f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
                    or pid
                )
        return pid

    # ── Appointments ──────────────────────────────────────────────────────────

    def count_today_appointments(self) -> int:
        today = datetime.date.today().isoformat()
        return sum(
            1 for r in self._read(APPOINTMENTS_CSV)
            if r.get("date_time", "").startswith(today)
        )

    def get_today_appointments(self) -> list[dict]:
        today  = datetime.date.today().isoformat()
        result = []
        for r in self._read(APPOINTMENTS_CSV):
            if r.get("date_time", "").startswith(today):
                result.append({
                    "patient_name": self.get_patient_name(r.get("patient_id", "")),
                    "reason":       r.get("reason", ""),
                    "date_time":    r.get("date_time", ""),
                    "status":       r.get("status", ""),
                })
        return sorted(result, key=lambda x: x["date_time"])

    def count_appointments_in_range(self, start: datetime.date, end: datetime.date) -> int:
        count = 0
        for r in self._read(APPOINTMENTS_CSV):
            raw = r.get("date_time", "")[:10]
            try:
                if start <= datetime.date.fromisoformat(raw) <= end:
                    count += 1
            except ValueError:
                pass
        return count

    def appointments_change(self) -> str:
        this_s, this_e = self.week_range(0)
        last_s, last_e = self.week_range(1)
        return self.fmt_change(
            self.count_appointments_in_range(this_s, this_e),
            self.count_appointments_in_range(last_s, last_e),
        )

    # ── Inventory / Low stock ─────────────────────────────────────────────────

    def count_low_stock(self) -> int:
        count = 0
        for r in self._read(INVENTORY_CSV):
            try:
                if float(r.get("quantity", 0)) <= float(r.get("reorder_level", 0)):
                    count += 1
            except (ValueError, TypeError):
                pass
        return count

    def get_low_stock_items(self) -> list[dict]:
        result = []
        for r in self._read(INVENTORY_CSV):
            try:
                qty     = float(r.get("quantity", 0))
                reorder = float(r.get("reorder_level", 0))
                if qty <= reorder:
                    result.append({
                        "name":          r.get("name", ""),
                        "quantity":      int(qty),
                        "unit":          r.get("unit", ""),
                        "reorder_level": int(reorder),
                    })
            except (ValueError, TypeError):
                pass
        return sorted(result, key=lambda x: x["quantity"])

    def low_stock_change(self) -> str:
        # Stock levels fluctuate continuously; a week diff is not meaningful.
        return ""

    # ── Queue ─────────────────────────────────────────────────────────────────

    def count_active_queue(self) -> int:
        active = {QueueStatus.WAITING, QueueStatus.IN_PROGRESS}
        return sum(1 for r in self._read(QUEUE_CSV) if r.get("status") in active)

    def count_queue_in_range(self, start: datetime.date, end: datetime.date) -> int:
        count = 0
        for r in self._read(QUEUE_CSV):
            raw = r.get("checkin_time", "")[:10]
            try:
                if start <= datetime.date.fromisoformat(raw) <= end:
                    count += 1
            except ValueError:
                pass
        return count

    def active_queue_change(self) -> str:
        this_s, this_e = self.week_range(0)
        last_s, last_e = self.week_range(1)
        return self.fmt_change(
            self.count_queue_in_range(this_s, this_e),
            self.count_queue_in_range(last_s, last_e),
        )

    # ── Clearances ────────────────────────────────────────────────────────────

    def count_pending_clearances(self) -> int:
        return sum(
            1 for r in self._read(CLEARANCE_CSV)
            if r.get("status", "").lower() == ClearanceStatus.PENDING
        )

    def count_clearances_in_range(self, start: datetime.date, end: datetime.date) -> int:
        count = 0
        for r in self._read(CLEARANCE_CSV):
            raw = r.get("date", "")[:10]
            try:
                if start <= datetime.date.fromisoformat(raw) <= end:
                    count += 1
            except ValueError:
                pass
        return count

    def pending_clearances_change(self) -> str:
        this_s, this_e = self.week_range(0)
        last_s, last_e = self.week_range(1)
        return self.fmt_change(
            self.count_clearances_in_range(this_s, this_e),
            self.count_clearances_in_range(last_s, last_e),
        )

    # ── Incidents (Emergency Cases) ───────────────────────────────────────────

    def count_incidents(self) -> int:
        """Count incidents logged today only.

        The dashboard card is meant for daily monitoring, so showing the
        all-time total (which only ever grows) is misleading.  Filtering
        by today's ISO date gives staff an accurate picture at a glance.
        """
        today = datetime.date.today().isoformat()
        return sum(
            1 for r in self._read(INCIDENTS_CSV)
            if r.get("date", "").startswith(today)
        )

    def count_incidents_in_range(self, start: datetime.date, end: datetime.date) -> int:
        count = 0
        for r in self._read(INCIDENTS_CSV):
            raw = r.get("date", "")[:10]
            try:
                if start <= datetime.date.fromisoformat(raw) <= end:
                    count += 1
            except ValueError:
                pass
        return count

    def incidents_change(self) -> str:
        this_s, this_e = self.week_range(0)
        last_s, last_e = self.week_range(1)
        return self.fmt_change(
            self.count_incidents_in_range(this_s, this_e),
            self.count_incidents_in_range(last_s, last_e),
        )

    # ── All-in-one metric bundle ──────────────────────────────────────────────

    def get_metric_bundle(self) -> list[tuple[str, str, str]]:
        """Return (title, value, change) tuples consumed by the dashboard cards."""
        return [
            ("Total Patients",       str(self.count_patients()),           self.patients_change()),
            ("Today's Appointments", str(self.count_today_appointments()),  self.appointments_change()),
            ("Low Medicine Stock",   str(self.count_low_stock()),           self.low_stock_change()),
            ("Active Queue",         str(self.count_active_queue()),        self.active_queue_change()),
            ("Pending Clearances",   str(self.count_pending_clearances()),  self.pending_clearances_change()),
            ("Emergency Cases",      str(self.count_incidents()),           self.incidents_change()),
        ]


# =============================================================================
