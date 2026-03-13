"""Employee create/edit dialog."""
from __future__ import annotations
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QPushButton,
    QLineEdit, QComboBox, QDialogButtonBox, QMessageBox,
)
from database.models import Employee, Department, JobPosition
from sqlalchemy.orm import Session


class EmployeeDialog(QDialog):
    def __init__(self, session: Session, employee_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self._session = session
        self._emp_id = employee_id
        self.setWindowTitle("Στοιχεία Υπαλλήλου")
        self.setMinimumWidth(440)
        self._build_ui()
        if employee_id:
            self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(8)

        self._ed_code = QLineEdit()
        form.addRow("Κωδικός:", self._ed_code)

        self._ed_last = QLineEdit()
        form.addRow("Επώνυμο *:", self._ed_last)

        self._ed_first = QLineEdit()
        form.addRow("Όνομα *:", self._ed_first)

        self._cb_dept = QComboBox()
        self._cb_dept.addItem("-- Επιλογή --", None)
        for d in self._session.query(Department).filter_by(active=True).order_by(Department.name).all():
            self._cb_dept.addItem(d.name, d.id)
        form.addRow("Τμήμα:", self._cb_dept)

        self._cb_pos = QComboBox()
        self._cb_pos.addItem("-- Επιλογή --", None)
        for p in self._session.query(JobPosition).filter_by(active=True).order_by(JobPosition.name).all():
            self._cb_pos.addItem(p.name, p.id)
        form.addRow("Θέση:", self._cb_pos)

        self._ed_email = QLineEdit()
        form.addRow("Email:", self._ed_email)

        self._ed_phone = QLineEdit()
        form.addRow("Τηλέφωνο:", self._ed_phone)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("Αποθήκευση")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Ακύρωση")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load(self):
        e = self._session.get(Employee, self._emp_id)
        if not e:
            return
        self._ed_code.setText(e.code or "")
        self._ed_last.setText(e.last_name or "")
        self._ed_first.setText(e.first_name or "")
        self._ed_email.setText(e.email or "")
        self._ed_phone.setText(e.phone or "")
        for i in range(self._cb_dept.count()):
            if self._cb_dept.itemData(i) == e.department_id:
                self._cb_dept.setCurrentIndex(i)
                break
        for i in range(self._cb_pos.count()):
            if self._cb_pos.itemData(i) == e.position_id:
                self._cb_pos.setCurrentIndex(i)
                break

    def _save(self):
        last = self._ed_last.text().strip()
        first = self._ed_first.text().strip()
        if not last or not first:
            QMessageBox.warning(self, "Σφάλμα", "Επώνυμο και όνομα είναι υποχρεωτικά.")
            return
        if self._emp_id:
            e = self._session.get(Employee, self._emp_id)
        else:
            e = Employee()
            self._session.add(e)
        e.code = self._ed_code.text().strip() or None
        e.last_name = last
        e.first_name = first
        e.email = self._ed_email.text().strip() or None
        e.phone = self._ed_phone.text().strip() or None
        e.department_id = self._cb_dept.currentData()
        e.position_id = self._cb_pos.currentData()
        try:
            self._session.commit()
            self.accept()
        except Exception as ex:
            self._session.rollback()
            QMessageBox.critical(self, "Σφάλμα", str(ex))
