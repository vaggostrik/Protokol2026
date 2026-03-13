"""Login dialog — shown on application startup."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database.db import get_session, authenticate_user
from database.models import AppUser


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user: AppUser | None = None
        self.setWindowTitle("Σύνδεση")
        self.setFixedSize(400, 320)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        self.setStyleSheet("""
            QDialog { background: #f0f4f8; }
            QLabel { color: #2d3748; font-size: 13px; }
            QLineEdit {
                background: white;
                border: 1px solid #cbd5e0;
                border-radius: 5px;
                padding: 8px 10px;
                font-size: 13px;
                color: #2d3748;
            }
            QLineEdit:focus { border: 2px solid #3182ce; }
            QPushButton {
                background: #2b6cb0;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover { background: #3182ce; }
            QPushButton:pressed { background: #2c5282; }
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(100)
        header.setStyleSheet("background: #1a365d;")
        hv = QVBoxLayout(header)
        hv.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Σύστημα Πρωτοκόλλου")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")

        sub = QLabel("Παρακαλώ εισάγετε τα στοιχεία σας")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #bee3f8; font-size: 11px; margin-top: 4px;")

        hv.addWidget(title)
        hv.addWidget(sub)
        layout.addWidget(header)

        # ── Form ──────────────────────────────────────────────────────────────
        form = QWidget()
        form.setStyleSheet("background: #f0f4f8;")
        fv = QVBoxLayout(form)
        fv.setContentsMargins(40, 24, 40, 16)
        fv.setSpacing(14)

        # Username
        lbl_user = QLabel("Όνομα Χρήστη:")
        lbl_user.setStyleSheet("color: #2d3748; font-size: 12px; font-weight: bold; margin-bottom: 2px;")
        self._ed_user = QLineEdit()
        self._ed_user.setPlaceholderText("Εισάγετε όνομα χρήστη")
        self._ed_user.setMinimumHeight(38)
        self._ed_user.setText("admin")

        # Password
        lbl_pass = QLabel("Κωδικός Πρόσβασης:")
        lbl_pass.setStyleSheet("color: #2d3748; font-size: 12px; font-weight: bold; margin-bottom: 2px;")
        self._ed_pass = QLineEdit()
        self._ed_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._ed_pass.setPlaceholderText("Εισάγετε κωδικό")
        self._ed_pass.setMinimumHeight(38)
        self._ed_pass.returnPressed.connect(self._login)

        fv.addWidget(lbl_user)
        fv.addWidget(self._ed_user)
        fv.addWidget(lbl_pass)
        fv.addWidget(self._ed_pass)

        # Error label
        self._lbl_error = QLabel("")
        self._lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_error.setStyleSheet("color: #e53e3e; font-size: 11px; min-height: 16px;")
        fv.addWidget(self._lbl_error)

        # Login button
        btn = QPushButton("Σύνδεση")
        btn.setMinimumHeight(42)
        btn.clicked.connect(self._login)
        fv.addWidget(btn)

        layout.addWidget(form, 1)

        # ── Footer ────────────────────────────────────────────────────────────
        hint = QLabel("Προεπιλογή: admin / admin123")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #a0aec0; font-size: 10px; padding: 8px;")
        layout.addWidget(hint)

        self._ed_pass.setFocus()

    def _login(self):
        username = self._ed_user.text().strip()
        password = self._ed_pass.text()
        if not username or not password:
            self._lbl_error.setText("Συμπληρώστε όνομα χρήστη και κωδικό.")
            return

        s = get_session()
        user = authenticate_user(s, username, password)
        if user:
            # Access all attributes while session is open to avoid DetachedInstanceError
            _ = user.username, user.full_name, user.role, user.email, user.active, user.id
            self.current_user = user
            s.close()
            self.accept()
        else:
            s.close()
            self._lbl_error.setText("Λάθος όνομα χρήστη ή κωδικός.")
            self._ed_pass.clear()
            self._ed_pass.setFocus()
