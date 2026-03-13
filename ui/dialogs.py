"""Various helper dialogs."""
from __future__ import annotations
from typing import List, Tuple, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox,
    QListWidget, QListWidgetItem, QDialogButtonBox, QMessageBox,
    QCheckBox, QWidget,
)
from PyQt6.QtCore import Qt

from database.models import Contact, RecipientList, Protocol, ProtocolHistory, Employee
from sqlalchemy.orm import Session


class ContactDialog(QDialog):
    """Create or edit a Contact."""
    def __init__(self, session: Session, contact_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self._session = session
        self.contact: Optional[Contact] = None
        self.setWindowTitle("Διαχείριση Επαφής")
        self.setMinimumWidth(500)
        self._build_ui()
        if contact_id:
            self._load(contact_id)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(8)

        self._ed_name = QLineEdit()
        self._ed_name.setPlaceholderText("Ονοματεπώνυμο / Επωνυμία")
        form.addRow("Όνομα *:", self._ed_name)

        self._ed_org = QLineEdit()
        self._ed_org.setPlaceholderText("Οργανισμός / Υπηρεσία")
        form.addRow("Οργανισμός:", self._ed_org)

        self._cb_type = QComboBox()
        for t in ["Φυσικό Πρόσωπο", "Νομικό Πρόσωπο", "Δημόσια Αρχή", "ΟΤΑ", "ΝΠΔΔ", "Άλλο"]:
            self._cb_type.addItem(t)
        form.addRow("Τύπος:", self._cb_type)

        self._ed_address = QLineEdit()
        form.addRow("Διεύθυνση:", self._ed_address)

        addr_row = QWidget()
        ar = QHBoxLayout(addr_row)
        ar.setContentsMargins(0, 0, 0, 0)
        self._ed_city = QLineEdit()
        self._ed_city.setPlaceholderText("Πόλη")
        self._ed_postal = QLineEdit()
        self._ed_postal.setPlaceholderText("ΤΚ")
        self._ed_postal.setMaximumWidth(80)
        ar.addWidget(self._ed_city, 1)
        ar.addWidget(QLabel("ΤΚ:"))
        ar.addWidget(self._ed_postal)
        form.addRow("Πόλη / ΤΚ:", addr_row)

        self._ed_phone = QLineEdit()
        form.addRow("Τηλέφωνο:", self._ed_phone)

        self._ed_fax = QLineEdit()
        form.addRow("Fax:", self._ed_fax)

        self._ed_email = QLineEdit()
        form.addRow("Email:", self._ed_email)

        self._ed_notes = QTextEdit()
        self._ed_notes.setMaximumHeight(80)
        form.addRow("Σημειώσεις:", self._ed_notes)

        layout.addLayout(form)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Save).setText("Αποθήκευση")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Ακύρωση")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load(self, contact_id: int):
        c = self._session.get(Contact, contact_id)
        if not c:
            return
        self._ed_name.setText(c.name or "")
        self._ed_org.setText(c.organization or "")
        self._ed_address.setText(c.address or "")
        self._ed_city.setText(c.city or "")
        self._ed_postal.setText(c.postal_code or "")
        self._ed_phone.setText(c.phone or "")
        self._ed_fax.setText(c.fax or "")
        self._ed_email.setText(c.email or "")
        self._ed_notes.setPlainText(c.notes or "")
        idx = self._cb_type.findText(c.contact_type or "")
        if idx >= 0:
            self._cb_type.setCurrentIndex(idx)

    def _save(self):
        name = self._ed_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Σφάλμα", "Το όνομα είναι υποχρεωτικό.")
            return
        if self.contact is None:
            self.contact = Contact()
            self._session.add(self.contact)
        c = self.contact
        c.name = name
        c.organization = self._ed_org.text().strip() or None
        c.contact_type = self._cb_type.currentText()
        c.address = self._ed_address.text().strip() or None
        c.city = self._ed_city.text().strip() or None
        c.postal_code = self._ed_postal.text().strip() or None
        c.phone = self._ed_phone.text().strip() or None
        c.fax = self._ed_fax.text().strip() or None
        c.email = self._ed_email.text().strip() or None
        c.notes = self._ed_notes.toPlainText().strip() or None
        try:
            self._session.commit()
            self.accept()
        except Exception as ex:
            self._session.rollback()
            QMessageBox.critical(self, "Σφάλμα", str(ex))


