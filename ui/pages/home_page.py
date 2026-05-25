import os, sys, csv, datetime
from datetime import datetime as _dt

from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtGui import (
    QColor, QFont, QLinearGradient, QBrush, QPainter, QPen,
)
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDateEdit, QDialog, QFrame,
    QGraphicsDropShadowEffect, QGridLayout,
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
from backend.dashboard_stats import DashboardStats as _Stats
from ui.pages.base_page import BasePage

# =============================================================================

HOME_STYLE = """
/* ── Page bg ─────────────────────────────────── */
#dash_scroll  { border: none; background: #f5f6fa; }
#dash_body    { background: #f5f6fa; }

/* ── Metric cards ────────────────────────────── */
#metric_card {
    background: #ffffff;
    border: 1px solid #d0d8ef;
    border-top: 4px solid #f0c040;
    border-radius: 10px;
}
#metric_card:hover { border-top-color: #1a3a8a; }

#mc_label      { font-size: 11px; font-weight: 700;
                 color: #5a6480; text-transform: uppercase; letter-spacing: 0.4px; }
#mc_value      { font-size: 30px; font-weight: 800; color: #0d2260; }
#mc_delta_up   { font-size: 11px; font-weight: 700; color: #1a7a4a; }
#mc_delta_down { font-size: 11px; font-weight: 700; color: #c0392b; }
#mc_delta_sub  { font-size: 11px; color: #9ca3af; }

/* ── Panel cards ─────────────────────────────── */
#panel_card {
    background: #ffffff;
    border: 1px solid #d0d8ef;
    border-radius: 10px;
}
#panel_header {
    background: #1a3a8a;
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    min-height: 40px; max-height: 40px;
}
#panel_title  { color: #ffffff; font-size: 12px; font-weight: 800; }

/* ── Panel table ─────────────────────────────── */
QTableWidget {
    background: #ffffff; border: none;
    color: #1a1a2e; gridline-color: #e8ebf2;
    selection-background-color: #fff8e1; selection-color: #0d2260;
    alternate-background-color: #f5f6fa;
}
QHeaderView::section {
    background: #f5f6fa; color: #5a6480; border: none;
    border-bottom: 1px solid #d0d8ef;
    padding: 6px 10px; font-size: 10px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.3px;
}
QTableWidget::item { padding: 8px 10px; font-size: 11px; }
QTableWidget::item:selected { background: #fff8e1; color: #0d2260; font-weight: 600; }

/* ── Status pills ────────────────────────────── */
#pill_confirmed { background: #e6f4ec; color: #1a7a4a; border-radius: 8px;
                  padding: 2px 8px; font-size: 10px; font-weight: 700; }
#pill_pending   { background: #fdf6e3; color: #c9a227; border-radius: 8px;
                  padding: 2px 8px; font-size: 10px; font-weight: 700; }
#pill_cancelled { background: #fdecea; color: #c0392b; border-radius: 8px;
                  padding: 2px 8px; font-size: 10px; font-weight: 700; }

/* ── Empty state ─────────────────────────────── */
#empty_label { color: #b0bdd8; font-size: 12px; }

/* Scrollbars */
QScrollBar:vertical { background: #f0f1f5; width: 4px; border-radius: 2px; }
QScrollBar::handle:vertical { background: #c0cce0; border-radius: 2px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


# ── Rounded icon square ───────────────────────────────────────────────────────

class _IconCircle(QWidget):
    def __init__(self, emoji: str, bg: str, size: int = 40):
        super().__init__()
        self.setFixedSize(size, size)
        self._emoji = emoji
        self._bg    = QColor(bg)
        self._size  = size

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._bg))
        r = self._size * 0.25
        p.drawRoundedRect(0, 0, self._size, self._size, r, r)
        p.setPen(QPen(QColor("white")))
        p.setFont(QFont("Segoe UI Emoji", int(self._size * 0.38)))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._emoji)


# ── Metric card ───────────────────────────────────────────────────────────────

class MetricCard(QWidget):
    _CFG = {
        "Total Patients":       ("👥", "#1a3a8a", "#0d1f3c"),
        "Today's Appointments": ("📅", "#6366f1", "#1e1e4a"),
        "Low Medicine Stock":   ("💊", "#c9a227", "#3d2f10"),
        "Active Queue":         ("🩺", "#1a7a4a", "#0d3028"),
        "Pending Clearances":   ("📋", "#8b5cf6", "#2a1f45"),
        "Total Incidents":      ("⚠️",  "#c0392b", "#3d1515"),
    }

    def __init__(self, title: str, value: str, change: str = ""):
        super().__init__()
        self.setObjectName("metric_card")
        self.setMinimumHeight(148)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        emoji, icon_color, icon_bg = self._CFG.get(title, ("📊", "#1a3a8a", "#0d1f3c"))

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(0)

        # Top row
        top = QHBoxLayout()
        lbl = QLabel(title)
        lbl.setObjectName("mc_label")
        top.addWidget(lbl)
        top.addStretch()

        ico      = _IconCircle(emoji, icon_bg, 40)
        ico_wrap = QWidget()
        ico_wrap.setFixedSize(42, 42)
        ico_wrap.setStyleSheet(
            f"border: 1px solid {icon_color}50; border-radius: 11px; background: transparent;"
        )
        ico_inner = QVBoxLayout(ico_wrap)
        ico_inner.setContentsMargins(1, 1, 1, 1)
        ico_inner.addWidget(ico)
        top.addWidget(ico_wrap)
        root.addLayout(top)
        root.addSpacing(12)

        # Value
        val = QLabel(str(value))
        val.setObjectName("mc_value")
        root.addWidget(val)
        root.addSpacing(8)

        # Delta
        if change:
            d_row    = QHBoxLayout()
            positive = "+" in change
            arrow    = "↑" if positive else "↓"
            obj      = "mc_delta_up" if positive else "mc_delta_down"
            arr_lbl  = QLabel(f"{arrow}  {change.lstrip('+-').strip()}")
            arr_lbl.setObjectName(obj)
            d_row.addWidget(arr_lbl)
            sub_lbl = QLabel("vs last week")
            sub_lbl.setObjectName("mc_delta_sub")
            d_row.addWidget(sub_lbl)
            d_row.addStretch()
            root.addLayout(d_row)

        root.addStretch()

        fx = QGraphicsDropShadowEffect()
        fx.setBlurRadius(20)
        fx.setOffset(0, 4)
        fx.setColor(QColor("#00000018"))
        self.setGraphicsEffect(fx)


# ── Panel card helper ─────────────────────────────────────────────────────────

def _panel_card(title: str, icon: str = "") -> tuple:
    """Returns (outer_widget, body_layout)."""
    card = QWidget()
    card.setObjectName("panel_card")
    c_lay = QVBoxLayout(card)
    c_lay.setContentsMargins(0, 0, 0, 0)
    c_lay.setSpacing(0)

    header = QWidget()
    header.setObjectName("panel_header")
    h_lay  = QHBoxLayout(header)
    h_lay.setContentsMargins(14, 0, 14, 0)
    t_lbl = QLabel(f"{icon}  {title}" if icon else title)
    t_lbl.setObjectName("panel_title")
    h_lay.addWidget(t_lbl)
    h_lay.addStretch()
    c_lay.addWidget(header)

    body   = QWidget()
    b_lay  = QVBoxLayout(body)
    b_lay.setContentsMargins(0, 0, 0, 0)
    b_lay.setSpacing(0)
    c_lay.addWidget(body, 1)

    # Drop shadow
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(18)
    fx.setOffset(0, 3)
    fx.setColor(QColor("#00000015"))
    card.setGraphicsEffect(fx)

    return card, b_lay


# ── Homepage ──────────────────────────────────────────────────────────────────

class HomePage(QWidget):
    """Royal Dark dashboard home page."""

    def __init__(self):
        super().__init__()
        self._stats = _Stats()
        self._scroll_ref = None
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(HOME_STYLE)
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        self._build_scroll(page_layout)

    def _build_scroll(self, parent_layout):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("dash_scroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        body.setObjectName("dash_body")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(28, 24, 28, 28)
        body_layout.setSpacing(20)

        # ── Greeting header ───────────────────────────────────────────────────
        greet_row = QHBoxLayout()
        greet_lbl = QLabel(f"Good {self._time_of_day()}, welcome back 👋")
        greet_lbl.setStyleSheet(
            "font-size: 18px; font-weight: 800; color: #0d2260;"
        )
        greet_row.addWidget(greet_lbl)
        greet_row.addStretch()
        date_lbl = QLabel(_dt.now().strftime("%A, %B %d %Y"))
        date_lbl.setStyleSheet("font-size: 12px; color: #5a6480; font-weight: 600;")
        greet_row.addWidget(date_lbl)
        body_layout.addLayout(greet_row)

        # ── Metric cards ──────────────────────────────────────────────────────
        metrics = [
            ("Total Patients",       self._count_patients(),           self._patients_change()),
            ("Today's Appointments", self._count_today_appointments(), self._appointments_change()),
            ("Low Medicine Stock",   self._count_low_stock(),          self._low_stock_change()),
            ("Active Queue",         self._count_active_queue(),       self._active_queue_change()),
            ("Pending Clearances",   self._count_pending_clearances(), self._pending_clearances_change()),
            ("Total Incidents",      self._count_incidents(),          self._incidents_change()),
        ]
        grid = QGridLayout()
        grid.setSpacing(14)
        r = c = 0
        for t, v, ch in metrics:
            grid.addWidget(MetricCard(t, str(v), ch), r, c)
            c += 1
            if c >= 3:
                c = 0
                r += 1
        body_layout.addLayout(grid)

        # ── Lower panels ──────────────────────────────────────────────────────
        lower = QHBoxLayout()
        lower.setSpacing(14)
        lower.addWidget(self._build_appointments_panel(), 1)
        lower.addWidget(self._build_stock_panel(), 1)
        body_layout.addLayout(lower)

        body_layout.addStretch()

        scroll.setWidget(body)
        parent_layout.addWidget(scroll)
        self._scroll_ref = scroll

    # ── Panel builders ────────────────────────────────────────────────────────

    def _build_appointments_panel(self) -> QWidget:
        card, b_lay = _panel_card("Today's Appointments", "📅")
        appts = self._get_today_appointments()

        if not appts:
            emp = QLabel("No appointments scheduled for today")
            emp.setObjectName("empty_label")
            emp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            b_lay.addWidget(emp)
        else:
            tbl = QTableWidget(len(appts), 3)
            tbl.setHorizontalHeaderLabels(["Patient", "Reason", "Status"])
            tbl.verticalHeader().setVisible(False)
            tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            tbl.setAlternatingRowColors(True)
            tbl.setShowGrid(True)
            tbl.horizontalHeader().setStretchLastSection(True)
            for i, a in enumerate(appts):
                tbl.setItem(i, 0, QTableWidgetItem(a["patient_name"]))
                tbl.setItem(i, 1, QTableWidgetItem(a["reason"]))
                # Status pill
                status = a["status"].lower()
                obj    = {"confirmed": "pill_confirmed",
                          "pending":   "pill_pending",
                          "cancelled": "pill_cancelled"}.get(status, "pill_pending")
                pill = QLabel(a["status"].capitalize())
                pill.setObjectName(obj)
                pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
                tbl.setCellWidget(i, 2, pill)
            tbl.resizeColumnsToContents()
            tbl.horizontalHeader().setStretchLastSection(True)
            b_lay.addWidget(tbl)

        return card

    def _build_stock_panel(self) -> QWidget:
        card, b_lay = _panel_card("Low Stock / Expiring Soon", "⚠️")
        items = self._get_low_stock_items()

        if not items:
            emp = QLabel("All inventory is at healthy levels ✓")
            emp.setObjectName("empty_label")
            emp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            b_lay.addWidget(emp)
        else:
            tbl = QTableWidget(len(items), 3)
            tbl.setHorizontalHeaderLabels(["Item", "Qty", "Reorder At"])
            tbl.verticalHeader().setVisible(False)
            tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            tbl.setAlternatingRowColors(True)
            tbl.setShowGrid(True)
            tbl.horizontalHeader().setStretchLastSection(True)
            for i, it in enumerate(items):
                name_item = QTableWidgetItem(it["name"])
                qty_item  = QTableWidgetItem(
                    f"{it['quantity']} {it.get('unit','')}"
                )
                qty_item.setForeground(QColor("#c0392b"))
                reord_item = QTableWidgetItem(str(it["reorder_level"]))
                tbl.setItem(i, 0, name_item)
                tbl.setItem(i, 1, qty_item)
                tbl.setItem(i, 2, reord_item)
            tbl.resizeColumnsToContents()
            tbl.horizontalHeader().setStretchLastSection(True)
            b_lay.addWidget(tbl)

        return card

    # ── Refresh ───────────────────────────────────────────────────────────────

    def load_data(self):
        """Tear-down + rebuild the entire scroll body."""
        layout = self.layout()
        old    = layout.itemAt(0)
        if old and old.widget():
            old.widget().deleteLater()
            layout.removeItem(old)
        self._build_scroll(layout)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _time_of_day() -> str:
        h = _dt.now().hour
        if h < 12:
            return "morning"
        if h < 17:
            return "afternoon"
        return "evening"

    @staticmethod
    def _week_range(weeks_ago: int = 0):
        today = datetime.date.today()
        start = today - datetime.timedelta(days=today.weekday() + weeks_ago * 7)
        end   = start + datetime.timedelta(days=6)
        return start, end

    @staticmethod
    def _fmt_change(this_week: int, last_week: int) -> str:
        diff = this_week - last_week
        if diff > 0:
            return f"+{diff} this week"
        if diff < 0:
            return f"{diff} this week"
        return "No change this week"

    # ── Stat counters (same logic as original, cleaned up) ────────────────────

    def _count_patients(self) -> int:
        try:
            with open(PATIENTS_CSV, "r", encoding="utf-8") as f:
                return sum(1 for _ in csv.DictReader(f))
        except (FileNotFoundError, IOError):
            return 0

    def _patients_change(self) -> str:
        this_start, this_end = self._week_range(0)
        last_start, last_end = self._week_range(1)
        def _week(s, e):
            n = 0
            try:
                with open(PATIENTS_CSV, "r", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        try:
                            dt = datetime.date.fromisoformat(row.get("Date of Birth","")[:10])
                        except ValueError:
                            continue
                        if s <= dt <= e:
                            n += 1
            except (FileNotFoundError, IOError):
                pass
            return n
        return self._fmt_change(_week(this_start, this_end),
                                _week(last_start, last_end))

    def _count_today_appointments(self) -> int:
        today = _dt.now().strftime("%Y-%m-%d")
        try:
            with open(APPOINTMENTS_CSV, "r", encoding="utf-8") as f:
                return sum(1 for r in csv.DictReader(f)
                           if r.get("date_time", "").startswith(today))
        except (FileNotFoundError, IOError):
            return 0

    def _appointments_change(self) -> str:
        def _week(s, e):
            n = 0
            try:
                with open(APPOINTMENTS_CSV, "r", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        try:
                            dt = datetime.date.fromisoformat(
                                row.get("date_time", "")[:10])
                            if s <= dt <= e:
                                n += 1
                        except ValueError:
                            pass
            except (FileNotFoundError, IOError):
                pass
            return n
        ts, te = self._week_range(0)
        ls, le = self._week_range(1)
        return self._fmt_change(_week(ts, te), _week(ls, le))

    def _count_low_stock(self) -> int:
        n = 0
        try:
            with open(INVENTORY_CSV, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    try:
                        if float(row.get("quantity", 0)) <= float(row.get("reorder_level", 0)):
                            n += 1
                    except (ValueError, TypeError):
                        pass
        except (FileNotFoundError, IOError):
            pass
        return n

    def _low_stock_change(self) -> str:
        n = self._count_low_stock()
        if n == 0:
            return "All stock healthy"
        return f"{n} item{'s' if n != 1 else ''} need reorder"

    def _count_active_queue(self) -> int:
        n = 0
        try:
            with open(QUEUE_CSV, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get("status", "").lower() in ("waiting", "in progress"):
                        n += 1
        except (FileNotFoundError, IOError):
            pass
        return n

    def _active_queue_change(self) -> str:
        n = self._count_active_queue()
        if n == 0:
            return "Queue is clear"
        return f"{n} patient{'s' if n != 1 else ''} waiting"

    def _count_pending_clearances(self) -> int:
        n = 0
        try:
            with open(CLEARANCE_CSV, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get("status", "").lower() in ("pending", "valid"):
                        n += 1
        except (FileNotFoundError, IOError):
            pass
        return n

    def _pending_clearances_change(self) -> str:
        def _week(s, e):
            n = 0
            try:
                with open(CLEARANCE_CSV, "r", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        try:
                            dt = datetime.date.fromisoformat(
                                row.get("date_issued", "")[:10])
                            if s <= dt <= e:
                                n += 1
                        except ValueError:
                            pass
            except (FileNotFoundError, IOError):
                pass
            return n
        ts, te = self._week_range(0)
        ls, le = self._week_range(1)
        return self._fmt_change(_week(ts, te), _week(ls, le))

    def _count_incidents(self) -> int:
        try:
            with open(INCIDENTS_CSV, "r", encoding="utf-8") as f:
                return sum(1 for _ in csv.DictReader(f))
        except (FileNotFoundError, IOError):
            return 0

    def _incidents_change(self) -> str:
        def _week(s, e):
            n = 0
            try:
                with open(INCIDENTS_CSV, "r", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        try:
                            dt = datetime.date.fromisoformat(
                                row.get("date_time", "")[:10])
                            if s <= dt <= e:
                                n += 1
                        except ValueError:
                            pass
            except (FileNotFoundError, IOError):
                pass
            return n
        ts, te = self._week_range(0)
        ls, le = self._week_range(1)
        return self._fmt_change(_week(ts, te), _week(ls, le))

    def _get_today_appointments(self) -> list:
        today  = _dt.now().strftime("%Y-%m-%d")
        result = []
        try:
            with open(APPOINTMENTS_CSV, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get("date_time", "").startswith(today):
                        result.append({
                            "patient_name": self._get_patient_name(
                                row.get("patient_id", "")),
                            "reason":    row.get("reason", ""),
                            "date_time": row.get("date_time", ""),
                            "status":    row.get("status", ""),
                        })
        except (FileNotFoundError, IOError):
            pass
        return sorted(result, key=lambda x: x["date_time"])

    def _get_patient_name(self, pid: str) -> str:
        try:
            with open(PATIENTS_CSV, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get("patient_id") == pid:
                        return (
                            f"{row.get('first_name','')} {row.get('last_name','')}".strip()
                            or pid
                        )
        except (FileNotFoundError, IOError):
            pass
        return pid

    def _get_low_stock_items(self) -> list:
        result = []
        try:
            with open(INVENTORY_CSV, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    try:
                        qty    = float(row.get("quantity", "0"))
                        reord  = float(row.get("reorder_level", "0"))
                        if qty <= reord:
                            result.append({
                                "name":          row.get("name", ""),
                                "quantity":      int(qty),
                                "unit":          row.get("unit", ""),
                                "reorder_level": int(reord),
                            })
                    except (ValueError, TypeError):
                        pass
        except (FileNotFoundError, IOError):
            pass
        return sorted(result, key=lambda x: x["quantity"])
