"""Protocol registration / edit form dialog."""
from __future__ import annotations
import os
from datetime import date
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QDateEdit,
    QCheckBox, QTabWidget, QWidget, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QSplitter, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialogButtonBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from database.db import get_session, create_protocol, next_protocol_number, format_protocol_number, REGISTRY_PREFIXES
from database.models import (
    Protocol, DocumentDirection, DocumentPriority, ProcessingStatus,
    RegistryType, Contact, Employee, Department, DocumentType, DocumentTheme,
    FileFolder, Attachment, ProtocolHistory,
)
from config.settings import ATTACHMENTS_DIR, load_config
from utils.helpers import format_date_short, copy_file_to_store, file_extension, file_size_human


class ProtocolForm(QDialog):
    """Create or edit a protocol entry."""
    saved = pyqtSignal(int)  # protocol id

    def __init__(self, protocol_id: Optional[int] = None,
                 direction: DocumentDirection = DocumentDirection.INCOMING,
                 parent=None):
        super().__init__(parent)
        self.protocol_id = protocol_id
        self.default_direction = direction
        self._protocol: Optional[Protocol] = None
        self._session = get_session()
        self._config = load_config()

        self.setWindowTitle("Καταχώρηση Εγγράφου" if not protocol_id else "Επεξεργασία Εγγράφου")
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)
        self._build_ui()
        if protocol_id:
            self._load_protocol()
        else:
            self._setup_defaults()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # Header bar
        header = QWidget()
        header.setStyleSheet("background:#1a365d; padding:10px;")
        hl = QHBoxLayout(header)
        self._title_lbl = QLabel("Νέο Έγγραφο")
        self._title_lbl.setStyleSheet("color:white; font-size:16px; font-weight:bold;")
        self._proto_num_lbl = QLabel("")
        self._proto_num_lbl.setStyleSheet(
            "color:#bee3f8; font-size:20px; font-weight:bold; margin-left:20px;"
        )
        hl.addWidget(self._title_lbl)
        hl.addWidget(self._proto_num_lbl)
        hl.addStretch()
        root.addWidget(header)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setContentsMargins(8, 8, 8, 8)
        root.addWidget(self._tabs, 1)

        self._tabs.addTab(self._build_main_tab(), "Βασικά Στοιχεία")
        self._tabs.addTab(self._build_recipients_tab(), "Αποστολέας / Αποδέκτες")
        self._tabs.addTab(self._build_attachments_tab(), "Συνημμένα / Σκαναρισμένα")
        self._tabs.addTab(self._build_history_tab(), "Ιστορικό Σταδίων")

        # Buttons
        btn_bar = QWidget()
        btn_bar.setStyleSheet("background:#f7fafc; border-top:1px solid #e2e8f0;")
        bl = QHBoxLayout(btn_bar)
        bl.setContentsMargins(12, 8, 12, 8)

        self._btn_save = QPushButton("Αποθήκευση")
        self._btn_save.setStyleSheet(
            "QPushButton{background:#38a169;color:white;padding:9px 24px;"
            "border-radius:5px;font-size:14px;font-weight:bold;}"
            "QPushButton:hover{background:#48bb78;}"
        )
        self._btn_save.clicked.connect(self._save)

        btn_cancel = QPushButton("Ακύρωση")
        btn_cancel.setProperty("flat", "true")
        btn_cancel.clicked.connect(self.reject)

        self._btn_receipt = QPushButton("Εκτύπωση Βεβαίωσης")
        self._btn_receipt.setEnabled(bool(self.protocol_id))
        self._btn_receipt.clicked.connect(self._print_receipt)

        bl.addWidget(self._btn_receipt)
        bl.addStretch()
        bl.addWidget(btn_cancel)
        bl.addWidget(self._btn_save)
        root.addWidget(btn_bar)

    def _build_main_tab(self) -> QWidget:
        w = QScrollArea()
        w.setWidgetResizable(True)
        inner = QWidget()
        w.setWidget(inner)
        layout = QVBoxLayout(inner)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Direction & Protocol number
        g_proto = QGroupBox("Στοιχεία Πρωτοκόλλου")
        gf = QFormLayout(g_proto)
        gf.setSpacing(8)

        self._cb_registry = QComboBox()
        for rt in RegistryType:
            self._cb_registry.addItem(rt.value, rt)
        self._cb_registry.currentIndexChanged.connect(self._update_proto_preview)
        gf.addRow("Τύπος Πρωτοκόλλου *:", self._cb_registry)

        self._cb_direction = QComboBox()
        for d in DocumentDirection:
            self._cb_direction.addItem(d.value, d)
        self._cb_direction.currentIndexChanged.connect(self._on_direction_changed)
        gf.addRow("Κατεύθυνση *:", self._cb_direction)

        date_row = QWidget()
        dr_layout = QHBoxLayout(date_row)
        dr_layout.setContentsMargins(0, 0, 0, 0)
        self._de_proto_date = QDateEdit(QDate.currentDate())
        self._de_proto_date.setCalendarPopup(True)
        self._de_proto_date.setDisplayFormat("dd/MM/yyyy")
        self._lbl_proto_num = QLabel("<i>Θα αποδοθεί αυτόματα</i>")
        self._lbl_proto_num.setStyleSheet("color:#2b6cb0; font-weight:bold; font-size:16px;")
        dr_layout.addWidget(self._de_proto_date)
        dr_layout.addWidget(QLabel("  Αρ. Πρωτ.:"))
        dr_layout.addWidget(self._lbl_proto_num)
        dr_layout.addStretch()
        gf.addRow("Ημερομηνία *:", date_row)

        self._cb_priority = QComboBox()
        for p in DocumentPriority:
            self._cb_priority.addItem(p.value, p)
        gf.addRow("Προτεραιότητα:", self._cb_priority)

        self._cb_status = QComboBox()
        for s in ProcessingStatus:
            self._cb_status.addItem(s.value, s)
        gf.addRow("Κατάσταση:", self._cb_status)

        self._cb_doc_type = QComboBox()
        self._cb_doc_type.addItem("-- Επιλογή --", None)
        gf.addRow("Είδος Εγγράφου:", self._cb_doc_type)

        layout.addWidget(g_proto)

        # Subject & summary
        g_subject = QGroupBox("Θέμα Εγγράφου")
        gsf = QFormLayout(g_subject)
        gsf.setSpacing(8)
        self._ed_subject = QLineEdit()
        self._ed_subject.setPlaceholderText("Εισάγετε το θέμα του εγγράφου...")
        self._ed_subject.setMinimumHeight(36)
        gsf.addRow("Θέμα *:", self._ed_subject)

        self._cb_theme = QComboBox()
        self._cb_theme.addItem("-- Επιλογή --", None)
        gsf.addRow("Κατηγορία Θέματος:", self._cb_theme)

        self._ed_summary = QTextEdit()
        self._ed_summary.setPlaceholderText("Σύντομη περιγραφή εγγράφου...")
        self._ed_summary.setMaximumHeight(80)
        gsf.addRow("Περίληψη:", self._ed_summary)
        layout.addWidget(g_subject)

        # External reference
        g_ext = QGroupBox("Εξωτερική Αναφορά (για Εισερχόμενα)")
        gef = QFormLayout(g_ext)
        gef.setSpacing(8)
        self._ed_ext_num = QLineEdit()
        self._ed_ext_num.setPlaceholderText("Αρ. Πρωτ. Αποστολέα")
        gef.addRow("Αρ. Πρωτ. Αποστολέα:", self._ed_ext_num)
        self._de_ext_date = QDateEdit()
        self._de_ext_date.setCalendarPopup(True)
        self._de_ext_date.setDisplayFormat("dd/MM/yyyy")
        self._de_ext_date.setSpecialValueText(" ")
        self._de_ext_date.setDate(QDate.currentDate())
        gef.addRow("Ημερομηνία Αποστολέα:", self._de_ext_date)
        self._de_received = QDateEdit(QDate.currentDate())
        self._de_received.setCalendarPopup(True)
        self._de_received.setDisplayFormat("dd/MM/yyyy")
        gef.addRow("Ημερομηνία Παραλαβής:", self._de_received)
        self._de_deadline = QDateEdit()
        self._de_deadline.setCalendarPopup(True)
        self._de_deadline.setDisplayFormat("dd/MM/yyyy")
        self._de_deadline.setSpecialValueText(" ")
        self._de_deadline.setDate(QDate.currentDate())
        gef.addRow("Προθεσμία Διεκπεραίωσης:", self._de_deadline)
        layout.addWidget(g_ext)

        # Classification
        g_class = QGroupBox("Ταξινόμηση")
        gcf = QFormLayout(g_class)
        gcf.setSpacing(8)
        self._cb_department = QComboBox()
        self._cb_department.addItem("-- Επιλογή --", None)
        gcf.addRow("Τμήμα:", self._cb_department)

        self._cb_handler = QComboBox()
        self._cb_handler.addItem("-- Επιλογή --", None)
        gcf.addRow("Χειριστής:", self._cb_handler)

        self._cb_folder = QComboBox()
        self._cb_folder.addItem("-- Επιλογή --", None)
        gcf.addRow("Φάκελος Αρχείου:", self._cb_folder)
        layout.addWidget(g_class)

        layout.addStretch()
        self._populate_combos_main()
        return w

    def _build_recipients_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Sender
        g_sender = QGroupBox("Αποστολέας")
        sf = QFormLayout(g_sender)
        sf.setSpacing(8)
        sender_row = QWidget()
        sl = QHBoxLayout(sender_row)
        sl.setContentsMargins(0, 0, 0, 0)
        self._cb_sender = QComboBox()
        self._cb_sender.setEditable(True)
        self._cb_sender.setMinimumWidth(300)
        self._cb_sender.addItem("-- Επιλογή --", None)
        btn_new_sender = QPushButton("+")
        btn_new_sender.setToolTip("Νέα επαφή")
        btn_new_sender.setMaximumWidth(30)
        btn_new_sender.clicked.connect(self._new_contact)
        sl.addWidget(self._cb_sender, 1)
        sl.addWidget(btn_new_sender)
        sf.addRow("Εξωτερικός Αποστολέας:", sender_row)

        self._cb_sender_emp = QComboBox()
        self._cb_sender_emp.addItem("-- Επιλογή --", None)
        sf.addRow("Εσωτερικός Αποστολέας:", self._cb_sender_emp)
        layout.addWidget(g_sender)

        # Recipients
        g_recv = QGroupBox("Αποδέκτες")
        rv = QVBoxLayout(g_recv)
        rh = QHBoxLayout()
        self._cb_add_recipient = QComboBox()
        self._cb_add_recipient.setEditable(True)
        self._cb_add_recipient.setMinimumWidth(300)
        btn_add_r = QPushButton("Προσθήκη")
        btn_add_r.clicked.connect(self._add_recipient)
        btn_add_list = QPushButton("Πίνακας Αποδεκτών")
        btn_add_list.clicked.connect(self._add_from_list)
        rh.addWidget(QLabel("Αποδέκτης:"))
        rh.addWidget(self._cb_add_recipient, 1)
        rh.addWidget(btn_add_r)
        rh.addWidget(btn_add_list)
        rv.addLayout(rh)
        self._list_recipients = QListWidget()
        self._list_recipients.setMaximumHeight(120)
        btn_del_r = QPushButton("Αφαίρεση επιλεγμένου")
        btn_del_r.clicked.connect(self._remove_recipient)
        rv.addWidget(self._list_recipients)
        rv.addWidget(btn_del_r)
        layout.addWidget(g_recv)

        # CC
        g_cc = QGroupBox("Κοινοποίηση (ΚΕ)")
        cv = QVBoxLayout(g_cc)
        ch = QHBoxLayout()
        self._cb_add_cc = QComboBox()
        self._cb_add_cc.setEditable(True)
        self._cb_add_cc.setMinimumWidth(300)
        btn_add_cc = QPushButton("Προσθήκη")
        btn_add_cc.clicked.connect(self._add_cc)
        ch.addWidget(QLabel("Κοινοποίηση:"))
        ch.addWidget(self._cb_add_cc, 1)
        ch.addWidget(btn_add_cc)
        cv.addLayout(ch)
        self._list_cc = QListWidget()
        self._list_cc.setMaximumHeight(100)
        btn_del_cc = QPushButton("Αφαίρεση επιλεγμένου")
        btn_del_cc.clicked.connect(self._remove_cc)
        cv.addWidget(self._list_cc)
        cv.addWidget(btn_del_cc)
        layout.addWidget(g_cc)

        layout.addStretch()
        self._populate_combos_recipients()
        return w

    def _build_attachments_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        btn_row = QHBoxLayout()
        btn_add_file = QPushButton("Προσθήκη Αρχείου")
        btn_add_file.clicked.connect(self._add_file)
        btn_scan = QPushButton("Σάρωση (Scanner)")
        btn_scan.clicked.connect(self._scan_document)
        btn_del_att = QPushButton("Αφαίρεση")
        btn_del_att.clicked.connect(self._remove_attachment)
        btn_open_att = QPushButton("Άνοιγμα")
        btn_open_att.clicked.connect(self._open_attachment)
        btn_row.addWidget(btn_add_file)
        btn_row.addWidget(btn_scan)
        btn_row.addStretch()
        btn_row.addWidget(btn_open_att)
        btn_row.addWidget(btn_del_att)
        layout.addLayout(btn_row)

        self._att_table = QTableWidget(0, 4)
        self._att_table.setHorizontalHeaderLabels(["Αρχείο", "Τύπος", "Μέγεθος", "Περιγραφή"])
        self._att_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._att_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._att_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._att_table.setAlternatingRowColors(True)
        layout.addWidget(self._att_table, 1)

        self._pending_attachments: list[dict] = []  # for new unsaved protocols
        return w

    def _build_history_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        # Add stage button
        btn_row = QHBoxLayout()
        btn_add_stage = QPushButton("Καταχώρηση Σταδίου")
        btn_add_stage.clicked.connect(self._add_history_stage)
        btn_row.addWidget(btn_add_stage)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._history_table = QTableWidget(0, 4)
        self._history_table.setHorizontalHeaderLabels(["Ημερομηνία/Ώρα", "Ενέργεια", "Χρήστης", "Σημειώσεις"])
        self._history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._history_table.setAlternatingRowColors(True)
        layout.addWidget(self._history_table, 1)
        return w

    # ── Populate combos ───────────────────────────────────────────────────────

    def _populate_combos_main(self):
        s = self._session

        # Departments
        depts = s.query(Department).filter_by(active=True).order_by(Department.name).all()
        for d in depts:
            self._cb_department.addItem(d.name, d.id)

        # Employees
        emps = s.query(Employee).filter_by(active=True).order_by(Employee.last_name).all()
        for e in emps:
            self._cb_handler.addItem(e.full_name, e.id)

        # Doc types
        types = s.query(DocumentType).filter_by(active=True).order_by(DocumentType.name).all()
        for t in types:
            self._cb_doc_type.addItem(t.name, t.id)

        # Themes
        themes = s.query(DocumentTheme).filter_by(active=True).order_by(DocumentTheme.name).all()
        for t in themes:
            self._cb_theme.addItem(t.name, t.id)

        # Folders
        folders = s.query(FileFolder).filter_by(active=True, parent_id=None).order_by(FileFolder.name).all()
        for f in folders:
            self._cb_folder.addItem(f.name, f.id)
            for child in f.children:
                self._cb_folder.addItem(f"  └ {child.name}", child.id)

    def _populate_combos_recipients(self):
        s = self._session
        contacts = s.query(Contact).filter_by(active=True).order_by(Contact.name).all()
        for c in contacts:
            self._cb_sender.addItem(c.display_name, c.id)
            self._cb_add_recipient.addItem(c.display_name, c.id)
            self._cb_add_cc.addItem(c.display_name, c.id)

        emps = s.query(Employee).filter_by(active=True).order_by(Employee.last_name).all()
        for e in emps:
            self._cb_sender_emp.addItem(e.full_name, e.id)

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_direction_changed(self):
        d = self._cb_direction.currentData()
        titles = {
            DocumentDirection.INCOMING: "Εισερχόμενο Έγγραφο",
            DocumentDirection.OUTGOING: "Εξερχόμενο Έγγραφο",
            DocumentDirection.INTERNAL: "Εσωτερικό Έγγραφο",
        }
        self._title_lbl.setText(titles.get(d, "Νέο Έγγραφο"))

    def _update_proto_preview(self):
        from database.models import ProtocolCounter
        s = self._session
        year = date.today().year
        registry_type = self._cb_registry.currentData() or RegistryType.GENERAL
        reg_val = registry_type.value
        counter = s.query(ProtocolCounter).filter_by(year=year, registry_type=reg_val).first()
        next_num = (counter.last_number + 1) if counter else 1
        prefix = self._config.get("protocol_prefix", "")
        preview = format_protocol_number(next_num, year, prefix, registry_type)
        self._lbl_proto_num.setText(f"{preview} (προεπισκόπηση)")

    def _setup_defaults(self):
        # Pre-select direction
        for i in range(self._cb_direction.count()):
            if self._cb_direction.itemData(i) == self.default_direction:
                self._cb_direction.setCurrentIndex(i)
                break
        self._on_direction_changed()
        self._update_proto_preview()

    def _add_recipient(self):
        cid = self._cb_add_recipient.currentData()
        text = self._cb_add_recipient.currentText()
        if not text or text == "-- Επιλογή --":
            return
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, cid)
        self._list_recipients.addItem(item)

    def _remove_recipient(self):
        row = self._list_recipients.currentRow()
        if row >= 0:
            self._list_recipients.takeItem(row)

    def _add_cc(self):
        cid = self._cb_add_cc.currentData()
        text = self._cb_add_cc.currentText()
        if not text or text == "-- Επιλογή --":
            return
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, cid)
        self._list_cc.addItem(item)

    def _remove_cc(self):
        row = self._list_cc.currentRow()
        if row >= 0:
            self._list_cc.takeItem(row)

    def _add_from_list(self):
        from ui.dialogs import RecipientListDialog
        dlg = RecipientListDialog(self._session, self)
        if dlg.exec():
            for name, cid in dlg.selected():
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, cid)
                self._list_recipients.addItem(item)

    def _new_contact(self):
        from ui.dialogs import ContactDialog
        dlg = ContactDialog(self._session, parent=self)
        if dlg.exec():
            c = dlg.contact
            self._cb_sender.addItem(c.display_name, c.id)
            idx = self._cb_sender.count() - 1
            self._cb_sender.setCurrentIndex(idx)

    def _add_file(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Επιλογή Αρχείου", "",
            "Όλα τα αρχεία (*.*);;PDF (*.pdf);;Word (*.doc *.docx);;Excel (*.xls *.xlsx);;Email (*.eml *.msg);;Εικόνες (*.jpg *.png *.tif)"
        )
        for path in paths:
            self._attach_file(path, is_scan=False)

    def _scan_document(self):
        from services.scanner import scan_document
        paths = scan_document(parent=self)
        for path in paths:
            self._attach_file(path, is_scan=True)

    def _attach_file(self, path: str, is_scan: bool = False):
        p = Path(path)
        if not p.exists():
            return
        ext = file_extension(path)
        size = p.stat().st_size
        row = self._att_table.rowCount()
        self._att_table.insertRow(row)
        self._att_table.setItem(row, 0, QTableWidgetItem(p.name))
        self._att_table.setItem(row, 1, QTableWidgetItem(ext.upper()))
        self._att_table.setItem(row, 2, QTableWidgetItem(file_size_human(size)))
        self._att_table.setItem(row, 3, QTableWidgetItem("Σκαναρισμένο" if is_scan else ""))
        self._pending_attachments.append({
            "path": path,
            "filename": p.name,
            "ext": ext,
            "size": size,
            "is_scan": is_scan,
        })

    def _remove_attachment(self):
        row = self._att_table.currentRow()
        if row >= 0:
            self._att_table.removeRow(row)
            if row < len(self._pending_attachments):
                self._pending_attachments.pop(row)
            elif self._protocol:
                # remove saved attachment
                pass

    def _open_attachment(self):
        row = self._att_table.currentRow()
        if row < 0:
            return
        from utils.stamp import stamp_and_open
        from utils.helpers import format_date_short

        proto_num  = ""
        proto_date = ""
        if self._protocol:
            proto_num  = self._protocol.protocol_full or ""
            proto_date = format_date_short(self._protocol.protocol_date) if self._protocol.protocol_date else ""

        if self._protocol and row < len(self._protocol.attachments):
            att = self._protocol.attachments[row]
            file_path = att.file_path if os.path.exists(att.file_path or "") else None
            if file_path:
                stamp_and_open(file_path, proto_num, proto_date)
            else:
                QMessageBox.warning(self, "Αρχείο", "Το αρχείο δεν βρέθηκε.")
        elif row < len(self._pending_attachments):
            stamp_and_open(self._pending_attachments[row]["path"], proto_num, proto_date)

    def _add_history_stage(self):
        from ui.dialogs import HistoryStageDialog
        if not self._protocol:
            QMessageBox.information(self, "Πληροφορία", "Αποθηκεύστε πρώτα το έγγραφο.")
            return
        dlg = HistoryStageDialog(self._session, self._protocol, self)
        if dlg.exec():
            self._reload_history()

    # ── Load existing protocol ────────────────────────────────────────────────

    def _load_protocol(self):
        self._protocol = self._session.get(Protocol, self.protocol_id)
        if not self._protocol:
            return
        p = self._protocol
        self._lbl_proto_num.setText(p.protocol_full or "")
        self._title_lbl.setText(f"Επεξεργασία: {p.protocol_full}")

        # Direction
        for i in range(self._cb_direction.count()):
            if self._cb_direction.itemData(i) == p.direction:
                self._cb_direction.setCurrentIndex(i)
                break

        # Dates
        if p.protocol_date:
            self._de_proto_date.setDate(QDate(p.protocol_date.year, p.protocol_date.month, p.protocol_date.day))

        # Subject
        self._ed_subject.setText(p.subject or "")
        self._ed_summary.setPlainText(p.summary or "")
        self._ed_ext_num.setText(p.ext_protocol_number or "")

        # Priority/Status
        for i in range(self._cb_priority.count()):
            if self._cb_priority.itemData(i) == p.priority:
                self._cb_priority.setCurrentIndex(i)
                break
        for i in range(self._cb_status.count()):
            if self._cb_status.itemData(i) == p.status:
                self._cb_status.setCurrentIndex(i)
                break

        # Recipients
        for c in p.recipients:
            item = QListWidgetItem(c.display_name)
            item.setData(Qt.ItemDataRole.UserRole, c.id)
            self._list_recipients.addItem(item)
        for c in p.cc_contacts:
            item = QListWidgetItem(c.display_name)
            item.setData(Qt.ItemDataRole.UserRole, c.id)
            self._list_cc.addItem(item)

        # Attachments
        self._reload_attachments()
        self._reload_history()
        self._btn_receipt.setEnabled(True)

    def _reload_attachments(self):
        self._att_table.setRowCount(0)
        if self._protocol:
            for att in self._protocol.attachments:
                row = self._att_table.rowCount()
                self._att_table.insertRow(row)
                self._att_table.setItem(row, 0, QTableWidgetItem(att.original_filename or att.filename))
                self._att_table.setItem(row, 1, QTableWidgetItem(att.file_type or ""))
                self._att_table.setItem(row, 2, QTableWidgetItem(file_size_human(att.file_size or 0)))
                self._att_table.setItem(row, 3, QTableWidgetItem(att.description or ""))

    def _reload_history(self):
        self._history_table.setRowCount(0)
        if self._protocol:
            for h in self._protocol.history:
                row = self._history_table.rowCount()
                self._history_table.insertRow(row)
                self._history_table.setItem(row, 0, QTableWidgetItem(
                    h.created_at.strftime("%d/%m/%Y %H:%M") if h.created_at else ""))
                self._history_table.setItem(row, 1, QTableWidgetItem(h.action or ""))
                self._history_table.setItem(row, 2, QTableWidgetItem(h.employee_name or ""))
                self._history_table.setItem(row, 3, QTableWidgetItem(h.notes or ""))

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self):
        subject = self._ed_subject.text().strip()
        if not subject:
            QMessageBox.warning(self, "Σφάλμα", "Το θέμα είναι υποχρεωτικό.")
            self._tabs.setCurrentIndex(0)
            self._ed_subject.setFocus()
            return

        direction = self._cb_direction.currentData()
        priority = self._cb_priority.currentData()
        status = self._cb_status.currentData()
        qd = self._de_proto_date.date()
        proto_date = date(qd.year(), qd.month(), qd.day())

        try:
            s = self._session
            if self._protocol is None:
                # New protocol
                prefix = self._config.get("protocol_prefix", "")
                registry_type = self._cb_registry.currentData() or RegistryType.GENERAL
                self._protocol = create_protocol(
                    s,
                    direction=direction,
                    subject=subject,
                    protocol_date=proto_date,
                    priority=priority,
                    status=status,
                    registry_type=registry_type,
                    summary=self._ed_summary.toPlainText().strip() or None,
                    ext_protocol_number=self._ed_ext_num.text().strip() or None,
                    department_id=self._cb_department.currentData(),
                    handler_id=self._cb_handler.currentData(),
                    folder_id=self._cb_folder.currentData(),
                    theme_id=self._cb_theme.currentData(),
                    doc_type_id=self._cb_doc_type.currentData(),
                    sender_contact_id=self._cb_sender.currentData(),
                    sender_employee_id=self._cb_sender_emp.currentData(),
                    prefix=prefix,
                )
            else:
                p = self._protocol
                p.direction = direction
                p.subject = subject
                p.priority = priority
                p.status = status
                p.protocol_date = proto_date
                p.summary = self._ed_summary.toPlainText().strip() or None
                p.ext_protocol_number = self._ed_ext_num.text().strip() or None
                p.department_id = self._cb_department.currentData()
                p.handler_id = self._cb_handler.currentData()
                p.folder_id = self._cb_folder.currentData()
                p.theme_id = self._cb_theme.currentData()
                p.doc_type_id = self._cb_doc_type.currentData()
                p.sender_contact_id = self._cb_sender.currentData()
                p.sender_employee_id = self._cb_sender_emp.currentData()

            # Recipients
            self._protocol.recipients.clear()
            for i in range(self._list_recipients.count()):
                cid = self._list_recipients.item(i).data(Qt.ItemDataRole.UserRole)
                if cid:
                    c = s.get(Contact, cid)
                    if c:
                        self._protocol.recipients.append(c)

            # CC
            self._protocol.cc_contacts.clear()
            for i in range(self._list_cc.count()):
                cid = self._list_cc.item(i).data(Qt.ItemDataRole.UserRole)
                if cid:
                    c = s.get(Contact, cid)
                    if c:
                        self._protocol.cc_contacts.append(c)

            # Save attachments
            for att_info in self._pending_attachments:
                dest = copy_file_to_store(
                    att_info["path"], ATTACHMENTS_DIR,
                    prefix=f"p{self._protocol.protocol_full.replace('/', '_')}_"
                )
                att = Attachment(
                    protocol_id=self._protocol.id,
                    filename=dest.name,
                    original_filename=att_info["filename"],
                    file_path=str(dest),
                    file_type=att_info["ext"],
                    file_size=att_info["size"],
                    is_scan=att_info["is_scan"],
                )
                s.add(att)
            self._pending_attachments.clear()

            s.commit()
            self._lbl_proto_num.setText(self._protocol.protocol_full or "")
            self._btn_receipt.setEnabled(True)
            self.saved.emit(self._protocol.id)

            # Auto-archive attachments if enabled
            try:
                from services.archiver import archive_protocol_attachments
                cfg = load_config()
                if cfg.get("archive_enabled") and self._protocol.attachments:
                    archive_protocol_attachments(self._protocol, cfg)
            except Exception:
                pass  # archiving failure should not block saving

            QMessageBox.information(self, "Επιτυχία",
                f"Το έγγραφο αποθηκεύτηκε με αριθμό πρωτοκόλλου:\n{self._protocol.protocol_full}")
            self.accept()

        except Exception as ex:
            self._session.rollback()
            QMessageBox.critical(self, "Σφάλμα αποθήκευσης", str(ex))

    def _print_receipt(self):
        if not self._protocol:
            return
        from reports.receipt import print_receipt
        print_receipt(self._protocol, self._config)

    def closeEvent(self, event):
        self._session.close()
        super().closeEvent(event)
