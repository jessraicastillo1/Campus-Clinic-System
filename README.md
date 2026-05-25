# Campus Clinic Record System — v9

A PyQt6 desktop application for managing a school clinic. Runs fully offline — no internet or database server required. All data is stored in plain CSV files on disk.

## Quick Start

### Requirements

```
Python 3.10+
PyQt6 >= 6.4.0
```

### Install

```bash
pip install PyQt6
```

### Run

```bash
python main.py
```

On first launch, you will be prompted to create an admin account and a recovery key. Store the recovery key somewhere safe — it is the only way to reset a forgotten password.

---

## Default Login (after first-run setup)

Use the credentials you created on first launch. There is no hardcoded default account.

---

## Features

### Patient Management
- Register students and staff as patients (with role type)
- Track personal info, blood type, allergies, and chronic conditions
- Live search bar on every module — type to filter instantly
- Allergy warning banner shown in red when dispensing medicine to a patient with recorded allergies

### Clinical Modules
| Module | What it does |
|---|---|
| Medical History | Log visit complaints, diagnosis, treatment, and notes |
| Vitals | Record height, weight, BP, temperature; auto-calculates BMI; highlights out-of-range values in red |
| Vaccinations | Track vaccine name, dose, date given, and next due date |
| Prescriptions | Issue and view prescriptions with drug, dosage, frequency, and duration |
| Dispensing | Dispense inventory items to patients; checks for allergies; deducts stock automatically |
| Queue | Patient check-in queue with Normal / Urgent / Emergency priority and color-coded rows |
| Appointments | Schedule and track appointments with status (pending → confirmed → completed) |

### Administrative Modules
| Module | What it does |
|---|---|
| Inventory | Track medicines and supplies with quantity, expiry date, reorder level, and batch/lot number |
| Referrals | Record external referrals with reason and destination |
| Clearances | Issue medical clearances (pending / approved / rejected) |
| Excused Absences | Issue absence certificates with date ranges |
| Incidents | Log clinic incidents with location, description, and actions taken |
| Emergency Contacts | Store emergency contact info per patient |

### System Features
- **Audit trail** — every Add / Edit / Delete / Dispense is logged to `audit_log.csv` with the user, timestamp, module, and record ID
- **Data backup** — sidebar "💾 Backup Data" button copies all CSV files to a timestamped folder under `data/backups/`
- **Print** — every module has a 🖨 Print button that opens a formatted HTML report in the browser
- **Role-based access** — three roles: `admin`, `staff`, `viewer`
- **Recovery key** — admin password can be reset using the recovery key generated on first run

---

## Architecture

```
clinic_systemv9/
├── main.py                        # Entry point; applies global stylesheet; shows login
├── requirements.txt
├── backend/
│   ├── config.py                  # File paths, date formats, role list, status enums
│   ├── models.py                  # Domain model classes (Patient, Vital, InventoryItem, etc.)
│   ├── database.py                # CSV read/write, audit logging, backup
│   ├── auth.py                    # Password hashing (SHA-256), login, recovery key
│   ├── dashboard_stats.py         # All dashboard metric calculations (extracted from UI)
│   ├── inventory.py               # Inventory-specific helpers (stock deduction)
│   ├── queue_logic.py             # Queue add/update logic with duplicate guard
│   └── utils.py                   # new_id(), calc_bmi(), is_low_stock(), is_expiring_soon()
├── ui/
│   ├── login_window.py            # Login screen with register and forgot-password flow
│   ├── dashboard_window.py        # Main window with sidebar navigation
│   └── pages/
│       ├── base_page.py           # Base class all pages inherit from
│       ├── table_page.py          # Reusable table with search, print, row count
│       ├── home_page.py           # Dashboard stats cards
│       ├── patient_page.py        # Patient list and registration form
│       ├── vitals_page.py         # Vitals recording with range alerts and auto-BMI
│       ├── clinical_pages.py      # Appointments, Queue, Emergency contacts, Inventory
│       ├── admin_pages.py         # Referrals, Clearances, Absences, Incidents
│       ├── dispense_page.py       # Medicine dispensing with allergy check
│       ├── history_page.py        # Medical history per patient
│       ├── prescriptions_page.py  # Prescription management
│       ├── vaccines_page.py       # Vaccination records
│       ├── inventory_page.py      # Inventory list with low-stock and expiry alerts
│       ├── audit_page.py          # Read-only audit trail viewer
│       ├── users_page.py          # User account management (admin only)
│       ├── shared_modal.py        # Reusable modal dialog components
│       └── _dialog_base.py        # Base class for all dialogs
└── data/
    ├── patients.csv
    ├── vitals.csv
    ├── medical_history.csv
    ├── prescriptions.csv
    ├── dispensing_log.csv
    ├── inventory.csv
    ├── queue.csv
    ├── appointments.csv
    ├── vaccinations.csv
    ├── referrals.csv
    ├── clearances.csv
    ├── excused_absences.csv
    ├── incidents.csv
    ├── emergency_contacts.csv
    ├── audit_log.csv
    ├── users.csv
    └── backups/                   # Timestamped backup folders created by the app
```

---

## Data Flow

1. `main.py` starts → creates all CSV files if missing → shows login window
2. User logs in → `auth.py` hashes the password with SHA-256 and checks `users.csv`
3. Dashboard loads → `dashboard_stats.py` reads CSVs and computes all metrics
4. User opens a module → the matching page loads and reads its CSV
5. User fills a form → `models.py` validates the data (required fields, numeric ranges)
6. On save → `database.py` writes to the module's CSV and appends a row to `audit_log.csv`
7. The table refreshes by re-reading the CSV

---

## Roles

| Role | Permissions |
|---|---|
| `admin` | Full access including user management, audit log, and system settings |
| `staff` | Full clinical and administrative access; cannot manage users |
| `viewer` | Read-only access to patient records and reports |

New self-registered accounts start as `viewer` and must be promoted by an admin.

---

## Vital Normal Ranges

The system flags out-of-range vitals in red and prompts for confirmation before saving.

| Measurement | Normal Range |
|---|---|
| Systolic BP | 70 – 180 mmHg |
| Diastolic BP | 40 – 120 mmHg |
| Temperature | 35.0 – 38.5 °C |
| BMI | 10.0 – 40.0 |

---

## Building a Standalone Executable

A PyInstaller spec file is included:

```bash
pip install pyinstaller
pyinstaller ClinicSystem.spec
```

The output will be in the `dist/` folder.

---

## Notes

- All data is stored locally. There is no server, no database engine, and no network connection required.
- Backup folders are named by timestamp (e.g. `data/backups/20260526_002612/`) and contain a full copy of all CSV files at the time the backup was triggered.
- The recovery key is generated once on first run. Only its SHA-256 hash is stored on disk — the plaintext key is shown once and never saved.
