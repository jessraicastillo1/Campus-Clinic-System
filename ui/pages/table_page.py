import os
import sys
import csv
import datetime
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
from backend.auth import *
from backend.inventory import *
from backend.queue_logic import *
from ui.pages.base_page import BasePage

# =============================================================================
# Royal Dark — TablePage stylesheet
# Tokens: sidebar #0d2260 · nav active #1a3a8a · gold #f0c040
#         page bg #f5f6fa · card bg #ffffff · body text #1a1a2e
#         border/muted #d0d8ef · alt row #f5f6fa · selected #fff8e1
# =============================================================================

TABLE_PAGE_STYLE = """
/* ── Crumb bar ── */
#crumb_bar {
    background: #ffffff;
    border-bottom: 1px solid #d0d8ef;
    min-height: 32px;
    max-height: 32px;
}
#crumb_item    { color: #5a6480;  font-size: 10px; }
#crumb_sep     { color: #d0d8ef;  font-size: 10px; }
#crumb_current { color: #1a3a8a;  font-size: 10px; font-weight: 700; }

/* ── Page body ── */
#page_body_widget { background: #f5f6fa; }
#page_scroll      { background: #f5f6fa; border: none; }

/* ── Table card ── */
#table_card {
    background: #ffffff;
    border: 1px solid #d0d8ef;
    border-radius: 10px;
}

/* ── Card toolbar ── */
#card_toolbar {
    background: #ffffff;
    border-bottom: 1px solid #d0d8ef;
    border-top-left-radius:  10px;
    border-top-right-radius: 10px;
    min-height: 52px;
    max-height: 52px;
}
#card_title {
    color: #1a3a8a;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.2px;
}

/* ── Search box ── */
#search_box {
    background: #f5f6fa;
    border: 1.5px solid #d0d8ef;
    border-radius: 7px;
    padding: 5px 12px 5px 10px;
    font-size: 11px;
    color: #1a1a2e;
    min-width: 200px;
    max-height: 32px;
}
#search_box:focus {
    border-color: #1a3a8a;
    background: #ffffff;
}

/* ── Action buttons ── */
#btn_add {
    background: #f0c040;
    color: #0d2260;
    border: none;
    border-radius: 6px;
    padding: 0 14px;
    font-size: 11px;
    font-weight: 800;
    max-height: 32px;
    min-height: 32px;
}
#btn_add:hover   { background: #e5b830; }
#btn_add:pressed { background: #d4a820; }

#btn_edit {
    background: #ffffff;
    color: #1a3a8a;
    border: 1.5px solid #1a3a8a;
    border-radius: 6px;
    padding: 0 14px;
    font-size: 11px;
    font-weight: 700;
    max-height: 32px;
    min-height: 32px;
}
#btn_edit:hover   { background: #e8edf8; }
#btn_edit:pressed { background: #d0d8ef; }

#btn_delete {
    background: #fdecea;
    color: #c0392b;
    border: 1.5px solid rgba(192,57,43,0.28);
    border-radius: 6px;
    padding: 0 14px;
    font-size: 11px;
    font-weight: 700;
    max-height: 32px;
    min-height: 32px;
}
#btn_delete:hover   { background: #f8c8c5; }
#btn_delete:pressed { background: #f0a8a5; }

#btn_print {
    background: #ffffff;
    color: #5a6480;
    border: 1.5px solid #d0d8ef;
    border-radius: 6px;
    padding: 0 14px;
    font-size: 11px;
    font-weight: 600;
    max-height: 32px;
    min-height: 32px;
}
#btn_print:hover   { background: #f5f6fa; color: #1a1a2e; }
#btn_print:pressed { background: #e8edf8; }

/* ── Row count / status label ── */
#row_count_label {
    color: #5a6480;
    font-size: 10px;
    padding-left: 4px;
}

/* ── QTableWidget — Royal Dark ── */
QTableWidget {
    background: #ffffff;
    border: none;
    border-bottom-left-radius:  10px;
    border-bottom-right-radius: 10px;
    color: #1a1a2e;
    gridline-color: #e8ebf2;
    selection-background-color: #fff8e1;
    selection-color: #0d2260;
    alternate-background-color: #f5f6fa;
    outline: none;
}

/* ── Column headers ── */
QHeaderView {
    background: #1a3a8a;
}
QHeaderView::section {
    background: #1a3a8a;
    color: #ffffff;
    border: none;
    border-right: 1px solid rgba(255,255,255,0.10);
    padding: 10px 12px;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}
QHeaderView::section:first { border-top-left-radius: 0; }
QHeaderView::section:last  { border-right: none; }
QHeaderView::section:hover { background: #1e4aa8; }

/* ── Rows ── */
QTableWidget::item {
    padding: 9px 12px;
    font-size: 11px;
    border: none;
}
QTableWidget::item:selected {
    background: #fff8e1;
    color: #0d2260;
    font-weight: 600;
}
QTableWidget::item:hover:!selected {
    background: #f0f4ff;
}

/* ── Scrollbars inside the table ── */
QScrollBar:vertical {
    background: #f0f1f5;
    width: 6px;
    border-radius: 3px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #b0bdd8;
    border-radius: 3px;
    min-height: 32px;
}
QScrollBar::handle:vertical:hover { background: #1a3a8a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #f0f1f5;
    height: 6px;
    border-radius: 3px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #b0bdd8;
    border-radius: 3px;
    min-width: 32px;
}
QScrollBar::handle:horizontal:hover { background: #1a3a8a; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""

# ── Shared themed-dialog stylesheets ─────────────────────────────────────────

_MB_INFO_STYLE = """
QMessageBox { background: #ffffff; }
QMessageBox QLabel { color: #1a1a2e; font-size: 12px; min-width: 260px; }
QPushButton {
    background: #1a3a8a; color: #ffffff; border: none;
    border-radius: 6px; padding: 7px 22px;
    font-weight: 700; font-size: 11px; min-width: 88px;
}
QPushButton:hover   { background: #1e4aa8; }
QPushButton:pressed { background: #0d2260; }
"""

_MB_WARN_STYLE = """
QMessageBox { background: #ffffff; }
QMessageBox QLabel { color: #1a1a2e; font-size: 12px; min-width: 260px; }
QPushButton {
    background: #f0c040; color: #0d2260; border: none;
    border-radius: 6px; padding: 7px 22px;
    font-weight: 800; font-size: 11px; min-width: 88px;
}
QPushButton:hover   { background: #e5b830; }
QPushButton:pressed { background: #d4a820; }
"""

_MB_CONFIRM_STYLE = """
QMessageBox { background: #ffffff; }
QMessageBox QLabel { color: #1a1a2e; font-size: 12px; min-width: 260px; }
QPushButton {
    background: #1a3a8a; color: #ffffff; border: none;
    border-radius: 6px; padding: 7px 22px;
    font-weight: 700; font-size: 11px; min-width: 88px;
}
QPushButton:hover   { background: #1e4aa8; }
QPushButton:pressed { background: #0d2260; }
QPushButton[text="&Yes"], QPushButton[text="Yes"] {
    background: #c0392b;
}
QPushButton[text="&Yes"]:hover, QPushButton[text="Yes"]:hover {
    background: #a93226;
}
"""

_MB_NO_SEL_STYLE = """
QMessageBox { background: #ffffff; }
QMessageBox QLabel {
    color: #1a3a8a;
    font-size: 12px;
    min-width: 260px;
}
QPushButton {
    background: #f0c040; color: #0d2260; border: none;
    border-radius: 6px; padding: 7px 22px;
    font-weight: 800; font-size: 11px; min-width: 88px;
}
QPushButton:hover   { background: #e5b830; }
QPushButton:pressed { background: #d4a820; }
"""


def _mb_info(parent, title: str, text: str) -> None:
    """Themed information dialog."""
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setIcon(QMessageBox.Icon.Information)
    mb.setStandardButtons(QMessageBox.StandardButton.Ok)
    mb.setStyleSheet(_MB_INFO_STYLE)
    mb.exec()


def _mb_warn(parent, title: str, text: str) -> None:
    """Themed warning dialog."""
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setIcon(QMessageBox.Icon.Warning)
    mb.setStandardButtons(QMessageBox.StandardButton.Ok)
    mb.setStyleSheet(_MB_WARN_STYLE)
    mb.exec()


def _mb_no_selection(parent, action: str = "perform this action") -> None:
    """
    Styled 'nothing selected' prompt — shown whenever Edit / Delete is
    triggered without a row highlighted in the table.
    """
    mb = QMessageBox(parent)
    mb.setWindowTitle("No Record Selected")
    mb.setText(
        f"<b>Please select a record first.</b><br><br>"
        f"Highlight a row in the table, then choose <i>{action}</i> again."
    )
    mb.setIcon(QMessageBox.Icon.Information)
    mb.setStandardButtons(QMessageBox.StandardButton.Ok)
    mb.setStyleSheet(_MB_NO_SEL_STYLE)
    mb.exec()


def _mb_confirm_delete(parent, record_label: str = "this record") -> bool:
    """
    Themed yes/no confirmation before a destructive delete.
    Returns True if the user confirmed.
    """
    mb = QMessageBox(parent)
    mb.setWindowTitle("Confirm Delete")
    mb.setText(
        f"<b>Delete {record_label}?</b><br><br>"
        "This action <b>cannot be undone</b>."
    )
    mb.setIcon(QMessageBox.Icon.Warning)
    mb.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    mb.setDefaultButton(QMessageBox.StandardButton.No)
    mb.setStyleSheet(_MB_CONFIRM_STYLE)
    return mb.exec() == QMessageBox.StandardButton.Yes


# =============================================================================


class TablePage(BasePage):

    DEFAULT_HEADERS = []

    # Subclasses declare which column keys are PHI / sensitive.
    SENSITIVE_COLUMNS: list = []

    def __init__(self, title: str, csv_path: str,
                 role: str = "viewer", username: str = ""):
        self._csv_path = csv_path
        self._role     = role.lower()
        self._username = username
        self._table    = None
        self._headers  = []
        self._all_rows = []
        super().__init__(title)
        self.setStyleSheet(TABLE_PAGE_STYLE)
        self._init_content()
        self._apply_role_permissions()
        self.load_data()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _init_content(self):
        # ── Table card wrapper ────────────────────────────────────────────────
        card = QWidget()
        card.setObjectName("table_card")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setObjectName("card_toolbar")
        tb_lay = QHBoxLayout(toolbar)
        tb_lay.setContentsMargins(16, 0, 16, 0)
        tb_lay.setSpacing(8)

        title_lbl = QLabel(f"  {self._title}")
        title_lbl.setObjectName("card_title")
        tb_lay.addWidget(title_lbl)
        tb_lay.addStretch()

        # Search box
        self._search_box = QLineEdit()
        self._search_box.setObjectName("search_box")
        self._search_box.setPlaceholderText("🔍  Search…")
        self._search_box.setClearButtonEnabled(True)
        self._search_box.textChanged.connect(self._apply_filter)
        tb_lay.addWidget(self._search_box)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet("background: #d0d8ef; margin: 10px 2px;")
        tb_lay.addWidget(sep)

        # Action buttons
        self._add_button = QPushButton("＋  Add")
        self._add_button.setObjectName("btn_add")
        self._add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_button.clicked.connect(self.on_add)
        tb_lay.addWidget(self._add_button)

        self._edit_button = QPushButton("✎  Edit")
        self._edit_button.setObjectName("btn_edit")
        self._edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._edit_button.clicked.connect(self.on_edit)
        tb_lay.addWidget(self._edit_button)

        self._delete_button = QPushButton("🗑  Delete")
        self._delete_button.setObjectName("btn_delete")
        self._delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_button.clicked.connect(self.on_delete)
        tb_lay.addWidget(self._delete_button)

        self._print_button = QPushButton("🖨  Print")
        self._print_button.setObjectName("btn_print")
        self._print_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._print_button.clicked.connect(self.on_print)
        tb_lay.addWidget(self._print_button)

        self._row_count_label = QLabel("")
        self._row_count_label.setObjectName("row_count_label")
        tb_lay.addWidget(self._row_count_label)

        card_lay.addWidget(toolbar)

        # ── QTableWidget ──────────────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        card_lay.addWidget(self._table)

        self.body_layout.addWidget(card)

    # ── Role-based button visibility ──────────────────────────────────────────

    def _apply_role_permissions(self):
        can_write = self._role in ("admin", "staff")
        self._add_button.setVisible(can_write)
        self._edit_button.setVisible(can_write)
        self._delete_button.setVisible(can_write)

    # ── Data loading ──────────────────────────────────────────────────────────

    def load_data(self):
        self._all_rows = read_csv(self._csv_path)
        if self._all_rows:
            self._headers = [h for h in self._all_rows[0].keys() if h is not None]
        else:
            self._headers = list(self.DEFAULT_HEADERS)
        self._apply_filter(self._search_box.text() if self._search_box else "")

    def _apply_filter(self, text: str):
        is_viewer = self._role == "viewer"
        sensitive = set(self.SENSITIVE_COLUMNS)
        term      = text.strip().lower()

        if term:
            filtered = [
                row for row in self._all_rows
                if any(
                    term in str(v).lower()
                    for k, v in row.items()
                    if not (is_viewer and k in sensitive)
                )
            ]
        else:
            filtered = self._all_rows

        self._table.setSortingEnabled(False)
        self._table.setColumnCount(len(self._headers))
        self._table.setRowCount(len(filtered))
        self._table.setHorizontalHeaderLabels(
            [h.replace("_", " ").title() for h in self._headers]
        )

        for row_idx, row in enumerate(filtered):
            # Alternate row tint — even rows stay white, odd rows get #f5f6fa.
            row_bg = QColor("#ffffff") if row_idx % 2 == 0 else QColor("#f5f6fa")

            for col_idx, header in enumerate(self._headers):
                if is_viewer and header in sensitive:
                    display = "••••••"
                else:
                    display = row.get(header, "")

                item = QTableWidgetItem(display)
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                item.setBackground(row_bg)

                if is_viewer and header in sensitive:
                    item.setForeground(QColor("#b0bdd8"))
                    item.setFont(QFont("Segoe UI", 9))

                self._table.setItem(row_idx, col_idx, item)

        self._table.resizeColumnsToContents()
        self._table.resizeRowsToContents()
        self._table.setSortingEnabled(True)

        total = len(self._all_rows)
        shown = len(filtered)
        if self._row_count_label:
            label = (f"{shown} of {total} records" if term
                     else f"{total} record{'s' if total != 1 else ''}")
            if is_viewer and sensitive:
                label += "  🔒"
            self._row_count_label.setText(label)

    def selected_row_data(self):
        row_idx = self._table.currentRow()
        if row_idx < 0:
            return None
        return {
            self._headers[c]: self._table.item(row_idx, c).text()
            for c in range(self._table.columnCount())
        }

    # ── Overridable actions ───────────────────────────────────────────────────

    def on_add(self):
        """Override in subclass to implement Add."""
        _mb_info(self, "Not Implemented",
                 "Add is not implemented for this module yet.")

    def on_edit(self):
        """Override in subclass to implement Edit."""
        if self.selected_row_data() is None:
            _mb_no_selection(self, "Edit")
            return
        _mb_info(self, "Not Implemented",
                 "Edit is not implemented for this module yet.")

    def on_delete(self):
        """Override in subclass to implement Delete."""
        if self.selected_row_data() is None:
            _mb_no_selection(self, "Delete")
            return
        _mb_info(self, "Not Implemented",
                 "Delete is not implemented for this module yet.")

    def on_print(self):
        import tempfile
        import webbrowser
        import html as html_mod

        rows = self._all_rows
        if not rows:
            _mb_info(self, "Print", "No data to print.")
            return

        is_viewer = self._role == "viewer"
        sensitive = set(self.SENSITIVE_COLUMNS)
        headers   = self._headers
        title     = self._title

        th = "".join(
            f"<th>{html_mod.escape(h.replace('_', ' ').title())}</th>"
            for h in headers
        )
        trs = ""
        for r_idx, row in enumerate(rows):
            row_style = "" if r_idx % 2 == 0 else 'style="background:#f5f6fa"'
            tds = ""
            for h in headers:
                if is_viewer and h in sensitive:
                    tds += '<td style="color:#9ca3af">••••••</td>'
                else:
                    tds += f"<td>{html_mod.escape(row.get(h, ''))}</td>"
            trs += f"<tr {row_style}>{tds}</tr>\n"

        html_content = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>{html_mod.escape(title)}</title>
<style>
  body   {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px;
            margin: 28px; color: #1a1a2e; }}
  h2     {{ color: #0d2260; margin-bottom: 2px; font-size: 18px; }}
  .meta  {{ color: #5a6480; font-size: 11px; margin-bottom: 16px; }}
  table  {{ border-collapse: collapse; width: 100%; }}
  th     {{ background: #1a3a8a; color: #fff; padding: 9px 12px;
            text-align: left; font-size: 11px; text-transform: uppercase;
            letter-spacing: 0.4px; }}
  td     {{ border: 1px solid #d0d8ef; padding: 7px 12px; }}
  tr:nth-child(even) {{ background: #f5f6fa; }}
  tr:hover {{ background: #fff8e1; }}
</style></head>
<body>
<h2>Campus Clinic — {html_mod.escape(title)}</h2>
<p class="meta">
  Printed: {_dt.now().strftime('%Y-%m-%d %H:%M')}
  &nbsp;|&nbsp; {len(rows)} record{'s' if len(rows) != 1 else ''}
</p>
<table>
  <thead><tr>{th}</tr></thead>
  <tbody>{trs}</tbody>
</table>
</body></html>"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html_content)
            tmp_path = f.name
        webbrowser.open(f"file://{tmp_path}")


# =============================================================================