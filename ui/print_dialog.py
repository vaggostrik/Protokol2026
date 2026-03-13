"""Print Protocol Book dialog."""
from __future__ import annotations
from datetime import date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QPushButton, QDialogButtonBox, QLabel, QGroupBox, QHBoxLayout,
    QCheckBox, QMessageBox,
)
from PyQt6.QtCore import Qt


class PrintBookDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Εκτύπωση Βιβλίου Πρωτοκόλλου")
        self.setMinimumWidth(400)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        form.setSpacing(10)

        self._cb_year = QComboBox()
        self._cb_year.addItem("Όλα τα έτη", None)
        current = date.today().year
        for y in range(current, current - 10, -1):
            self._cb_year.addItem(str(y), y)
        self._cb_year.setCurrentIndex(1)  # default current year
        form.addRow("Έτος:", self._cb_year)

        self._cb_direction = QComboBox()
        self._cb_direction.addItem("Όλα", None)
        self._cb_direction.addItem("Εισερχόμενα", "ΕΙΣΕΡΧΟΜΕΝΟ")
        self._cb_direction.addItem("Εξερχόμενα", "ΕΞΕΡΧΟΜΕΝΟ")
        self._cb_direction.addItem("Εσωτερικά", "ΕΣΩΤΕΡΙΚΟ")
        form.addRow("Κατεύθυνση:", self._cb_direction)

        self._cb_paper = QComboBox()
        for p in ["A4", "A3", "A5", "Letter"]:
            self._cb_paper.addItem(p)
        form.addRow("Μέγεθος χαρτιού:", self._cb_paper)

        self._cb_orientation = QComboBox()
        self._cb_orientation.addItem("Οριζόντιο (Landscape)", "landscape")
        self._cb_orientation.addItem("Κατακόρυφο (Portrait)", "portrait")
        form.addRow("Προσανατολισμός:", self._cb_orientation)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_print = QPushButton("Εκτύπωση / Αποθήκευση PDF")
        btn_print.setStyleSheet(
            "background:#2b6cb0;color:white;padding:9px 20px;border-radius:5px;font-weight:bold;"
        )
        btn_print.clicked.connect(self._print)
        btn_cancel = QPushButton("Ακύρωση")
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_print)
        layout.addLayout(btns)

    def _print(self):
        from database.db import get_session, search_protocols
        from reports.protocol_book import print_protocol_book
        from config.settings import load_config

        s = get_session()
        year = self._cb_year.currentData()
        direction = self._cb_direction.currentData()
        paper = self._cb_paper.currentText()
        orientation = self._cb_orientation.currentData()

        protocols, total = search_protocols(s, year=year, direction=direction, limit=10000)
        if total == 0:
            QMessageBox.information(self, "Πληροφορία", "Δεν βρέθηκαν εγγραφές με τα επιλεγμένα κριτήρια.")
            return

        config = load_config()
        path = print_protocol_book(protocols, config, paper, orientation, year, direction)
        if path:
            QMessageBox.information(self, "Επιτυχία", f"Το βιβλίο πρωτοκόλλου αποθηκεύτηκε:\n{path}")
            self.accept()
