"""Search panel – main view for browsing protocols."""
from __future__ import annotations
from datetime import date
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QComboBox, QDateEdit,
    QSplitter, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from database.db import get_session, search_protocols
from database.models import (
    DocumentDirection, ProcessingStatus, DocumentPriority,
    Department, Employee, DocumentTheme, FileFolder, DocumentType,
)
from ui.widgets import ProtocolTable, SectionHeader
from utils.helpers import parse_date


class SearchPanel(QWidget):
    open_protocol = pyqtSignal(int)
    new_protocol = pyqtSignal(str)  # direction string

    def __init__(self, parent=None):
        super().__init__(parent)
        self._session = get_session()
        self._build_ui()
        self._populate_filters()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 12)

        # Title + quick actions
        title_row = QHBoxLayout()
        title_row.addWidget(SectionHeader("Αναζήτηση Εγγράφων"))
        title_row.addStretch()

        btn_new_in = QPushButton("+ Εισερχόμενο")
        btn_new_in.setStyleSheet("QPushButton{background:#276749;color:white;padding:8px 16px;border-radius:5px;font-weight:bold;} QPushButton:hover{background:#38a169;}")
        btn_new_in.clicked.connect(lambda: self.new_protocol.emit("ΕΙΣΕΡΧΟΜΕΝΟ"))

        btn_new_out = QPushButton("+ Εξερχόμενο")
        btn_new_out.setStyleSheet("QPushButton{background:#2b6cb0;color:white;padding:8px 16px;border-radius:5px;font-weight:bold;} QPushButton:hover{background:#3182ce;}")
        btn_new_out.clicked.connect(lambda: self.new_protocol.emit("ΕΞΕΡΧΟΜΕΝΟ"))

        btn_new_int = QPushButton("+ Εσωτερικό")
        btn_new_int.setStyleSheet("QPushButton{background:#744210;color:white;padding:8px 16px;border-radius:5px;font-weight:bold;} QPushButton:hover{background:#975a16;}")
        btn_new_int.clicked.connect(lambda: self.new_protocol.emit("ΕΣΩΤΕΡΙΚΟ"))

        title_row.addWidget(btn_new_in)
        title_row.addWidget(btn_new_out)
        title_row.addWidget(btn_new_int)
        root.addLayout(title_row)

        # Splitter: filters | results
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Filter panel ──────────────────────────────────────────────────────
        filter_widget = QWidget()
        filter_widget.setMaximumWidth(300)
        filter_widget.setMinimumWidth(220)
        fv = QVBoxLayout(filter_widget)
        fv.setSpacing(8)
        fv.setContentsMargins(0, 0, 8, 0)

        g_quick = QGroupBox("Γρήγορη Αναζήτηση")
        qf = QVBoxLayout(g_quick)
        self._ed_keyword = QLineEdit()
        self._ed_keyword.setPlaceholderText("Θέμα, αρ. πρωτ., αποστολέας...")
        self._ed_keyword.returnPressed.connect(self.do_search)
        qf.addWidget(self._ed_keyword)
        fv.addWidget(g_quick)

        g_filters = QGroupBox("Φίλτρα")
        ff = QFormLayout(g_filters)
        ff.setSpacing(6)

        self._cb_direction = QComboBox()
        self._cb_direction.addItem("Όλα", None)
        for d in DocumentDirection:
            self._cb_direction.addItem(d.value, d.value)
        ff.addRow("Κατεύθυνση:", self._cb_direction)

        self._cb_status = QComboBox()
        self._cb_status.addItem("Όλες", None)
        for s in ProcessingStatus:
            self._cb_status.addItem(s.value, s.value)
        ff.addRow("Κατάσταση:", self._cb_status)

        self._cb_priority = QComboBox()
        self._cb_priority.addItem("Όλες", None)
        for p in DocumentPriority:
            self._cb_priority.addItem(p.value, p.value)
        ff.addRow("Προτεραιότητα:", self._cb_priority)

        self._cb_department = QComboBox()
        self._cb_department.addItem("Όλα", None)
        ff.addRow("Τμήμα:", self._cb_department)

        self._cb_handler = QComboBox()
        self._cb_handler.addItem("Όλοι", None)
        ff.addRow("Χειριστής:", self._cb_handler)

        self._cb_year = QComboBox()
        self._cb_year.addItem("Όλα", None)
        current_year = date.today().year
        for y in range(current_year, current_year - 10, -1):
            self._cb_year.addItem(str(y), y)
        ff.addRow("Έτος:", self._cb_year)

        self._de_from = QDateEdit()
        self._de_from.setCalendarPopup(True)
        self._de_from.setDisplayFormat("dd/MM/yyyy")
        self._de_from.setSpecialValueText("Από...")
        self._de_from.setDate(QDate(date.today().year, 1, 1))
        ff.addRow("Από:", self._de_from)

        self._de_to = QDateEdit()
        self._de_to.setCalendarPopup(True)
        self._de_to.setDisplayFormat("dd/MM/yyyy")
        self._de_to.setSpecialValueText("Έως...")
        self._de_to.setDate(QDate.currentDate())
        ff.addRow("Έως:", self._de_to)

        self._cb_doc_type = QComboBox()
        self._cb_doc_type.addItem("Όλα", None)
        ff.addRow("Είδος:", self._cb_doc_type)

        self._cb_theme = QComboBox()
        self._cb_theme.addItem("Όλα", None)
        ff.addRow("Θέμα:", self._cb_theme)

        fv.addWidget(g_filters)

        btn_search = QPushButton("Αναζήτηση")
        btn_search.clicked.connect(self.do_search)
        btn_reset = QPushButton("Καθαρισμός")
        btn_reset.setProperty("flat", "true")
        btn_reset.clicked.connect(self._reset_filters)
        bh = QHBoxLayout()
        bh.addWidget(btn_reset)
        bh.addWidget(btn_search)
        fv.addLayout(bh)
        fv.addStretch()

        splitter.addWidget(filter_widget)

        # ── Results panel ─────────────────────────────────────────────────────
        results_widget = QWidget()
        rv = QVBoxLayout(results_widget)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(4)

        self._result_lbl = QLabel("Εμφάνιση εγγραφών...")
        self._result_lbl.setStyleSheet("color:#718096; font-size:12px;")

        # Action buttons for selected row
        action_row = QHBoxLayout()
        btn_open = QPushButton("Άνοιγμα")
        btn_open.clicked.connect(self._open_selected)
        btn_delete = QPushButton("Διαγραφή")
        btn_delete.setProperty("danger", "true")
        btn_delete.clicked.connect(self._delete_selected)
        btn_email = QPushButton("Αποστολή Email")
        btn_email.clicked.connect(self._email_selected)
        btn_print = QPushButton("Εκτύπωση")
        btn_print.clicked.connect(self._print_selected)
        action_row.addWidget(self._result_lbl)
        action_row.addStretch()
        action_row.addWidget(btn_email)
        action_row.addWidget(btn_print)
        action_row.addWidget(btn_open)
        action_row.addWidget(btn_delete)

        rv.addLayout(action_row)

        self._table = ProtocolTable()
        self._table.row_double_clicked.connect(self.open_protocol)
        rv.addWidget(self._table, 1)

        splitter.addWidget(results_widget)
        splitter.setSizes([260, 740])
        root.addWidget(splitter, 1)

        # Load all on startup
        self.do_search()

    def _populate_filters(self):
        s = self._session

        depts = s.query(Department).filter_by(active=True).order_by(Department.name).all()
        for d in depts:
            self._cb_department.addItem(d.name, d.id)

        emps = s.query(Employee).filter_by(active=True).order_by(Employee.last_name).all()
        for e in emps:
            self._cb_handler.addItem(e.full_name, e.id)

        from database.models import DocumentType, DocumentTheme
        types = s.query(DocumentType).filter_by(active=True).order_by(DocumentType.name).all()
        for t in types:
            self._cb_doc_type.addItem(t.name, t.id)

        themes = s.query(DocumentTheme).filter_by(active=True).order_by(DocumentTheme.name).all()
        for t in themes:
            self._cb_theme.addItem(t.name, t.id)

    def do_search(self):
        s = self._session
        keyword = self._ed_keyword.text().strip()
        direction = self._cb_direction.currentData()
        status = self._cb_status.currentData()
        priority = self._cb_priority.currentData()
        dept_id = self._cb_department.currentData()
        handler_id = self._cb_handler.currentData()
        year = self._cb_year.currentData()
        doc_type_id = self._cb_doc_type.currentData()
        theme_id = self._cb_theme.currentData()

        qd_from = self._de_from.date()
        qd_to = self._de_to.date()
        d_from = date(qd_from.year(), qd_from.month(), qd_from.day()) if not self._de_from.specialValueText() == self._de_from.text() else None
        d_to = date(qd_to.year(), qd_to.month(), qd_to.day()) if not self._de_to.specialValueText() == self._de_to.text() else None

        results, total = search_protocols(
            s,
            keyword=keyword,
            direction=direction,
            status=status,
            priority=priority,
            department_id=dept_id,
            handler_id=handler_id,
            year=year,
            doc_type_id=doc_type_id,
            theme_id=theme_id,
            date_from=d_from,
            date_to=d_to,
        )
        self._table.populate(results)
        self._result_lbl.setText(f"Βρέθηκαν {total} εγγραφές")

    def _reset_filters(self):
        self._ed_keyword.clear()
        self._cb_direction.setCurrentIndex(0)
        self._cb_status.setCurrentIndex(0)
        self._cb_priority.setCurrentIndex(0)
        self._cb_department.setCurrentIndex(0)
        self._cb_handler.setCurrentIndex(0)
        self._cb_year.setCurrentIndex(0)
        self._cb_doc_type.setCurrentIndex(0)
        self._cb_theme.setCurrentIndex(0)
        self.do_search()

    def _open_selected(self):
        pid = self._table.selected_protocol_id()
        if pid:
            self.open_protocol.emit(pid)

    def _delete_selected(self):
        from database.models import Protocol, EmailLog
        from ui.widgets import ConfirmDialog
        from PyQt6.QtWidgets import QMessageBox

        pid = self._table.selected_protocol_id()
        if not pid:
            return

        p = self._session.get(Protocol, pid)
        if not p:
            return

        proto_num = p.protocol_full or str(p.protocol_number or pid)
        if not ConfirmDialog.ask(
            self,
            "Διαγραφή Εγγράφου",
            f"Να διαγραφεί οριστικά το έγγραφο\n«{proto_num}»;\n\n"
            "Θα διαγραφούν επίσης όλα τα συνημμένα και το ιστορικό του."
        ):
            return

        try:
            # Delete email logs manually (no cascade on that relation)
            self._session.query(EmailLog).filter_by(protocol_id=pid).delete(
                synchronize_session=False)
            self._session.delete(p)
            self._session.commit()
            QMessageBox.information(self, "Διαγραφή",
                                    f"Το έγγραφο {proto_num} διαγράφηκε.")
            self.do_search()
        except Exception as ex:
            self._session.rollback()
            QMessageBox.critical(self, "Σφάλμα Διαγραφής",
                                 f"Αδυναμία διαγραφής:\n{ex}")

    def _email_selected(self):
        pid = self._table.selected_protocol_id()
        if not pid:
            return
        from database.models import Protocol
        p = self._session.get(Protocol, pid)
        if p:
            from ui.email_dialog import EmailDialog
            dlg = EmailDialog(self._session, p, self)
            dlg.exec()

    def _print_selected(self):
        pid = self._table.selected_protocol_id()
        if not pid:
            return
        from database.models import Protocol
        p = self._session.get(Protocol, pid)
        if p:
            from reports.receipt import print_receipt
            from config.settings import load_config
            print_receipt(p, load_config())

    def refresh(self):
        self.do_search()
