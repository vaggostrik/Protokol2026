"""User management panel (admin only)."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialog, QDialogButtonBox,
    QMessageBox, QCheckBox,
)
from PyQt6.QtCore import Qt
from database.db import get_session
from database.models import AppUser, UserRole
from ui.widgets import SectionHeader, ConfirmDialog


class UserManagementPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._session = get_session()
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(SectionHeader("Διαχείριση Χρηστών"))

        btn_row = QHBoxLayout()
        btn_add = QPushButton("Νέος Χρήστης")
        btn_add.clicked.connect(self._add_user)
        btn_edit = QPushButton("Επεξεργασία")
        btn_edit.clicked.connect(self._edit_user)
        btn_del = QPushButton("Απενεργοποίηση")
        btn_del.setProperty("danger", "true")
        btn_del.clicked.connect(self._deactivate_user)
        btn_pwd = QPushButton("Αλλαγή Κωδικού")
        btn_pwd.clicked.connect(self._change_password)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_pwd)
        btn_row.addStretch()
        btn_row.addWidget(btn_del)
        layout.addLayout(btn_row)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["Όνομα Χρήστη", "Ονοματεπώνυμο", "Ρόλος", "Email", "Ενεργός"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, 1)

    def _load(self):
        self._table.setRowCount(0)
        users = self._session.query(AppUser).order_by(AppUser.username).all()
        for u in users:
            r = self._table.rowCount()
            self._table.insertRow(r)
            self._table.setItem(r, 0, QTableWidgetItem(u.username))
            self._table.setItem(r, 1, QTableWidgetItem(u.full_name))
            self._table.setItem(r, 2, QTableWidgetItem(u.role.value if u.role else ""))
            self._table.setItem(r, 3, QTableWidgetItem(u.email or ""))
            active_item = QTableWidgetItem("Ναι" if u.active else "Όχι")
            if not u.active:
                active_item.setForeground(Qt.GlobalColor.red)
            self._table.setItem(r, 4, active_item)

    def _selected_username(self):
        row = self._table.currentRow()
        if row < 0:
            return None
        return self._table.item(row, 0).text()

    def _get_user(self):
        name = self._selected_username()
        if not name:
            return None
        return self._session.query(AppUser).filter_by(username=name).first()

    def _add_user(self):
        dlg = UserDialog(self._session, parent=self)
        if dlg.exec():
            self._load()

    def _edit_user(self):
        u = self._get_user()
        if not u:
            return
        dlg = UserDialog(self._session, user_id=u.id, parent=self)
        if dlg.exec():
            self._load()

    def _deactivate_user(self):
        u = self._get_user()
        if not u:
            return
        if u.username == "admin":
            QMessageBox.warning(self, "Απαγορεύεται", "Ο χρήστης admin δεν μπορεί να απενεργοποιηθεί.")
            return
        if ConfirmDialog.ask(self, "Απενεργοποίηση", f"Να απενεργοποιηθεί ο χρήστης '{u.username}';"):
            u.active = False
            self._session.commit()
            self._load()

    def _change_password(self):
        u = self._get_user()
        if not u:
            return
        dlg = ChangePasswordDialog(self._session, u, parent=self)
        dlg.exec()


class UserDialog(QDialog):
    def __init__(self, session, user_id=None, parent=None):
        super().__init__(parent)
        self._session = session
        self._user_id = user_id
        self.setWindowTitle("Στοιχεία Χρήστη")
        self.setMinimumWidth(400)
        self._build_ui()
        if user_id:
            self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self._ed_username = QLineEdit()
        form.addRow("Όνομα Χρήστη *:", self._ed_username)

        self._ed_fullname = QLineEdit()
        form.addRow("Ονοματεπώνυμο *:", self._ed_fullname)

        self._cb_role = QComboBox()
        for r in UserRole:
            self._cb_role.addItem(r.value, r)
        form.addRow("Ρόλος:", self._cb_role)

        self._ed_email = QLineEdit()
        form.addRow("Email:", self._ed_email)

        self._ed_password = QLineEdit()
        self._ed_password.setEchoMode(QLineEdit.EchoMode.Password)
        self._ed_password.setPlaceholderText("Αφήστε κενό για να μην αλλάξει" if self._user_id else "Υποχρεωτικό")
        form.addRow("Κωδικός:", self._ed_password)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("Αποθήκευση")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Ακύρωση")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load(self):
        u = self._session.get(AppUser, self._user_id)
        if not u:
            return
        self._ed_username.setText(u.username)
        self._ed_fullname.setText(u.full_name)
        self._ed_email.setText(u.email or "")
        for i in range(self._cb_role.count()):
            if self._cb_role.itemData(i) == u.role:
                self._cb_role.setCurrentIndex(i)
                break

    def _save(self):
        username = self._ed_username.text().strip()
        fullname = self._ed_fullname.text().strip()
        if not username or not fullname:
            QMessageBox.warning(self, "Σφάλμα", "Όνομα χρήστη και ονοματεπώνυμο είναι υποχρεωτικά.")
            return
        password = self._ed_password.text()
        if not self._user_id and not password:
            QMessageBox.warning(self, "Σφάλμα", "Ο κωδικός είναι υποχρεωτικός για νέο χρήστη.")
            return
        if self._user_id:
            u = self._session.get(AppUser, self._user_id)
        else:
            u = AppUser()
            self._session.add(u)
        u.username = username
        u.full_name = fullname
        u.role = self._cb_role.currentData()
        u.email = self._ed_email.text().strip() or None
        if password:
            u.set_password(password)
        try:
            self._session.commit()
            self.accept()
        except Exception as ex:
            self._session.rollback()
            QMessageBox.critical(self, "Σφάλμα", str(ex))


class ChangePasswordDialog(QDialog):
    def __init__(self, session, user: AppUser, parent=None):
        super().__init__(parent)
        self._session = session
        self._user = user
        self.setWindowTitle(f"Αλλαγή Κωδικού - {user.username}")
        self.setMinimumWidth(350)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)
        self._ed_new = QLineEdit()
        self._ed_new.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Νέος Κωδικός *:", self._ed_new)
        self._ed_confirm = QLineEdit()
        self._ed_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Επιβεβαίωση *:", self._ed_confirm)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("Αλλαγή")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Ακύρωση")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _save(self):
        new_pwd = self._ed_new.text()
        confirm = self._ed_confirm.text()
        if not new_pwd:
            QMessageBox.warning(self, "Σφάλμα", "Εισάγετε νέο κωδικό.")
            return
        if new_pwd != confirm:
            QMessageBox.warning(self, "Σφάλμα", "Οι κωδικοί δεν ταιριάζουν.")
            return
        self._user.set_password(new_pwd)
        self._session.commit()
        QMessageBox.information(self, "Επιτυχία", "Ο κωδικός άλλαξε.")
        self.accept()