class RecipientListDialog(QDialog):
    """Pick a recipient list and return its members."""
    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self._session = session
        self._selected: List[Tuple[str, int]] = []
        self.setWindowTitle("Πίνακες Αποδεκτών")
        self.setMinimumSize(400, 400)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self._list_lists = QListWidget()
        lists = self._session.query(RecipientList).filter_by(active=True).order_by(RecipientList.name).all()
        for rl in lists:
            item = QListWidgetItem(f"{rl.name} ({len(rl.members)} μέλη)")
            item.setData(Qt.ItemDataRole.UserRole, rl.id)
            self._list_lists.addItem(item)
        self._list_lists.currentItemChanged.connect(self._on_list_selected)
        layout.addWidget(QLabel("Επιλέξτε πίνακα:"))
        layout.addWidget(self._list_lists)

        self._list_members = QListWidget()
        layout.addWidget(QLabel("Μέλη:"))
        layout.addWidget(self._list_members)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("Προσθήκη")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Ακύρωση")
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _on_list_selected(self, item):
        if not item:
            return
        rl_id = item.data(Qt.ItemDataRole.UserRole)
        rl = self._session.get(RecipientList, rl_id)
        self._list_members.clear()
        if rl:
            for m in rl.members:
                self._list_members.addItem(m.display_name)

    def _on_ok(self):
        item = self._list_lists.currentItem()
        if not item:
            self.reject()
            return
        rl_id = item.data(Qt.ItemDataRole.UserRole)
        rl = self._session.get(RecipientList, rl_id)
        if rl:
            self._selected = [(m.display_name, m.id) for m in rl.members]
        self.accept()

    def selected(self) -> List[Tuple[str, int]]:
        return self._selected


class HistoryStageDialog(QDialog):
    """Add a processing stage to a protocol."""
    def __init__(self, session: Session, protocol: Protocol, parent=None):
        super().__init__(parent)
        self._session = session
        self._protocol = protocol
        self.setWindowTitle("Καταχώρηση Σταδίου Διεκπεραίωσης")
        self.setMinimumWidth(450)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(8)

        self._cb_action = QComboBox()
        self._cb_action.setEditable(True)
        for a in ["Παραλαβή", "Διαβίβαση", "Ενέργεια", "Απάντηση", "Αρχειοθέτηση",
                  "Διεκπεραίωση", "Ακύρωση", "Επιστροφή", "Άλλο"]:
            self._cb_action.addItem(a)
        form.addRow("Ενέργεια *:", self._cb_action)

        self._cb_new_status = QComboBox()
        from database.models import ProcessingStatus
        for s in ProcessingStatus:
            self._cb_new_status.addItem(s.value, s)
        form.addRow("Νέα Κατάσταση:", self._cb_new_status)

        self._cb_employee = QComboBox()
        self._cb_employee.addItem("-- Επιλογή --", None)
        emps = self._session.query(Employee).filter_by(active=True).order_by(Employee.last_name).all()
        for e in emps:
            self._cb_employee.addItem(e.full_name, e.id)
        form.addRow("Υπάλληλος:", self._cb_employee)

        self._ed_notes = QTextEdit()
        self._ed_notes.setMaximumHeight(100)
        form.addRow("Σημειώσεις:", self._ed_notes)

        layout.addLayout(form)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Save).setText("Αποθήκευση")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Ακύρωση")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _save(self):
        action = self._cb_action.currentText().strip()
        if not action:
            QMessageBox.warning(self, "Σφάλμα", "Η ενέργεια είναι υποχρεωτική.")
            return
        old_status = self._protocol.status.value if self._protocol.status else None
        new_status_enum = self._cb_new_status.currentData()
        self._protocol.status = new_status_enum

        emp_id = self._cb_employee.currentData()
        emp_name = ""
        if emp_id:
            emp = self._session.get(Employee, emp_id)
            if emp:
                emp_name = emp.full_name

        h = ProtocolHistory(
            protocol_id=self._protocol.id,
            action=action,
            old_status=old_status,
            new_status=new_status_enum.value if new_status_enum else None,
            notes=self._ed_notes.toPlainText().strip() or None,
            employee_name=emp_name,
        )
        self._session.add(h)
        try:
            self._session.commit()
            self.accept()
        except Exception as ex:
            self._session.rollback()
            QMessageBox.critical(self, "Σφάλμα", str(ex))
