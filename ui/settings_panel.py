"""Parametric settings panel (departments, employees, contacts, etc.)."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFormLayout, QGroupBox, QMessageBox, QDialog, QDialogButtonBox,
    QTextEdit, QListWidget, QListWidgetItem, QSplitter,
)
from PyQt6.QtCore import Qt

from database.db import get_session
from database.models import (
    Department, JobPosition, Employee, Contact,
    RecipientList, FileFolder, DocumentTheme, DocumentType,
)
from ui.widgets import SectionHeader, ConfirmDialog
from config.settings import load_config, save_config


class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._session = get_session()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 12)
        root.addWidget(SectionHeader("Παραμετρικά Στοιχεία"))

        tabs = QTabWidget()
        tabs.addTab(self._build_org_tab(), "Οργανισμός")
        tabs.addTab(self._build_departments_tab(), "Τμήματα")
        tabs.addTab(self._build_positions_tab(), "Θέσεις")
        tabs.addTab(self._build_employees_tab(), "Υπάλληλοι")
        tabs.addTab(self._build_contacts_tab(), "Επαφές")
        tabs.addTab(self._build_recipient_lists_tab(), "Πίνακες Αποδεκτών")
        tabs.addTab(self._build_folders_tab(), "Φάκελοι Αρχείου")
        tabs.addTab(self._build_themes_tab(), "Θέματα")
        tabs.addTab(self._build_doc_types_tab(), "Είδη Εγγράφων")
        tabs.addTab(self._build_email_tab(), "Email / SMTP")
        tabs.addTab(self._build_archive_tab(), "Αρχειοθέτηση")
        root.addWidget(tabs, 1)

    # ── Organisation ──────────────────────────────────────────────────────────

    def _build_org_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        cfg = load_config()
        form = QFormLayout()
        form.setSpacing(10)
        self._ed_org_name = QLineEdit(cfg.get("organization_name", ""))
        form.addRow("Επωνυμία Οργανισμού:", self._ed_org_name)
        self._ed_org_address = QLineEdit(cfg.get("organization_address", ""))
        form.addRow("Διεύθυνση:", self._ed_org_address)
        self._ed_org_phone = QLineEdit(cfg.get("organization_phone", ""))
        form.addRow("Τηλέφωνο:", self._ed_org_phone)
        self._ed_org_email = QLineEdit(cfg.get("organization_email", ""))
        form.addRow("Email:", self._ed_org_email)
        self._ed_prefix = QLineEdit(cfg.get("protocol_prefix", ""))
        self._ed_prefix.setPlaceholderText("π.χ. ΑΠ-, ΔΗΜΟΣ-")
        form.addRow("Πρόθεμα Αρ. Πρωτ.:", self._ed_prefix)
        self._chk_year_reset = QCheckBox("Επαναφορά μέτρησης κάθε νέο έτος")
        self._chk_year_reset.setChecked(cfg.get("protocol_year_reset", True))
        form.addRow("", self._chk_year_reset)
        layout.addLayout(form)
        btn_save = QPushButton("Αποθήκευση")
        btn_save.clicked.connect(self._save_org)
        layout.addWidget(btn_save)
        layout.addStretch()
        return w

    def _save_org(self):
        cfg = load_config()
        cfg["organization_name"] = self._ed_org_name.text().strip()
        cfg["organization_address"] = self._ed_org_address.text().strip()
        cfg["organization_phone"] = self._ed_org_phone.text().strip()
        cfg["organization_email"] = self._ed_org_email.text().strip()
        cfg["protocol_prefix"] = self._ed_prefix.text().strip()
        cfg["protocol_year_reset"] = self._chk_year_reset.isChecked()
        save_config(cfg)
        QMessageBox.information(self, "Επιτυχία", "Τα στοιχεία αποθηκεύτηκαν.")

    # ── Generic CRUD table builder ────────────────────────────────────────────

    def _crud_tab(self, columns: list, load_fn, add_fn, edit_fn, delete_fn) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        btn_row = QHBoxLayout()
        btn_add = QPushButton("Προσθήκη")
        btn_add.clicked.connect(lambda: (add_fn(), self._refresh_table(table, load_fn)))
        btn_edit = QPushButton("Επεξεργασία")
        btn_edit.clicked.connect(lambda: (edit_fn(table), self._refresh_table(table, load_fn)))
        btn_del = QPushButton("Διαγραφή")
        btn_del.setProperty("danger", "true")
        btn_del.clicked.connect(lambda: (delete_fn(table), self._refresh_table(table, load_fn)))
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_edit)
        btn_row.addStretch()
        btn_row.addWidget(btn_del)
        layout.addLayout(btn_row)
        table = QTableWidget(0, len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        layout.addWidget(table, 1)
        self._refresh_table(table, load_fn)
        return w

    def _refresh_table(self, table: QTableWidget, load_fn):
        rows = load_fn()
        table.setRowCount(0)
        for row_data in rows:
            r = table.rowCount()
            table.insertRow(r)
            for col, val in enumerate(row_data):
                table.setItem(r, col, QTableWidgetItem(str(val) if val is not None else ""))

    # ── Departments ───────────────────────────────────────────────────────────

    def _build_departments_tab(self) -> QWidget:
        def load():
            return [(d.code, d.name, d.description or "", "Ναι" if d.active else "Όχι")
                    for d in self._session.query(Department).order_by(Department.name).all()]
        def add():
            dlg = SimpleFieldsDialog(
                "Νέο Τμήμα",
                [("Κωδικός *", "code"), ("Όνομα *", "name"), ("Περιγραφή", "desc")],
                self
            )
            if dlg.exec():
                d = Department(code=dlg.values["code"], name=dlg.values["name"],
                                description=dlg.values.get("desc") or None)
                self._session.add(d)
                self._commit()
        def edit(table):
            row = table.currentRow()
            if row < 0:
                return
            code = table.item(row, 0).text()
            d = self._session.query(Department).filter_by(code=code).first()
            if not d:
                return
            dlg = SimpleFieldsDialog(
                "Επεξεργασία Τμήματος",
                [("Κωδικός *", "code"), ("Όνομα *", "name"), ("Περιγραφή", "desc")],
                self,
                defaults={"code": d.code, "name": d.name, "desc": d.description or ""},
            )
            if dlg.exec():
                d.code = dlg.values["code"]
                d.name = dlg.values["name"]
                d.description = dlg.values.get("desc") or None
                self._commit()
        def delete(table):
            row = table.currentRow()
            if row < 0:
                return
            if ConfirmDialog.ask(self, "Διαγραφή", "Να διαγραφεί το τμήμα;"):
                code = table.item(row, 0).text()
                d = self._session.query(Department).filter_by(code=code).first()
                if d:
                    d.active = False
                    self._commit()
        return self._crud_tab(["Κωδικός", "Όνομα", "Περιγραφή", "Ενεργό"], load, add, edit, delete)

    # ── Job Positions ─────────────────────────────────────────────────────────

    def _build_positions_tab(self) -> QWidget:
        def load():
            return [(p.code, p.name, "Ναι" if p.active else "Όχι")
                    for p in self._session.query(JobPosition).order_by(JobPosition.name).all()]
        def add():
            dlg = SimpleFieldsDialog("Νέα Θέση", [("Κωδικός *", "code"), ("Όνομα *", "name")], self)
            if dlg.exec():
                self._session.add(JobPosition(code=dlg.values["code"], name=dlg.values["name"]))
                self._commit()
        def edit(table):
            row = table.currentRow()
            if row < 0:
                return
            code = table.item(row, 0).text()
            p = self._session.query(JobPosition).filter_by(code=code).first()
            if not p:
                return
            dlg = SimpleFieldsDialog("Επεξεργασία Θέσης",
                                      [("Κωδικός *", "code"), ("Όνομα *", "name")], self,
                                      defaults={"code": p.code, "name": p.name})
            if dlg.exec():
                p.code = dlg.values["code"]
                p.name = dlg.values["name"]
                self._commit()
        def delete(table):
            row = table.currentRow()
            if row < 0:
                return
            if ConfirmDialog.ask(self, "Διαγραφή", "Να διαγραφεί η θέση;"):
                code = table.item(row, 0).text()
                p = self._session.query(JobPosition).filter_by(code=code).first()
                if p:
                    p.active = False
                    self._commit()
        return self._crud_tab(["Κωδικός", "Όνομα", "Ενεργό"], load, add, edit, delete)

    # ── Employees ─────────────────────────────────────────────────────────────

    def _build_employees_tab(self) -> QWidget:
        def load():
            return [(e.code or "", e.last_name, e.first_name,
                     e.department.name if e.department else "",
                     e.position.name if e.position else "",
                     e.email or "", "Ναι" if e.active else "Όχι")
                    for e in self._session.query(Employee).order_by(Employee.last_name).all()]
        def add():
            from ui.employee_dialog import EmployeeDialog
            dlg = EmployeeDialog(self._session, parent=self)
            if dlg.exec():
                self._commit()
        def edit(table):
            row = table.currentRow()
            if row < 0:
                return
            code = table.item(row, 0).text()
            emp = self._session.query(Employee).filter_by(code=code).first()
            if emp:
                from ui.employee_dialog import EmployeeDialog
                dlg = EmployeeDialog(self._session, emp.id, parent=self)
                if dlg.exec():
                    self._commit()
        def delete(table):
            row = table.currentRow()
            if row < 0:
                return
            if ConfirmDialog.ask(self, "Διαγραφή", "Να απενεργοποιηθεί ο υπάλληλος;"):
                code = table.item(row, 0).text()
                emp = self._session.query(Employee).filter_by(code=code).first()
                if emp:
                    emp.active = False
                    self._commit()
        return self._crud_tab(
            ["Κωδικός", "Επώνυμο", "Όνομα", "Τμήμα", "Θέση", "Email", "Ενεργός"],
            load, add, edit, delete
        )

    # ── Contacts ──────────────────────────────────────────────────────────────

    def _build_contacts_tab(self) -> QWidget:
        # Κρατάμε αντιστοίχηση γραμμής → contact.id για αξιόπιστη αναζήτηση
        _contact_ids: list = []

        def load():
            _contact_ids.clear()
            rows = []
            for c in self._session.query(Contact).filter_by(active=True).order_by(Contact.name).all():
                _contact_ids.append(c.id)
                rows.append((c.name, c.organization or "", c.contact_type or "",
                              c.phone or "", c.email or ""))
            return rows

        def add():
            from ui.dialogs import ContactDialog
            dlg = ContactDialog(self._session, parent=self)
            dlg.exec()
            # Ανανέωση πίνακα γίνεται από το _crud_tab μέσω lambda

        def edit(table):
            row = table.currentRow()
            if row < 0:
                QMessageBox.information(self, "Επεξεργασία", "Επιλέξτε πρώτα μια επαφή.")
                return
            if row >= len(_contact_ids):
                return
            from ui.dialogs import ContactDialog
            dlg = ContactDialog(self._session, _contact_ids[row], parent=self)
            dlg.exec()

        def delete(table):
            row = table.currentRow()
            if row < 0:
                return
            if row >= len(_contact_ids):
                return
            name = table.item(row, 0).text()
            if ConfirmDialog.ask(self, "Διαγραφή", f"Να διαγραφεί η επαφή «{name}»;"):
                c = self._session.get(Contact, _contact_ids[row])
                if c:
                    c.active = False
                    self._commit()

        return self._crud_tab(["Όνομα", "Οργανισμός", "Τύπος", "Τηλέφωνο", "Email"],
                               load, add, edit, delete)

    # ── Recipient lists ───────────────────────────────────────────────────────

    def _build_recipient_lists_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(QLabel("Πίνακες αποδεκτών για μαζική αποστολή εγγράφων."))
        btn_row = QHBoxLayout()
        btn_add = QPushButton("Νέος Πίνακας")
        btn_add.clicked.connect(self._add_recipient_list)
        btn_row.addWidget(btn_add)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self._rl_list = QListWidget()
        self._rl_list.itemDoubleClicked.connect(self._edit_recipient_list)
        layout.addWidget(self._rl_list, 1)
        self._reload_recipient_lists()
        return w

    def _reload_recipient_lists(self):
        self._rl_list.clear()
        for rl in self._session.query(RecipientList).order_by(RecipientList.name).all():
            item = QListWidgetItem(f"{rl.name} ({len(rl.members)} μέλη)")
            item.setData(Qt.ItemDataRole.UserRole, rl.id)
            self._rl_list.addItem(item)

    def _add_recipient_list(self):
        dlg = RecipientListEditDialog(self._session, parent=self)
        if dlg.exec():
            self._reload_recipient_lists()

    def _edit_recipient_list(self, item):
        rl_id = item.data(Qt.ItemDataRole.UserRole)
        dlg = RecipientListEditDialog(self._session, rl_id, parent=self)
        if dlg.exec():
            self._reload_recipient_lists()

    # ── Folders ───────────────────────────────────────────────────────────────

    def _build_folders_tab(self) -> QWidget:
        def load():
            result = []
            for f in self._session.query(FileFolder).filter_by(parent_id=None).order_by(FileFolder.name).all():
                result.append((f.code or "", f.name, "", "Ναι" if f.active else "Όχι"))
                for ch in f.children:
                    result.append((ch.code or "", f"  └ {ch.name}", f.name, "Ναι" if ch.active else "Όχι"))
            return result
        def add():
            dlg = SimpleFieldsDialog("Νέος Φάκελος",
                [("Κωδικός", "code"), ("Όνομα *", "name"), ("Περιγραφή", "desc")], self)
            if dlg.exec():
                self._session.add(FileFolder(code=dlg.values.get("code") or None,
                                              name=dlg.values["name"],
                                              description=dlg.values.get("desc") or None))
                self._commit()
        def edit(table): pass
        def delete(table):
            row = table.currentRow()
            if row < 0:
                return
            if ConfirmDialog.ask(self, "Διαγραφή", "Να απενεργοποιηθεί ο φάκελος;"):
                code = table.item(row, 0).text()
                f = self._session.query(FileFolder).filter_by(code=code).first()
                if f:
                    f.active = False
                    self._commit()
        return self._crud_tab(["Κωδικός", "Όνομα", "Γονικός", "Ενεργός"], load, add, edit, delete)

    # ── Themes ────────────────────────────────────────────────────────────────

    def _build_themes_tab(self) -> QWidget:
        def load():
            return [(t.code or "", t.name, t.description or "", "Ναι" if t.active else "Όχι")
                    for t in self._session.query(DocumentTheme).order_by(
                        DocumentTheme.code, DocumentTheme.name).all()]
        def add():
            dlg = SimpleFieldsDialog(
                "Νέο Θέμα",
                [("Κωδικός", "code"), ("Όνομα *", "name"), ("Περιγραφή", "description")],
                self,
            )
            if dlg.exec():
                self._session.add(DocumentTheme(
                    code=dlg.values.get("code") or None,
                    name=dlg.values["name"],
                    description=dlg.values.get("description") or None,
                ))
                self._commit()
        def edit(table):
            row = table.currentRow()
            if row < 0:
                QMessageBox.information(self, "Επεξεργασία", "Επιλέξτε πρώτα ένα θέμα από τη λίστα.")
                return
            old_name = table.item(row, 1).text().strip()
            t = self._session.query(DocumentTheme).filter_by(name=old_name).first()
            if not t:
                return
            dlg = SimpleFieldsDialog(
                "Επεξεργασία Θέματος",
                [("Κωδικός", "code"), ("Όνομα *", "name"), ("Περιγραφή", "description")],
                self,
                defaults={
                    "code": t.code or "",
                    "name": t.name,
                    "description": t.description or "",
                },
            )
            if dlg.exec():
                t.code = dlg.values.get("code") or None
                t.name = dlg.values["name"]
                t.description = dlg.values.get("description") or None
                self._commit()
        def delete(table):
            row = table.currentRow()
            if row < 0:
                return
            name = table.item(row, 1).text().strip()
            if ConfirmDialog.ask(self, "Διαγραφή", f"Να διαγραφεί το θέμα «{name}»;"):
                t = self._session.query(DocumentTheme).filter_by(name=name).first()
                if t:
                    t.active = False
                    self._commit()
        return self._crud_tab(["Κωδικός", "Όνομα", "Περιγραφή", "Ενεργό"], load, add, edit, delete)

    # ── Document types ────────────────────────────────────────────────────────

    def _build_doc_types_tab(self) -> QWidget:
        def load():
            return [(t.code or "", t.name, t.direction or "", "Ναι" if t.active else "Όχι")
                    for t in self._session.query(DocumentType).order_by(DocumentType.name).all()]
        def add():
            dlg = SimpleFieldsDialog("Νέο Είδος", [
                ("Κωδικός", "code"), ("Όνομα *", "name"),
                ("Κατεύθυνση (INCOMING/OUTGOING/BOTH)", "direction"),
            ], self)
            if dlg.exec():
                self._session.add(DocumentType(
                    code=dlg.values.get("code") or None,
                    name=dlg.values["name"],
                    direction=dlg.values.get("direction") or "BOTH",
                ))
                self._commit()
        def edit(table): pass
        def delete(table):
            row = table.currentRow()
            if row < 0:
                return
            if ConfirmDialog.ask(self, "Διαγραφή", "Να διαγραφεί το είδος;"):
                name = table.item(row, 1).text().strip()
                t = self._session.query(DocumentType).filter_by(name=name).first()
                if t:
                    t.active = False
                    self._commit()
        return self._crud_tab(["Κωδικός", "Όνομα", "Κατεύθυνση", "Ενεργό"], load, add, edit, delete)

    # ── Email / SMTP ──────────────────────────────────────────────────────────

    def _build_email_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        cfg = load_config()
        form = QFormLayout()
        form.setSpacing(10)
        self._ed_smtp_host = QLineEdit(cfg.get("smtp_host", ""))
        form.addRow("SMTP Host:", self._ed_smtp_host)
        self._ed_smtp_port = QLineEdit(str(cfg.get("smtp_port", 587)))
        form.addRow("SMTP Port:", self._ed_smtp_port)
        self._ed_smtp_user = QLineEdit(cfg.get("smtp_user", ""))
        form.addRow("Username:", self._ed_smtp_user)
        self._ed_smtp_pass = QLineEdit(cfg.get("smtp_password", ""))
        self._ed_smtp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self._ed_smtp_pass)
        self._chk_tls = QCheckBox("Χρήση TLS")
        self._chk_tls.setChecked(cfg.get("smtp_use_tls", True))
        form.addRow("", self._chk_tls)
        layout.addLayout(form)
        btn_row = QHBoxLayout()
        btn_test = QPushButton("Δοκιμαστικό Email")
        btn_test.clicked.connect(self._test_email)
        btn_save = QPushButton("Αποθήκευση")
        btn_save.clicked.connect(self._save_email)
        btn_row.addWidget(btn_test)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)
        layout.addStretch()
        return w

    def _save_email(self):
        cfg = load_config()
        cfg["smtp_host"] = self._ed_smtp_host.text().strip()
        cfg["smtp_port"] = int(self._ed_smtp_port.text().strip() or 587)
        cfg["smtp_user"] = self._ed_smtp_user.text().strip()
        cfg["smtp_password"] = self._ed_smtp_pass.text()
        cfg["smtp_use_tls"] = self._chk_tls.isChecked()
        save_config(cfg)
        QMessageBox.information(self, "Επιτυχία", "Ρυθμίσεις SMTP αποθηκεύτηκαν.")

    def _test_email(self):
        from services.email_service import send_email
        cfg = load_config()
        user = cfg.get("smtp_user", "").strip()
        if not user:
            QMessageBox.warning(self, "Σφάλμα", "Συμπληρώστε πρώτα το Username (email αποστολέα).")
            return
        ok, msg = send_email(
            cfg,
            to=[user],
            subject="✅ Δοκιμαστικό Email – Σύστημα Πρωτοκόλλου",
            body=(
                "Αυτό είναι ένα δοκιμαστικό email από το Σύστημα Πρωτοκόλλου.\n\n"
                "Αν το λαμβάνετε, οι ρυθμίσεις SMTP είναι σωστές."
            ),
        )
        if ok:
            QMessageBox.information(
                self, "Επιτυχία",
                f"Δοκιμαστικό email στάλθηκε επιτυχώς στο:\n{user}"
            )
        else:
            QMessageBox.warning(self, "Αποτυχία", f"Αδυναμία αποστολής:\n{msg}")

    # ── Αρχειοθέτηση Εγγράφων ─────────────────────────────────────────────────

    def _build_archive_tab(self) -> QWidget:
        from PyQt6.QtWidgets import QFileDialog, QGroupBox
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        cfg = load_config()

        g = QGroupBox("Ρυθμίσεις Αρχειοθέτησης")
        gv = QVBoxLayout(g)
        gv.setSpacing(10)

        info = QLabel(
            "Όταν είναι ενεργοποιημένη, για κάθε αριθμό πρωτοκόλλου δημιουργείται\n"
            "αυτόματα φάκελος με το όνομα του αρ. πρωτ. και μέσα αποθηκεύονται\n"
            "όλα τα συνημμένα έγγραφα. Υποστηρίζεται τοπικός δίσκος ή διαδρομή\n"
            "δικτύου/Server (π.χ. \\\\Server\\Share\\Πρωτόκολλο)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#4a5568; font-size:11px;")
        gv.addWidget(info)

        self._chk_archive = QCheckBox("Ενεργοποίηση αυτόματης αρχειοθέτησης εγγράφων")
        self._chk_archive.setChecked(cfg.get("archive_enabled", False))
        gv.addWidget(self._chk_archive)

        form = QFormLayout()
        form.setSpacing(8)

        path_row = QHBoxLayout()
        self._ed_archive_path = QLineEdit(cfg.get("archive_path", ""))
        self._ed_archive_path.setPlaceholderText(
            r"π.χ. C:\Αρχείο\Πρωτόκολλο  ή  \\Server\Share\Πρωτόκολλο"
        )
        path_row.addWidget(self._ed_archive_path)
        btn_browse = QPushButton("Αναζήτηση...")
        btn_browse.setMaximumWidth(110)
        btn_browse.clicked.connect(self._browse_archive_path)
        path_row.addWidget(btn_browse)
        form.addRow("Διαδρομή αρχειοθέτησης:", path_row)

        gv.addLayout(form)
        layout.addWidget(g)

        btn_save = QPushButton("Αποθήκευση")
        btn_save.clicked.connect(self._save_archive)
        btn_test = QPushButton("Δοκιμή Διαδρομής")
        btn_test.clicked.connect(self._test_archive_path)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_test)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)
        layout.addStretch()
        return w

    def _browse_archive_path(self):
        from PyQt6.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self, "Επιλογή φακέλου αρχειοθέτησης",
                                                 self._ed_archive_path.text() or "")
        if path:
            self._ed_archive_path.setText(path)

    def _save_archive(self):
        cfg = load_config()
        cfg["archive_enabled"] = self._chk_archive.isChecked()
        cfg["archive_path"] = self._ed_archive_path.text().strip()
        save_config(cfg)
        QMessageBox.information(self, "Επιτυχία", "Ρυθμίσεις αρχειοθέτησης αποθηκεύτηκαν.")

    def _test_archive_path(self):
        import os
        path = self._ed_archive_path.text().strip()
        if not path:
            QMessageBox.warning(self, "Προσοχή", "Δεν έχει οριστεί διαδρομή.")
            return
        if os.path.isdir(path):
            QMessageBox.information(self, "Επιτυχία",
                                    f"Η διαδρομή υπάρχει και είναι προσβάσιμη:\n{path}")
        else:
            from PyQt6.QtWidgets import QMessageBox as MB
            reply = MB.question(self, "Δεν υπάρχει",
                                f"Η διαδρομή δεν υπάρχει:\n{path}\n\nΝα δημιουργηθεί;",
                                MB.StandardButton.Yes | MB.StandardButton.No)
            if reply == MB.StandardButton.Yes:
                try:
                    os.makedirs(path, exist_ok=True)
                    QMessageBox.information(self, "Επιτυχία", f"Ο φάκελος δημιουργήθηκε:\n{path}")
                except Exception as ex:
                    QMessageBox.critical(self, "Σφάλμα", f"Αδυναμία δημιουργίας:\n{ex}")

    def _commit(self):
        try:
            self._session.commit()
        except Exception as ex:
            self._session.rollback()
            QMessageBox.critical(self, "Σφάλμα", str(ex))


# ── Helper dialogs ────────────────────────────────────────────────────────────

class SimpleFieldsDialog(QDialog):
    """Generic form dialog with text fields."""
    def __init__(self, title: str, fields: list, parent=None, defaults: dict = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.values: dict = {}
        self._fields = fields
        self._edits: dict = {}
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(8)
        for label, key in fields:
            ed = QLineEdit()
            ed.setText(defaults.get(key, "") if defaults else "")
            form.addRow(label + ":", ed)
            self._edits[key] = ed
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("Αποθήκευση")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Ακύρωση")
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _on_ok(self):
        # Validate required fields (marked with *)
        for label, key in self._fields:
            if "*" in label and not self._edits[key].text().strip():
                QMessageBox.warning(self, "Σφάλμα", f"Το πεδίο '{label.replace(' *','')}' είναι υποχρεωτικό.")
                return
        self.values = {key: self._edits[key].text().strip() for _, key in self._fields}
        self.accept()


class RecipientListEditDialog(QDialog):
    """Create/edit a recipient distribution list."""
    def __init__(self, session, rl_id=None, parent=None):
        super().__init__(parent)
        self._session = session
        self._rl_id = rl_id
        self.setWindowTitle("Πίνακας Αποδεκτών")
        self.setMinimumSize(500, 400)
        self._build_ui()
        if rl_id:
            self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._ed_name = QLineEdit()
        form.addRow("Όνομα *:", self._ed_name)
        self._ed_desc = QLineEdit()
        form.addRow("Περιγραφή:", self._ed_desc)
        layout.addLayout(form)

        # Member selection
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.addWidget(QLabel("Διαθέσιμες Επαφές:"))
        self._all_contacts = QListWidget()
        contacts = self._session.query(Contact).filter_by(active=True).order_by(Contact.name).all()
        for c in contacts:
            item = QListWidgetItem(c.display_name)
            item.setData(Qt.ItemDataRole.UserRole, c.id)
            self._all_contacts.addItem(item)
        lv.addWidget(self._all_contacts, 1)
        btn_add = QPushButton("Προσθήκη >>")
        btn_add.clicked.connect(self._add_member)
        lv.addWidget(btn_add)
        splitter.addWidget(left)

        right = QWidget()
        rv = QVBoxLayout(right)
        rv.addWidget(QLabel("Μέλη Πίνακα:"))
        self._members = QListWidget()
        rv.addWidget(self._members, 1)
        btn_rem = QPushButton("<< Αφαίρεση")
        btn_rem.clicked.connect(self._remove_member)
        rv.addWidget(btn_rem)
        splitter.addWidget(right)
        layout.addWidget(splitter, 1)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("Αποθήκευση")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Ακύρωση")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load(self):
        rl = self._session.get(RecipientList, self._rl_id)
        if not rl:
            return
        self._ed_name.setText(rl.name)
        self._ed_desc.setText(rl.description or "")
        for m in rl.members:
            item = QListWidgetItem(m.display_name)
            item.setData(Qt.ItemDataRole.UserRole, m.id)
            self._members.addItem(item)

    def _add_member(self):
        item = self._all_contacts.currentItem()
        if item:
            new_item = QListWidgetItem(item.text())
            new_item.setData(Qt.ItemDataRole.UserRole, item.data(Qt.ItemDataRole.UserRole))
            self._members.addItem(new_item)

    def _remove_member(self):
        row = self._members.currentRow()
        if row >= 0:
            self._members.takeItem(row)

    def _save(self):
        name = self._ed_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Σφάλμα", "Το όνομα είναι υποχρεωτικό.")
            return
        if self._rl_id:
            rl = self._session.get(RecipientList, self._rl_id)
        else:
            rl = RecipientList()
            self._session.add(rl)
        rl.name = name
        rl.description = self._ed_desc.text().strip() or None
        rl.members.clear()
        for i in range(self._members.count()):
            cid = self._members.item(i).data(Qt.ItemDataRole.UserRole)
            c = self._session.get(Contact, cid)
            if c:
                rl.members.append(c)
        try:
            self._session.commit()
            self.accept()
        except Exception as ex:
            self._session.rollback()
            QMessageBox.critical(self, "Σφάλμα", str(ex))
