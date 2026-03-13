"""Reusable custom widgets."""
from __future__ import annotations
from typing import Optional, List, Tuple
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QDateEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame, QSizePolicy, QDialog,
    QDialogButtonBox, QListWidget, QListWidgetItem, QSplitter,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont, QIcon

from ui.styles import INCOMING_COLOR, OUTGOING_COLOR, INTERNAL_COLOR, STATUS_COLORS, PRIORITY_COLORS


class SectionHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("heading", "true")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.setFont(font)
        self.setStyleSheet(f"color: #1a365d; padding: 4px 0 8px 0;")


class StatusBadge(QLabel):
    def __init__(self, text: str, color: str = "#2b6cb0", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"background-color: {color}; color: white; border-radius: 10px; "
            f"padding: 2px 10px; font-size: 11px; font-weight: bold;"
        )
        self.setMaximumHeight(22)


class DirectionBadge(StatusBadge):
    COLORS = {
        "ΕΙΣΕΡΧΟΜΕΝΟ": INCOMING_COLOR,
        "ΕΞΕΡΧΟΜΕΝΟ": OUTGOING_COLOR,
        "ΕΣΩΤΕΡΙΚΟ": INTERNAL_COLOR,
    }

    def __init__(self, direction: str, parent=None):
        color = self.COLORS.get(direction, "#4a5568")
        super().__init__(direction, color, parent)


class FormRow(QWidget):
    """A label + widget row for forms."""
    def __init__(self, label: str, widget: QWidget, required: bool = False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        lbl_text = f"<b>{label}</b>" if required else label
        if required:
            lbl_text += ' <span style="color:red">*</span>'
        lbl = QLabel(lbl_text)
        lbl.setMinimumWidth(160)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl)
        layout.addWidget(widget, 1)


class SearchBar(QWidget):
    searched = pyqtSignal(str)

    def __init__(self, placeholder: str = "Αναζήτηση...", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.returnPressed.connect(self._emit)
        btn = QPushButton("Αναζήτηση")
        btn.clicked.connect(self._emit)
        layout.addWidget(self.edit, 1)
        layout.addWidget(btn)

    def _emit(self):
        self.searched.emit(self.edit.text())

    def text(self):
        return self.edit.text()


class ProtocolTable(QTableWidget):
    """Reusable table for displaying protocol lists."""
    COLUMNS: List[Tuple[str, int]] = [
        ("Αρ. Πρωτ.", 100),
        ("Ημερομηνία", 100),
        ("Κατεύθυνση", 110),
        ("Αποστολέας/Προς", 200),
        ("Θέμα", 300),
        ("Κατάσταση", 120),
        ("Προτεραιότητα", 110),
    ]

    row_double_clicked = pyqtSignal(int)  # protocol id

    def __init__(self, parent=None):
        super().__init__(0, len(self.COLUMNS), parent)
        headers = [c[0] for c in self.COLUMNS]
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for i, (_, w) in enumerate(self.COLUMNS):
            self.setColumnWidth(i, w)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)
        self._id_map: dict[int, int] = {}  # row -> protocol_id
        self.doubleClicked.connect(self._on_double_click)

    def _on_double_click(self, index):
        row = index.row()
        pid = self._id_map.get(row)
        if pid:
            self.row_double_clicked.emit(pid)

    def populate(self, protocols):
        self.setRowCount(0)
        self._id_map.clear()
        for row, p in enumerate(protocols):
            self.insertRow(row)
            self._id_map[row] = p.id

            items = [
                p.protocol_full or "",
                p.protocol_date.strftime("%d/%m/%Y") if p.protocol_date else "",
                p.direction.value if p.direction else "",
                self._sender_name(p),
                p.subject or "",
                p.status.value if p.status else "",
                p.priority.value if p.priority else "",
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if col == 2:  # direction
                    color_map = {
                        "ΕΙΣΕΡΧΟΜΕΝΟ": QColor("#e6fffa"),
                        "ΕΞΕΡΧΟΜΕΝΟ": QColor("#ebf8ff"),
                        "ΕΣΩΤΕΡΙΚΟ": QColor("#fffff0"),
                    }
                    item.setBackground(color_map.get(text, QColor("white")))
                if col == 5:  # status
                    fc = STATUS_COLORS.get(text, "#4a5568")
                    item.setForeground(QColor(fc))
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                if col == 6:  # priority
                    fc = PRIORITY_COLORS.get(text, "#4a5568")
                    item.setForeground(QColor(fc))
                self.setItem(row, col, item)

    @staticmethod
    def _sender_name(p) -> str:
        if p.sender_contact:
            return p.sender_contact.name
        if p.sender_employee:
            return p.sender_employee.full_name
        return ""

    def selected_protocol_id(self) -> Optional[int]:
        rows = self.selectedItems()
        if not rows:
            return None
        return self._id_map.get(self.currentRow())


class ConfirmDialog(QMessageBox):
    @staticmethod
    def ask(parent, title: str, message: str) -> bool:
        dlg = QMessageBox(parent)
        dlg.setWindowTitle(title)
        dlg.setText(message)
        dlg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        dlg.setDefaultButton(QMessageBox.StandardButton.No)
        dlg.button(QMessageBox.StandardButton.Yes).setText("Ναι")
        dlg.button(QMessageBox.StandardButton.No).setText("Όχι")
        return dlg.exec() == QMessageBox.StandardButton.Yes
