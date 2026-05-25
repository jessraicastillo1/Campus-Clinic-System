"""
audit_page.py  –  Read-only view of the audit trail.
Shows who did what and when across all modules.
"""
import os, sys, csv, datetime, hashlib
from datetime import datetime as _dt

from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtGui import QColor, QFont, QIcon, QLinearGradient, QBrush, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFormLayout, QFrame, QGraphicsDropShadowEffect, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from backend.config import *
from backend.utils import *
from backend.database import *
from ui.pages.base_page import BasePage
from ui.pages.table_page import TablePage

# =============================================================================

class AuditPage(TablePage):
    DEFAULT_HEADERS = ["timestamp", "user", "action", "module", "record_id", "details"]

    def __init__(self, role: str = "viewer"):
        super().__init__("Audit Log", AUDIT_CSV, role)
        # Audit log is read-only — hide Add / Edit / Delete
        self._add_button.setVisible(False)
        self._edit_button.setVisible(False)
        self._delete_button.setVisible(False)

    def on_add(self):    pass
    def on_edit(self):   pass
    def on_delete(self): pass

# =============================================================================
