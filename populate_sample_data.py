import os
import sys
import csv
from datetime import datetime as _dt
from backend.config import DATA_DIR

# =============================================================================

SAMPLE_PATIENTS = [
    {"patient_id": "P001", "role_type": "Student",  "first_name": "John",    "last_name": "Doe",      "Date of Birth": "2004-05-15", "gender": "Male",   "blood_type": "O+",  "allergies": "Penicillin", "chronic_conditions": "",             "email": "john@campus.edu",     "phone": "555-0101", "address": "123 Main St"},
    {"patient_id": "P002", "role_type": "Student",  "first_name": "Jane",    "last_name": "Smith",    "Date of Birth": "2005-03-22", "gender": "Female", "blood_type": "A+",  "allergies": "",           "chronic_conditions": "Asthma",       "email": "jane@campus.edu",     "phone": "555-0102", "address": "456 Oak Ave"},
    {"patient_id": "P003", "role_type": "Staff",    "first_name": "Michael", "last_name": "Johnson",  "Date of Birth": "1988-07-10", "gender": "Male",   "blood_type": "B+",  "allergies": "Shellfish",  "chronic_conditions": "",             "email": "mjohnson@campus.edu", "phone": "555-0103", "address": "789 Pine Rd"},
    {"patient_id": "P004", "role_type": "Student",  "first_name": "Sarah",   "last_name": "Williams", "Date of Birth": "2003-11-08", "gender": "Female", "blood_type": "AB+", "allergies": "",           "chronic_conditions": "",             "email": "sarah@campus.edu",    "phone": "555-0104", "address": "321 Elm St"},
    {"patient_id": "P005", "role_type": "Faculty",  "first_name": "David",   "last_name": "Brown",    "Date of Birth": "1975-02-14", "gender": "Male",   "blood_type": "O-",  "allergies": "Latex",      "chronic_conditions": "Hypertension", "email": "dbrown@campus.edu",   "phone": "555-0105", "address": "654 Maple Dr"},
]

SAMPLE_INVENTORY = [
    {"item_id": "I001", "name": "Paracetamol 500mg",   "quantity": "8",  "unit": "boxes",   "expiry_date": "2027-12-31", "reorder_level": "20"},
    {"item_id": "I002", "name": "Amoxicillin 250mg",   "quantity": "5",  "unit": "boxes",   "expiry_date": "2027-06-30", "reorder_level": "15"},
    {"item_id": "I003", "name": "Ibuprofen 400mg",     "quantity": "25", "unit": "boxes",   "expiry_date": "2027-09-15", "reorder_level": "20"},
    {"item_id": "I004", "name": "Cetirizine 10mg",     "quantity": "12", "unit": "boxes",   "expiry_date": "2027-11-20", "reorder_level": "15"},
    {"item_id": "I005", "name": "Antibiotic Cream",    "quantity": "40", "unit": "tubes",   "expiry_date": "2027-03-31", "reorder_level": "30"},
    {"item_id": "I006", "name": "Bandages (assorted)", "quantity": "3",  "unit": "boxes",   "expiry_date": "2027-12-31", "reorder_level": "10"},
    {"item_id": "I007", "name": "Antiseptic Solution", "quantity": "18", "unit": "bottles", "expiry_date": "2027-08-15", "reorder_level": "15"},
    {"item_id": "I008", "name": "Thermometers",        "quantity": "7",  "unit": "units",   "expiry_date": "2030-12-31", "reorder_level": "10"},
]


def get_sample_appointments():
    today = _dt.now().strftime("%Y-%m-%d")
    return [
        {"appt_id": "A001", "patient_id": "P001", "date_time": f"{today} 09:00", "reason": "General Checkup",       "status": "confirmed", "created_by": "admin"},
        {"appt_id": "A002", "patient_id": "P002", "date_time": f"{today} 10:00", "reason": "Consultation",          "status": "confirmed", "created_by": "admin"},
        {"appt_id": "A003", "patient_id": "P003", "date_time": f"{today} 14:00", "reason": "Follow-up",             "status": "pending",   "created_by": "staff"},
        {"appt_id": "A004", "patient_id": "P004", "date_time": f"{today} 15:00", "reason": "Vaccination",           "status": "confirmed", "created_by": "admin"},
        {"appt_id": "A005", "patient_id": "P001", "date_time": f"{today} 16:00", "reason": "Lab Work",              "status": "confirmed", "created_by": "staff"},
        {"appt_id": "A006", "patient_id": "P005", "date_time": "2026-05-23 09:30","reason": "Blood Pressure Check",  "status": "scheduled", "created_by": "admin"},
    ]


