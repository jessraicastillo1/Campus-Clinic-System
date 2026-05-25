# ui/pages/__init__.py  —  Royal Dark theme package
# All page classes are imported here so dashboard_window.py only needs:
#   from ui.pages import *

from ui.pages.home_page        import HomePage
from ui.pages.patient_page     import PatientPage
from ui.pages.history_page     import HistoryPage
from ui.pages.vitals_page      import VitalsPage
from ui.pages.vaccines_page    import VaccinesPage
from ui.pages.prescriptions_page import PrescriptionsPage

# These four live in clinical_pages.py (appointments, queue, emergency, inventory)
from ui.pages.clinical_pages import (
    AppointmentsPage,
    QueuePage,
    EmergencyPage,
    InventoryPage,
)

# These four live in admin_pages.py (referrals, clearances, absences, incidents)
from ui.pages.admin_pages import (
    ReferralsPage,
    ClearancesPage,
    AbsencesPage,
    IncidentsPage,
)

# Optional pages — imported only if their source files exist
try:
    from ui.pages.dispense_page import DispensePage
except ImportError:
    DispensePage = None  # type: ignore

try:
    from ui.pages.audit_page import AuditPage
except ImportError:
    AuditPage = None  # type: ignore

try:
    from ui.pages.users_page import UsersPage
except ImportError:
    UsersPage = None  # type: ignore

__all__ = [
    "HomePage",
    "PatientPage",
    "HistoryPage",
    "VitalsPage",
    "VaccinesPage",
    "PrescriptionsPage",
    "AppointmentsPage",
    "QueuePage",
    "EmergencyPage",
    "InventoryPage",
    "ReferralsPage",
    "ClearancesPage",
    "AbsencesPage",
    "IncidentsPage",
    "DispensePage",
    "AuditPage",
    "UsersPage",
]
