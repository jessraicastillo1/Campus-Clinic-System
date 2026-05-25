# Campus Clinic Record System — v4

A PyQt6 desktop application for managing a school clinic.

## What's New in v4 (Assessment Fixes)

### Nurse / Clinical Safety
| Fix | Detail |
|-----|--------|
| ✅ Patient search | Every module now has a live search bar — type to filter instantly |
| ✅ Allergy warning | Dispense form shows a red banner when the patient has recorded allergies |
| ✅ Vitals normal-range alerts | Out-of-range BP / temperature / BMI rows are highlighted red; saving prompts a confirmation |
| ✅ Auto BMI calculation | Height + weight auto-calculate BMI in the vitals form |
| ✅ Queue priority | Each queue entry has Normal / Urgent / Emergency priority; rows are color-coded |
| ✅ Print function | Every module has a 🖨 Print button that opens a formatted HTML report in the browser |
| ✅ Audit trail | Every Add / Edit / Delete / Dispense action is logged with user, timestamp, and record ID |
| ✅ Batch / lot numbers | Inventory now tracks batch/lot numbers for medication recall support |
| ✅ Data backup | Sidebar "💾 Backup Data" button copies all CSV files to a timestamped folder |

### OOP / Code Quality
| Fix | Detail |
|-----|--------|
| ✅ Model layer | `backend/models.py` — `Patient`, `Vital`, `InventoryItem`, `QueueEntry`, `DispenseRecord`, `Prescription` classes with typed properties and `validate()` methods |
| ✅ God-class split | `backend/dashboard_stats.py` — All stat-counting logic extracted from `HomePage` into `DashboardStats` |
| ✅ Form validation | Every form calls `model.validate()` and shows errors before saving |
| ✅ Status constants | `AppointmentStatus`, `QueueStatus`, `QueuePriority`, `ClearanceStatus` enums in `config.py` — no more bare strings |
| ✅ Exception handling | Removed silent `except: pass` patterns; errors are surfaced with proper messages |

## Requirements
```
PyQt6
```
Install: `pip install PyQt6`

## Running
```bash
python main.py
```
Default login: `admin` / `admin123`

## File Structure
```
clinic_systemv4/
├── main.py
├── backend/
│   ├── config.py          # Constants, status enums, paths
│   ├── models.py          # NEW: domain model classes
│   ├── dashboard_stats.py # NEW: extracted dashboard statistics
│   ├── database.py        # CSV I/O + audit log + backup
│   ├── auth.py
│   ├── inventory.py       # Updated: batch_lot support
│   ├── queue_logic.py     # Updated: priority support
│   └── utils.py
└── ui/
    └── pages/
        ├── table_page.py  # Updated: search bar, print, row count
        ├── patient_page.py  # Updated: validation, allergy helper
        ├── vitals_page.py   # Updated: range alerts, auto-BMI
        ├── dispense_page.py # Updated: allergy check, inventory link
        ├── queue_page.py    # Updated: priority field + colors
        ├── inventory_page.py # Updated: batch_lot, color alerts
        └── audit_page.py    # NEW: read-only audit trail viewer
```
