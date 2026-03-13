"""Login dialog — shown on application startup."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QMessageBox, QWidget,
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
        self.setFixedSize(380, 280)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background:#1a365d; padding:20px;")
        hv = QVBoxLayout(header)
        title = QLabel("Σύστημα Πρωτοκόλλου")
        title.setStyleSheet("color:white; font-size:18px; font-weight:bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("Παρακαλώ εισάγετε τα στοιχεία σας")
        sub.setStyleSheet("color:#bee3f8; font-size:11px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hv.addWidget(title)
        hv.addWidget(sub)
        layout.addWidget(header)

        # Form
        form_widget = QWidget()
        form_widget.setStyleSheet("background:#f7fafc; padding:10px;")
        fv = QVBoxLayout(form_widget)
        fv.setContentsMargins(30, 20, 30, 10)
        fv.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._ed_user = QLineEdit()
        self._ed_user.setPlaceholderText("Όνομα χρήστη")
        self._ed_user.setMinimumHeight(36)
        form.addRow("Χρήστης:", self._ed_user)

        self._ed_pass = QLineEdit()
        self._ed_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._ed_pass.setPlaceholderText("Κωδικός")
        self._ed_pass.setMinimumHeight(36)
        self._ed_pass.returnPressed.connect(self._login)
        form.addRow("Κωδικός:", self._ed_pass)
        fv.addLayout(form)

        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet("color:#e53e3e; font-size:11px;")
        self._lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fv.addWidget(self._lbl_error)

        btn = QPushButton("Σύνδεση")
        btn.setMinimumHeight(40)
        btn.setStyleSheet(
            "QPushButton{background:#2b6cb0;color:white;border-radius:5px;"
            "font-size:14px;font-weight:bold;}"
            "QPushButton:hover{background:#3182ce;}"
        )
        btn.clicked.connect(self._login)
        fv.addWidget(btn)

        layout.addWidget(form_widget, 1)

        # Default hint
        hint = QLabel("Προεπιλογή: admin / admin123")
        hint.setStyleSheet("color:#a0aec0; font-size:10px; padding:6px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        # Pre-fill admin for first run
        self._ed_user.setText("admin")
        self._ed_pass.setFocus()

    def _login(self):
        username = self._ed_user.text().strip()
        password = self._ed_pass.text()
        if not username or not password:
            self._lbl_error.setText("Συμπληρώστε όνομα χρήστη και κωδικό.")
            return
        s = get_session()
        user = authenticate_user(s, username, password)
        s.close()
        if user:
            self.current_user = user
            self.accept()
        else:
            self._lbl_error.setText("Λάθος όνομα χρήστη ή κωδικός.")
            self._ed_pass.clear()
            self._ed_pass.setFocus()
