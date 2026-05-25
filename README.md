Campus Clinic Record System — v9

A modular PyQt6 desktop-based clinic management system designed for campus healthcare environments.
The system manages patient records, consultations, vitals, medicine inventory, dispensing workflows, queue management, audit tracking, and reporting within a centralized offline application.

Built using:

Python
PyQt6
CSV-based persistence layer
Modular OOP architecture
Overview

The application is designed to simulate a lightweight clinical information system for educational institutions.
It focuses on:

Patient record management
Clinical safety workflows
Medicine inventory monitoring
Queue prioritization
Audit accountability
Printable reporting
Modular maintainable architecture

The project evolved through multiple refactoring iterations to improve:

code organization,
data validation,
UI consistency,
maintainability,
and operational safety.
Major Features
Patient Management
Add, edit, delete, and search patient records
Store:
demographics,
allergies,
medical conditions,
contact information
Real-time search filtering
Form validation before saving
Clinical Vitals System
Record:
blood pressure,
temperature,
heart rate,
respiratory rate,
oxygen saturation,
height,
weight,
BMI
Automatic BMI calculation
Out-of-range alerts
Highlight abnormal values visually
Confirmation prompt before saving abnormal vitals
Dispensing & Prescription Module
Medicine dispensing workflow
Prescription recording
Inventory deduction integration
Allergy warning banner before dispensing
Dispense history tracking
Inventory Management
Medicine inventory tracking
Batch/Lot number support
Stock quantity monitoring
Expiration date tracking
Low-stock visual alerts
Medication recall support
Queue Management
Student/patient queue tracking
Priority levels:
Normal
Urgent
Emergency
Color-coded priority visualization
Queue status management
Audit Trail System

Every critical action is logged:

Add
Edit
Delete
Dispense
Login events

Audit records include:

user,
timestamp,
affected record,
action type

This improves:

accountability,
traceability,
administrative monitoring.
Reporting & Printing

Each major module supports:

formatted print previews,
HTML-based report generation,
browser printing support.
Backup System

Integrated backup utility:

creates timestamped backup folders,
copies all CSV databases,
supports lightweight disaster recovery.
What's New in v9
Architecture Improvements
Improvement	Description
✅ Modular page system	UI pages separated into focused modules
✅ Expanded model layer	Stronger object-oriented domain modeling
✅ Cleaner backend separation	Reduced direct UI-to-storage coupling
✅ Centralized configuration	Shared constants and enums in config
✅ Improved validation	Consistent validation workflow across forms
✅ Better error handling	Removed silent exception patterns
✅ Dashboard stat extraction	Business logic separated from UI widgets
✅ Reusable table framework	Shared table-page behavior across modules
Clinical & Workflow Improvements
Improvement	Description
✅ Allergy safety alerts	Dispense module warns against allergy conflicts
✅ Auto BMI computation	BMI updates dynamically from height/weight
✅ Abnormal vitals highlighting	Unsafe ranges visually emphasized
✅ Queue priority workflow	Emergency handling support
✅ Batch/Lot tracking	Medication recall traceability
✅ Real-time search	Instant filtering across modules
✅ Audit monitoring	Full action history viewer
✅ Printable reports	HTML-based print support
Technology Stack
Component	Technology
Language	Python
GUI Framework	PyQt6
Data Storage	CSV
Styling	Qt Style Sheets (QSS)
Packaging	PyInstaller
Architecture Style	Modular Layered Architecture
Project Structure
campus_clinic_system_v9/
├── main.py
├── requirements.txt
├── ClinicSystem.spec
├── populate_sample_data.py
│
├── backend/
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── dashboard_stats.py
│   ├── inventory.py
│   ├── models.py
│   ├── queue_logic.py
│   └── utils.py
│
├── data/
│   ├── patients.csv
│   ├── inventory.csv
│   ├── vitals.csv
│   ├── queue.csv
│   ├── prescriptions.csv
│   └── audit_log.csv
│
├── ui/
│   ├── dashboard_window.py
│   ├── login_window.py
│   │
│   └── pages/
│       ├── audit_page.py
│       ├── dispense_page.py
│       ├── home_page.py
│       ├── inventory_page.py
│       ├── patient_page.py
│       ├── queue_page.py
│       ├── table_page.py
│       └── vitals_page.py
│
└── backups/
Installation
1. Clone the Repository
git clone <repository-url>
cd campus_clinic_system_v9
2. Install Dependencies
pip install -r requirements.txt

Minimal requirement:

pip install PyQt6
Running the Application
python main.py
Default Login
Username: admin
Password: admin123

Change default credentials immediately in production usage.

Architectural Notes
Current Persistence Design

The system currently uses:

CSV-based persistence

Advantages:

lightweight,
portable,
zero setup,
beginner-friendly.

Limitations:

no transactions,
limited scalability,
entire-file rewrites,
weaker concurrency safety.

Future planned migration:

SQLite database layer
Design Patterns Used

The project partially implements:

Repository-style persistence abstraction
Observer pattern via Qt signals/slots
Layered modular architecture
Domain model abstraction
Shared component reuse
Known Limitations
Area	Limitation
Persistence	CSV is not ideal for large-scale systems
Concurrency	Single-process desktop design
Threading	Some operations remain synchronous
Security	Requires stronger production-grade authentication
Testing	Automated tests are limited
Future Improvements
Planned Refactors
SQLite migration
Service layer abstraction
QThread background operations
Stronger typing/dataclasses
Automated testing
Role-based permissions
Export to PDF/Excel
Advanced analytics dashboard
Engineering Focus

This project emphasizes:

practical desktop application engineering,
modularization,
GUI architecture,
CRUD workflows,
maintainable PyQt6 structure,
and clinical workflow simulation.
Educational Value

The project demonstrates concepts in:

Object-Oriented Programming
GUI Engineering
Event-Driven Architecture
Data Persistence
Software Modularity
Validation Systems
User Workflow Design
Desktop Application Packaging
License

This project is intended for:

academic use,
educational demonstrations,
portfolio development,
and software engineering practice.
