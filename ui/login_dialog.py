"""Login dialog — shown on application startup."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QWidget, QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette, QColor

from database.db import get_session, authenticate_user
from database.models import AppUser, RegistryType

# Completely isolated stylesheet — overrides everything
_LOGIN_STYLE = """
* {
    font-family: "Segoe UI", Arial, sans-serif;
}
QDialog {
    background-color: #f0f4f8;
}
QWidget#header {
    background-color: #1a365d;
}
QWidget#formArea {
    background-color: #f0f4f8;
}
QLabel#title {
    color: white;
    font-size: 20px;
    font-weight: bold;
    background: transparent;
}
QLabel#subtitle {
    color: #bee3f8;
    font-size: 11px;
    background: transparent;
}
QLabel#fieldLabel {
    color: #2d3748;
    font-size: 12px;
    font-weight: bold;
    background: transparent;
}
QLabel#errorLabel {
    color: #c53030;
    font-size: 11px;
    background: transparent;
}
QLabel#hintLabel {
    color: #a0aec0;
    font-size: 10px;
    background: transparent;
}
QLineEdit#loginInput {
    background-color: white;
    color: #1a202c;
    border: 1.5px solid #cbd5e0;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #bee3f8;
}
QLineEdit#loginInput:focus {
    border: 2px solid #2b6cb0;
    background-color: white;
}
QComboBox#loginInput {
    background-color: white;
    color: #1a202c;
    border: 1.5px solid #cbd5e0;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}
QComboBox#loginInput:focus {
    border: 2px solid #2b6cb0;
}
QPushButton#loginBtn {
    background-color: #2b6cb0;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
    padding: 11px 0;
}
QPushButton#loginBtn:hover {
    background-color: #3182ce;
}
QPushButton#loginBtn:pressed {
    background-color: #2c5282;
}
"""


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user: AppUser | None = None
        self.selected_registry_type: RegistryType = RegistryType.GENERAL
        self.setWindowTitle("Σύνδεση")
        self.setFixedSize(400, 420)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        self.setStyleSheet(_LOGIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(105)
        hv = QVBoxLayout(header)
        hv.setContentsMargins(20, 18, 20, 18)
        hv.setSpacing(6)
        hv.setAlignment(Qt.AlignmentFlag.AlignCenter)

        t = QLabel("Σύστημα Πρωτοκόλλου")
        t.setObjectName("title")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)

        s = QLabel("Παρακαλώ εισάγετε τα στοιχεία σας")
        s.setObjectName("subtitle")
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hv.addWidget(t)
        hv.addWidget(s)
        root.addWidget(header)

        # ── Form area ─────────────────────────────────────────────────────────
        form = QWidget()
        form.setObjectName("formArea")
        fv = QVBoxLayout(form)
        fv.setContentsMargins(40, 28, 40, 20)
        fv.setSpacing(6)

        lbl_u = QLabel("Όνομα Χρήστη")
        lbl_u.setObjectName("fieldLabel")
        self._ed_user = QLineEdit()
        self._ed_user.setObjectName("loginInput")
        self._ed_user.setFixedHeight(40)
        self._ed_user.setPlaceholderText("Εισάγετε όνομα χρήστη")

        lbl_p = QLabel("Κωδικός Πρόσβασης")
        lbl_p.setObjectName("fieldLabel")
        lbl_p.setContentsMargins(0, 10, 0, 0)
        self._ed_pass = QLineEdit()
        self._ed_pass.setObjectName("loginInput")
        self._ed_pass.setFixedHeight(40)
        self._ed_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._ed_pass.setPlaceholderText("Εισάγετε κωδικό")
        self._ed_pass.returnPressed.connect(self._login)

        lbl_r = QLabel("Βιβλίο Πρωτοκόλλου")
        lbl_r.setObjectName("fieldLabel")
        lbl_r.setContentsMargins(0, 10, 0, 0)
        self._cb_registry = QComboBox()
        self._cb_registry.setObjectName("loginInput")
        self._cb_registry.setFixedHeight(40)
        self._cb_registry.addItem("Γενικό Πρωτόκολλο", RegistryType.GENERAL)
        self._cb_registry.addItem("Αιτήσεις Καταναλωτών", RegistryType.CONSUMER)
        self._cb_registry.addItem("Οικονομική Υπηρεσία", RegistryType.FINANCIAL)

        self._lbl_error = QLabel("")
        self._lbl_error.setObjectName("errorLabel")
        self._lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_error.setFixedHeight(20)

        btn = QPushButton("Σύνδεση")
        btn.setObjectName("loginBtn")
        btn.setFixedHeight(44)
        btn.clicked.connect(self._login)

        fv.addWidget(lbl_u)
        fv.addWidget(self._ed_user)
        fv.addWidget(lbl_p)
        fv.addWidget(self._ed_pass)
        fv.addWidget(lbl_r)
        fv.addWidget(self._cb_registry)
        fv.addSpacing(4)
        fv.addWidget(self._lbl_error)
        fv.addWidget(btn)

        root.addWidget(form, 1)

        # ── Footer ────────────────────────────────────────────────────────────
        footer = QWidget()
        footer.setObjectName("formArea")
        fl = QVBoxLayout(footer)
        fl.setContentsMargins(0, 0, 0, 8)
        # (no hint shown for security)
        root.addWidget(footer)

        self._ed_user.setFocus()

    def _login(self):
        username = self._ed_user.text().strip()
        password = self._ed_pass.text()

        if not username or not password:
            self._lbl_error.setText("Συμπληρώστε όνομα χρήστη και κωδικό.")
            return

        try:
            s = get_session()
            user = authenticate_user(s, username, password)
            if user:
                # Load all attributes while session is open
                _ = (user.id, user.username, user.full_name,
                     user.role, user.email, user.active)
                self.current_user = user
                self.selected_registry_type = self._cb_registry.currentData()
                s.close()
                self.accept()
            else:
                s.close()
                self._lbl_error.setText("Λάθος όνομα χρήστη ή κωδικός.")
                self._ed_pass.clear()
                self._ed_pass.setFocus()
        except Exception as ex:
            self._lbl_error.setText(f"Σφάλμα: {ex}")
