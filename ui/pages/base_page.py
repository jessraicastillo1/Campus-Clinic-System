import os
import sys
import csv
import datetime
from datetime import datetime as _dt

from PyQt6.QtCore import Qt, QSize, QDate, QTimer
from PyQt6.QtGui import (
    QColor, QFont, QIcon, QLinearGradient, QBrush, QPainter, QPen,
)
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
from backend.auth import *
from backend.inventory import *
from backend.queue_logic import *

# =============================================================================


class BasePage(QWidget):

    def __init__(self, title: str):
        super().__init__()
        self._title = title
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Breadcrumb bar
        crumb_bar = QWidget()
        crumb_bar.setObjectName("crumb_bar")
        crumb_lay = QHBoxLayout(crumb_bar)
        crumb_lay.setContentsMargins(20, 0, 20, 0)
        crumb_lay.setSpacing(6)
        crumb_home = QLabel("Home")
        crumb_home.setObjectName("crumb_item")
        crumb_sep = QLabel("›")
        crumb_sep.setObjectName("crumb_sep")
        crumb_current = QLabel(self._title)
        crumb_current.setObjectName("crumb_current")
        crumb_lay.addWidget(crumb_home)
        crumb_lay.addWidget(crumb_sep)
        crumb_lay.addWidget(crumb_current)
        crumb_lay.addStretch()
        layout.addWidget(crumb_bar)

        # Page body scroll area
        scroll = QScrollArea()
        scroll.setObjectName("page_scroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body_widget = QWidget()
        body_widget.setObjectName("page_body_widget")
        self.body_layout = QVBoxLayout(body_widget)
        self.body_layout.setContentsMargins(20, 16, 20, 16)
        self.body_layout.setSpacing(12)

        scroll.setWidget(body_widget)
        layout.addWidget(scroll, 1)

    # ─── Toast notification ───────────────────────────────────────────────────

    def show_toast(self, message: str, kind: str = "success"):
        """Display a floating toast notification for 3 seconds."""
        _COLORS = {
            "success": ("#1a7a4a", "#ffffff"),
            "error":   ("#c0392b", "#ffffff"),
            "info":    ("#1a3a8a", "#ffffff"),
            "warn":    ("#c9a227", "#0d2260"),
        }
        bg, fg = _COLORS.get(kind, _COLORS["success"])
        icons = {"success": "✓", "error": "✕", "info": "ℹ", "warn": "⚠"}
        icon = icons.get(kind, "✓")

        toast = QLabel(f"  {icon}  {message}  ", self)
        toast.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: {fg};
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
                padding: 10px 16px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor("#00000040"))
        toast.setGraphicsEffect(shadow)
        toast.adjustSize()
        toast.setFixedWidth(max(toast.width(), 260))

        # Position bottom-right of page
        x = self.width() - toast.width() - 24
        y = self.height() - toast.height() - 24
        toast.move(x, y)
        toast.raise_()
        toast.show()

        QTimer.singleShot(3000, toast.deleteLater)

    def resizeEvent(self, event):
        super().resizeEvent(event)


# =============================================================================
