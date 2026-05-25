import datetime
from backend.config import QUEUE_CSV, DATETIME_FMT, QueueStatus, QueuePriority
from backend.utils import new_id
from backend.database import append_csv, read_csv, write_csv

# =============================================================================

QUEUE_HEADERS = ["queue_id", "patient_id", "checkin_time", "status", "priority"]


def add_to_queue(patient_id, priority=QueuePriority.NORMAL):
    # Guard: reject if the patient already has an active (waiting / in-progress) entry.
    active_statuses = {QueueStatus.WAITING, QueueStatus.IN_PROGRESS}
    existing = read_csv(QUEUE_CSV)
    for entry in existing:
        if (entry.get("patient_id") == patient_id and
                entry.get("status") in active_statuses):
            return False  # caller should surface a warning to the user

    row = {
        "queue_id":     new_id("Q"),
        "patient_id":   patient_id,
        "checkin_time": datetime.datetime.now().strftime(DATETIME_FMT),
        "status":       QueueStatus.WAITING,
        "priority":     priority,
    }
    append_csv(QUEUE_CSV, row, headers=QUEUE_HEADERS)
    return True


# =============================================================================