def get_sample_vaccinations():
    today = _dt.now().strftime("%Y-%m-%d")
    return [
        {"record_id": "V001", "patient_id": "P001", "vaccine_name": "COVID-19", "dose": "1", "date_given": today,        "next_due": "2026-06-22"},
        {"record_id": "V002", "patient_id": "P002", "vaccine_name": "Flu",      "dose": "1", "date_given": "2026-05-20", "next_due": "2027-05-20"},
        {"record_id": "V003", "patient_id": "P003", "vaccine_name": "Tetanus",  "dose": "1", "date_given": "2026-01-15", "next_due": "2031-01-15"},
    ]


def get_sample_incidents():
    return [
        {"incident_id": "INC001", "date": "2026-05-20", "location": "Waiting Room", "patient_id": "P002", "description": "Patient fell",     "actions_taken": "First aid provided",         "reported_by": "admin"},
        {"incident_id": "INC002", "date": "2026-05-19", "location": "Exam Room 2",  "patient_id": "P004", "description": "Allergic reaction", "actions_taken": "Epinephrine administered",    "reported_by": "staff"},
        {"incident_id": "INC003", "date": "2026-05-18", "location": "Corridor",     "patient_id": "P005", "description": "Dizziness",         "actions_taken": "Patient sat down, monitored", "reported_by": "admin"},
    ]


def _write_csv_simple(filename, rows, headers):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\u2713 {filename}: {len(rows)} records added")


def populate_sample_data():
    print("\n" + "=" * 70)
    print("POPULATING SAMPLE DATA FOR DASHBOARD")
    print("=" * 70 + "\n")

    _write_csv_simple("patients.csv", SAMPLE_PATIENTS,
                      ["patient_id","role_type","first_name","last_name","Date of Birth","gender","blood_type","allergies","chronic_conditions","email","phone","address"])

    appointments = get_sample_appointments()
    _write_csv_simple("appointments.csv", appointments,
                      ["appt_id","patient_id","date_time","reason","status","created_by"])

    _write_csv_simple("inventory.csv", SAMPLE_INVENTORY,
                      ["item_id","name","quantity","unit","expiry_date","reorder_level"])

    vaccinations = get_sample_vaccinations()
    _write_csv_simple("vaccinations.csv", vaccinations,
                      ["record_id","patient_id","vaccine_name","dose","date_given","next_due"])

    incidents = get_sample_incidents()
    _write_csv_simple("incidents.csv", incidents,
                      ["incident_id","date","location","patient_id","description","actions_taken","reported_by"])

    print("\n" + "=" * 70)
    print("SAMPLE DATA SUMMARY")
    print("=" * 70)
    print(f"\u2713 Total Patients:        {len(SAMPLE_PATIENTS)}")
    today_str = _dt.now().strftime("%Y-%m-%d")
    print(f"\u2713 Today's Appointments:  {len([a for a in appointments if a['date_time'].startswith(today_str)])}")
    print(f"\u2713 Low Stock Items:       {len([i for i in SAMPLE_INVENTORY if int(i['quantity']) <= int(i['reorder_level'])])}")
    print(f"\u2713 Vaccination Records:   {len(vaccinations)}")
    print(f"\u2713 Incident Records:      {len(incidents)}")
    print("\n\u2728 Dashboard is now ready with sample data!\n")
    print("Start the application with: python combined_all.py")
    print("=" * 70 + "\n")


# =============================================================================
# ENTRY POINT
#   python populate_sample_data.py -> seed CSV data files
# =============================================================================

if __name__ == "__main__":
    populate_sample_data()
