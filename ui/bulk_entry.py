"""Μαζική Καταχώρηση Πρωτοκόλλου — Bulk Protocol Entry Panel."""
from __future__ import annotations
import csv
import io
from datetime import date, datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QComboBox, QDateEdit, QLineEdit, QHeaderView,
    QMessageBox, QFileDialog, QAbstractItemView, QDialog,
    QDialogButtonBox, QFormLayout, QGroupBox, QProgressBar,
    QCheckBox, QApplication,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from database.models import (
    DocumentDirection, DocumentPriority, ProcessingStatus, RegistryType,
)
from ui.widgets import SectionHeader


# ── Column constants ───────────────────────────────────────────────────────────
_COL_DIR      = 0   # Κατεύθυνση
_COL_DATE     = 1   # Ημερομηνία
_COL_SUBJECT  = 2   # Θέμα *
_COL_SENDER   = 3   # Αποστολέας
_COL_EXT_NUM  = 4   # Αρ. Πρωτ. Αποστολέα
_COL_PRIORITY = 5   # Προτεραιότητα
_COL_STATUS   = 6   # Κατάσταση
_COL_SUMMARY  = 7   # Περίληψη / Σημειώσεις

_HEADERS = [
    "Κατεύθυνση *", "Ημερομηνία *", "Θέμα *",
    "Αποστολέας", "Αρ. Πρωτ. Αποστολέα",
    "Προτεραιότητα", "Κατάσταση", "Περίληψη",
]

_DIRECTIONS  = [d.value for d in DocumentDirection]
_PRIORITIES  = [p.value for p in DocumentPriority]
_STATUSES    = [s.value for s in ProcessingStatus]
_DIR_DEFAULT = DocumentDirection.INCOMING.value
_PRI_DEFAULT = DocumentPriority.NORMAL.value
_STA_DEFAULT = ProcessingStatus.RECEIVED.value

_DIR_COLORS = {
    DocumentDirection.INCOMING.value: QColor("#e6fffa"),
    DocumentDirection.OUTGOING.value: QColor("#ebf8ff"),
    DocumentDirection.INTERNAL.value: QColor("#fffff0"),
}


def _today_str() -> str:
    return date.today().strftime("%d/%m/%Y")


def _parse_date(txt: str) -> Optional[date]:
    """Try multiple date formats; return None on failure."""
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(txt.strip(), fmt).date()
        except ValueError:
            continue
    return None


class BulkEntryPanel(QWidget):
    """Panel for fast batch protocol registration and Excel/CSV import."""

    saved = pyqtSignal(int)   # emitted with count of saved protocols

    def __init__(self, registry_type: RegistryType = RegistryType.GENERAL, parent=None):
        super().__init__(parent)
        self._registry_type = registry_type
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)
        root.addWidget(SectionHeader("Μαζική Καταχώρηση Πρωτοκόλλου"))

        # Info label
        info = QLabel(
            "Συμπληρώστε πολλές γραμμές ταυτόχρονα. "
            "Τα πεδία με * είναι υποχρεωτικά. "
            "Enter = μετάβαση στην επόμενη γραμμή ίδιας στήλης."
        )
        info.setStyleSheet("color:#4a5568; font-size:11px;")
        root.addWidget(info)

        tabs = QTabWidget()
        tabs.addTab(self._build_grid_tab(), "📝  Γρήγορη Καταχώρηση")
        tabs.addTab(self._build_import_tab(), "📂  Εισαγωγή από Excel / CSV")
        root.addWidget(tabs, 1)

    # ── Tab 1 : grid entry ─────────────────────────────────────────────────────

    def _build_grid_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Toolbar row
        top = QHBoxLayout()

        # Registry type selector
        top.addWidget(QLabel("Βιβλίο:"))
        self._cb_registry = QComboBox()
        for rt in RegistryType:
            self._cb_registry.addItem(rt.value, rt)
        # pre-select active registry
        for i in range(self._cb_registry.count()):
            if self._cb_registry.itemData(i) == self._registry_type:
                self._cb_registry.setCurrentIndex(i)
                break
        self._cb_registry.setMinimumWidth(180)
        top.addWidget(self._cb_registry)
        top.addSpacing(20)

        btn_add = QPushButton("➕  Νέα Γραμμή")
        btn_add.clicked.connect(self._add_row)
        btn_del = QPushButton("🗑  Διαγραφή Γραμμής")
        btn_del.clicked.connect(self._remove_row)
        btn_del.setProperty("danger", "true")
        btn_clear = QPushButton("🧹  Εκκαθάριση Όλων")
        btn_clear.clicked.connect(self._clear_all)

        for b in (btn_add, btn_del, btn_clear):
            top.addWidget(b)
        top.addStretch()

        # Row counter
        self._lbl_count = QLabel("Γραμμές: 0")
        self._lbl_count.setStyleSheet("color:#718096; font-size:11px;")
        top.addWidget(self._lbl_count)

        layout.addLayout(top)

        # Grid table
        self._table = QTableWidget(0, len(_HEADERS))
        self._table.setHorizontalHeaderLabels(_HEADERS)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(_COL_SUBJECT, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(_COL_SUMMARY, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(_COL_SENDER,  QHeaderView.ResizeMode.ResizeToContents)
        for col in (_COL_DIR, _COL_DATE, _COL_EXT_NUM, _COL_PRIORITY, _COL_STATUS):
            hh.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(False)
        self._table.verticalHeader().setDefaultSectionSize(30)
        self._table.setStyleSheet(
            "QTableWidget { font-size: 12px; }"
            "QTableWidget::item:selected { background:#bee3f8; color:#1a202c; }"
        )
        # Start with 5 empty rows
        for _ in range(5):
            self._append_row()

        layout.addWidget(self._table, 1)

        # Progress bar (hidden by default)
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(True)
        layout.addWidget(self._progress)

        # Save button row
        bot = QHBoxLayout()
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("font-size:12px;")
        bot.addWidget(self._lbl_status)
        bot.addStretch()

        btn_template = QPushButton("📥  Λήψη Πρότυπου Excel")
        btn_template.setToolTip("Κατεβάστε πρότυπο Excel για συμπλήρωση και εισαγωγή")
        btn_template.clicked.connect(self._export_template)

        btn_save = QPushButton("💾  Αποθήκευση Όλων")
        btn_save.setStyleSheet(
            "QPushButton{background:#276749;color:white;padding:9px 24px;"
            "border-radius:6px;font-size:13px;font-weight:bold;}"
            "QPushButton:hover{background:#2f855a;}"
        )
        btn_save.clicked.connect(self._save_all)
        bot.addWidget(btn_template)
        bot.addWidget(btn_save)
        layout.addLayout(bot)
        return w

    def _append_row(self, data: dict | None = None):
        """Append one editable row to the grid."""
        r = self._table.rowCount()
        self._table.insertRow(r)

        # Direction combo
        cb_dir = QComboBox()
        for d in _DIRECTIONS:
            cb_dir.addItem(d)
        cb_dir.setCurrentText(data.get("direction", _DIR_DEFAULT) if data else _DIR_DEFAULT)
        cb_dir.currentTextChanged.connect(lambda _, row=r: self._color_row(row))
        self._table.setCellWidget(r, _COL_DIR, cb_dir)

        # Date edit
        de = QDateEdit()
        de.setDisplayFormat("dd/MM/yyyy")
        de.setCalendarPopup(True)
        proto_date = data.get("date") if data else None
        if isinstance(proto_date, date):
            de.setDate(QDate(proto_date.year, proto_date.month, proto_date.day))
        else:
            de.setDate(QDate.currentDate())
        self._table.setCellWidget(r, _COL_DATE, de)

        # Subject
        subj = QTableWidgetItem(data.get("subject", "") if data else "")
        self._table.setItem(r, _COL_SUBJECT, subj)

        # Sender
        sender = QTableWidgetItem(data.get("sender", "") if data else "")
        self._table.setItem(r, _COL_SENDER, sender)

        # Ext protocol number
        ext = QTableWidgetItem(data.get("ext_protocol_number", "") if data else "")
        self._table.setItem(r, _COL_EXT_NUM, ext)

        # Priority combo
        cb_pri = QComboBox()
        for p in _PRIORITIES:
            cb_pri.addItem(p)
        cb_pri.setCurrentText(data.get("priority", _PRI_DEFAULT) if data else _PRI_DEFAULT)
        self._table.setCellWidget(r, _COL_PRIORITY, cb_pri)

        # Status combo
        cb_sta = QComboBox()
        for s in _STATUSES:
            cb_sta.addItem(s)
        cb_sta.setCurrentText(data.get("status", _STA_DEFAULT) if data else _STA_DEFAULT)
        self._table.setCellWidget(r, _COL_STATUS, cb_sta)

        # Summary
        summ = QTableWidgetItem(data.get("summary", "") if data else "")
        self._table.setItem(r, _COL_SUMMARY, summ)

        self._color_row(r)
        self._update_count()

    def _color_row(self, row: int):
        """Color a row based on selected direction."""
        widget = self._table.cellWidget(row, _COL_DIR)
        if not widget:
            return
        direction = widget.currentText()
        color = _DIR_COLORS.get(direction, QColor("white"))
        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item:
                item.setBackground(color)
            w = self._table.cellWidget(row, col)
            if w and not isinstance(w, QComboBox):
                w.setStyleSheet(f"background:{color.name()};")

    def _add_row(self):
        self._append_row()
        self._table.scrollToBottom()
        # Focus on subject of new row
        new_row = self._table.rowCount() - 1
        self._table.setCurrentCell(new_row, _COL_SUBJECT)

    def _remove_row(self):
        row = self._table.currentRow()
        if row >= 0:
            self._table.removeRow(row)
            self._update_count()

    def _clear_all(self):
        if self._table.rowCount() == 0:
            return
        reply = QMessageBox.question(
            self, "Εκκαθάριση",
            "Να διαγραφούν όλες οι γραμμές;",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._table.setRowCount(0)
            self._update_count()
            self._lbl_status.setText("")

    def _update_count(self):
        self._lbl_count.setText(f"Γραμμές: {self._table.rowCount()}")

    def _collect_rows(self) -> list[dict]:
        """Read all non-empty rows from the grid."""
        rows = []
        for r in range(self._table.rowCount()):
            subj_item = self._table.item(r, _COL_SUBJECT)
            subject   = subj_item.text().strip() if subj_item else ""
            if not subject:
                continue  # skip blank rows

            date_widget = self._table.cellWidget(r, _COL_DATE)
            qd = date_widget.date() if date_widget else QDate.currentDate()
            proto_date = date(qd.year(), qd.month(), qd.day())

            dir_widget = self._table.cellWidget(r, _COL_DIR)
            direction  = dir_widget.currentText() if dir_widget else _DIR_DEFAULT

            sender_item = self._table.item(r, _COL_SENDER)
            sender      = sender_item.text().strip() if sender_item else ""

            ext_item = self._table.item(r, _COL_EXT_NUM)
            ext_num  = ext_item.text().strip() if ext_item else ""

            pri_widget = self._table.cellWidget(r, _COL_PRIORITY)
            priority   = pri_widget.currentText() if pri_widget else _PRI_DEFAULT

            sta_widget = self._table.cellWidget(r, _COL_STATUS)
            status     = sta_widget.currentText() if sta_widget else _STA_DEFAULT

            summ_item = self._table.item(r, _COL_SUMMARY)
            summary   = summ_item.text().strip() if summ_item else ""

            rows.append(dict(
                direction=direction,
                date=proto_date,
                subject=subject,
                sender_name=sender,
                ext_protocol_number=ext_num,
                priority=priority,
                status=status,
                summary=summary,
                row_index=r,
            ))
        return rows

    def _save_all(self):
        from database.db import get_session, create_protocol, next_protocol_number
        from database.models import (
            DocumentDirection, DocumentPriority, ProcessingStatus,
            RegistryType, Contact,
        )
        from config.settings import load_config

        rows = self._collect_rows()
        if not rows:
            QMessageBox.warning(self, "Κενό", "Δεν υπάρχουν γραμμές για αποθήκευση.\n"
                                "Συμπληρώστε τουλάχιστον το πεδίο «Θέμα».")
            return

        registry_type = self._cb_registry.currentData()
        config = load_config()
        prefix = config.get("protocol_prefix", "")

        # Build lookup maps for enums
        dir_map = {d.value: d for d in DocumentDirection}
        pri_map = {p.value: p for p in DocumentPriority}
        sta_map = {s.value: s for s in ProcessingStatus}

        session = get_session()
        saved = 0
        errors = []

        self._progress.setVisible(True)
        self._progress.setMaximum(len(rows))
        self._progress.setValue(0)
        QApplication.processEvents()

        try:
            for i, row in enumerate(rows):
                try:
                    direction = dir_map.get(row["direction"], DocumentDirection.INCOMING)
                    priority  = pri_map.get(row["priority"],  DocumentPriority.NORMAL)
                    status    = sta_map.get(row["status"],    ProcessingStatus.RECEIVED)

                    kwargs = dict(
                        registry_type=registry_type,
                        prefix=prefix,
                        priority=priority,
                        status=status,
                    )
                    if row["summary"]:
                        kwargs["summary"] = row["summary"]
                    if row["ext_protocol_number"]:
                        kwargs["ext_protocol_number"] = row["ext_protocol_number"]

                    # Try to find sender contact by name
                    if row["sender_name"]:
                        contact = session.query(Contact).filter(
                            Contact.name.ilike(f"%{row['sender_name']}%")
                        ).first()
                        if contact:
                            kwargs["sender_contact_id"] = contact.id

                    proto = create_protocol(
                        session,
                        direction=direction,
                        subject=row["subject"],
                        protocol_date=row["date"],
                        **kwargs,
                    )
                    saved += 1
                    # Mark row green
                    self._mark_row_saved(row["row_index"])
                except Exception as ex:
                    errors.append(f"Γραμμή {row['row_index']+1}: {ex}")
                    self._mark_row_error(row["row_index"])

                self._progress.setValue(i + 1)
                QApplication.processEvents()

            if saved > 0:
                session.commit()
                self.saved.emit(saved)
                msg = f"✅  Αποθηκεύτηκαν {saved} πρωτόκολλο/α επιτυχώς."
                if errors:
                    msg += f"\n⚠️  {len(errors)} σφάλμα/τα."
                self._lbl_status.setText(msg)
                self._lbl_status.setStyleSheet("color:#276749; font-size:12px; font-weight:bold;")
                QMessageBox.information(
                    self, "Αποτέλεσμα Καταχώρησης",
                    f"Αποθηκεύτηκαν: {saved}\n" +
                    (f"Σφάλματα: {len(errors)}\n\n" + "\n".join(errors[:10]) if errors else "")
                )
            else:
                session.rollback()
                self._lbl_status.setText("❌  Καμία αποθήκευση.")
                self._lbl_status.setStyleSheet("color:#c53030; font-size:12px;")
                if errors:
                    QMessageBox.critical(self, "Σφάλμα", "\n".join(errors[:10]))
        except Exception as ex:
            session.rollback()
            QMessageBox.critical(self, "Σφάλμα", str(ex))
        finally:
            session.close()
            self._progress.setVisible(False)

    def _mark_row_saved(self, row: int):
        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item:
                item.setBackground(QColor("#c6f6d5"))
                item.setForeground(QColor("#22543d"))

    def _mark_row_error(self, row: int):
        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item:
                item.setBackground(QColor("#fed7d7"))
                item.setForeground(QColor("#742a2a"))

    # ── Template export ────────────────────────────────────────────────────────

    def _export_template(self):
        """Save an Excel template with headers and example row."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Αποθήκευση Πρότυπου", "protokolo_template.xlsx",
            "Excel (*.xlsx)"
        )
        if not path:
            return
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
        except ImportError:
            QMessageBox.warning(self, "Σφάλμα", "Απαιτείται openpyxl:\npip install openpyxl")
            return

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Πρωτόκολλο"

        header_fill  = PatternFill("solid", fgColor="1A365D")
        header_font  = Font(color="FFFFFF", bold=True, size=11)
        example_fill = PatternFill("solid", fgColor="EBF8FF")

        col_names = [
            "Κατεύθυνση", "Ημερομηνία (ΗΗ/ΜΜ/ΕΕΕΕ)",
            "Θέμα *", "Αποστολέας", "Αρ.Πρωτ.Αποστολέα",
            "Προτεραιότητα", "Κατάσταση", "Περίληψη",
        ]
        col_widths = [18, 22, 40, 25, 20, 18, 20, 35]

        for ci, (name, width) in enumerate(zip(col_names, col_widths), 1):
            cell = ws.cell(row=1, column=ci, value=name)
            cell.font  = header_font
            cell.fill  = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            ws.column_dimensions[
                openpyxl.utils.get_column_letter(ci)
            ].width = width

        ws.row_dimensions[1].height = 20

        example = [
            "ΕΙΣΕΡΧΟΜΕΝΟ", date.today().strftime("%d/%m/%Y"),
            "Παράδειγμα θέματος", "Υπουργείο ...", "ΑΠ-100/2026",
            "ΚΑΝΟΝΙΚΟ", "ΕΛΛΗΦΘΗ", "Σύντομη περίληψη",
        ]
        for ci, val in enumerate(example, 1):
            cell = ws.cell(row=2, column=ci, value=val)
            cell.fill = example_fill

        # Notes sheet
        ws2 = wb.create_sheet("Οδηγίες")
        ws2["A1"] = "ΤΙΜΕΣ ΠΕΔΙΩΝ"
        ws2["A1"].font = Font(bold=True, size=12)
        ws2["A3"] = "Κατεύθυνση:"
        ws2["B3"] = " | ".join(_DIRECTIONS)
        ws2["A4"] = "Προτεραιότητα:"
        ws2["B4"] = " | ".join(_PRIORITIES)
        ws2["A5"] = "Κατάσταση:"
        ws2["B5"] = " | ".join(_STATUSES)
        ws2["A7"] = "Τα πεδία με * είναι υποχρεωτικά."
        ws2["A8"] = "Ημερομηνία: μορφή ΗΗ/ΜΜ/ΕΕΕΕ (π.χ. 14/03/2026)"
        for c in ws2["A"]:
            if c.value:
                c.font = Font(bold=True)
        ws2.column_dimensions["A"].width = 20
        ws2.column_dimensions["B"].width = 70

        wb.save(path)
        QMessageBox.information(self, "Επιτυχία", f"Πρότυπο αποθηκεύτηκε:\n{path}")

    # ── Tab 2 : Excel / CSV import ─────────────────────────────────────────────

    def _build_import_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        g = QGroupBox("Επιλογή Αρχείου")
        gv = QHBoxLayout(g)
        self._ed_import_path = QLineEdit()
        self._ed_import_path.setReadOnly(True)
        self._ed_import_path.setPlaceholderText("Επιλέξτε αρχείο Excel (.xlsx) ή CSV (.csv)...")
        btn_browse = QPushButton("Αναζήτηση...")
        btn_browse.clicked.connect(self._browse_import)
        btn_load = QPushButton("Φόρτωση Προεπισκόπησης")
        btn_load.setStyleSheet(
            "background:#2b6cb0;color:white;padding:6px 14px;"
            "border-radius:4px;font-weight:bold;"
        )
        btn_load.clicked.connect(self._load_preview)
        gv.addWidget(self._ed_import_path)
        gv.addWidget(btn_browse)
        gv.addWidget(btn_load)
        layout.addWidget(g)

        # Mapping info
        map_info = QLabel(
            "Τα ονόματα στηλών αναγνωρίζονται αυτόματα. "
            "Χρησιμοποιήστε το πρότυπο Excel για σωστή μορφοποίηση."
        )
        map_info.setStyleSheet("color:#4a5568; font-size:11px;")
        layout.addWidget(map_info)

        # Preview table
        self._preview_table = QTableWidget(0, len(_HEADERS))
        self._preview_table.setHorizontalHeaderLabels(_HEADERS)
        self._preview_table.horizontalHeader().setSectionResizeMode(
            _COL_SUBJECT, QHeaderView.ResizeMode.Stretch)
        self._preview_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._preview_table.setAlternatingRowColors(True)
        layout.addWidget(self._preview_table, 1)

        # Import row
        bot = QHBoxLayout()
        self._lbl_import_status = QLabel("")
        self._lbl_import_status.setStyleSheet("font-size:12px;")
        bot.addWidget(self._lbl_import_status)
        bot.addStretch()

        # Registry for import
        bot.addWidget(QLabel("Βιβλίο:"))
        self._cb_import_registry = QComboBox()
        for rt in RegistryType:
            self._cb_import_registry.addItem(rt.value, rt)
        for i in range(self._cb_import_registry.count()):
            if self._cb_import_registry.itemData(i) == self._registry_type:
                self._cb_import_registry.setCurrentIndex(i)
                break
        self._cb_import_registry.setMinimumWidth(160)
        bot.addWidget(self._cb_import_registry)

        btn_import = QPushButton("📥  Εισαγωγή")
        btn_import.setStyleSheet(
            "QPushButton{background:#276749;color:white;padding:9px 24px;"
            "border-radius:6px;font-size:13px;font-weight:bold;}"
            "QPushButton:hover{background:#2f855a;}"
        )
        btn_import.clicked.connect(self._do_import)
        bot.addWidget(btn_import)
        layout.addLayout(bot)

        self._import_data: list[dict] = []
        return w

    def _browse_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Επιλογή αρχείου", "",
            "Υποστηριζόμενα αρχεία (*.xlsx *.xls *.csv);;Excel (*.xlsx *.xls);;CSV (*.csv)"
        )
        if path:
            self._ed_import_path.setText(path)

    def _load_preview(self):
        path = self._ed_import_path.text().strip()
        if not path:
            QMessageBox.warning(self, "Πρόβλημα", "Επιλέξτε αρχείο πρώτα.")
            return
        try:
            if path.lower().endswith(".csv"):
                rows = self._read_csv(path)
            else:
                rows = self._read_excel(path)
        except Exception as ex:
            QMessageBox.critical(self, "Σφάλμα Ανάγνωσης", str(ex))
            return

        self._import_data = rows
        self._preview_table.setRowCount(0)
        for row in rows:
            r = self._preview_table.rowCount()
            self._preview_table.insertRow(r)
            vals = [
                row.get("direction", ""), row.get("date_str", ""),
                row.get("subject", ""), row.get("sender_name", ""),
                row.get("ext_protocol_number", ""),
                row.get("priority", ""), row.get("status", ""),
                row.get("summary", ""),
            ]
            color = _DIR_COLORS.get(row.get("direction", ""), QColor("white"))
            for ci, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setBackground(color)
                self._preview_table.setItem(r, ci, item)

        self._lbl_import_status.setText(f"Φορτώθηκαν {len(rows)} γραμμές.")
        self._lbl_import_status.setStyleSheet("color:#2b6cb0;")

    def _read_excel(self, path: str) -> list[dict]:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows_iter = iter(ws.rows)
        # Read headers from first row
        header_row = next(rows_iter, None)
        if not header_row:
            return []
        headers = [str(c.value or "").strip().lower() for c in header_row]
        return self._parse_rows(headers, rows_iter, is_excel=True)

    def _read_csv(self, path: str) -> list[dict]:
        import csv as csv_mod
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv_mod.DictReader(f)
            rows = []
            for raw in reader:
                rows.append({k.strip().lower(): v.strip() for k, v in raw.items()})
        return [self._normalize_row(r) for r in rows if any(r.values())]

    _HEADER_ALIASES = {
        "direction": ["κατεύθυνση", "direction", "τυπος", "τύπος", "kateuthinsi"],
        "date":      ["ημερομηνία", "ημερ.", "date", "ημερομηνια"],
        "subject":   ["θέμα", "θεμα", "subject", "περιγραφή", "perigrafi"],
        "sender":    ["αποστολέας", "αποστολεας", "sender", "από", "apo"],
        "ext_num":   ["αρ.πρωτ.αποστολέα", "αρ. πρωτ. αποστολέα", "εξωτερικος", "ext_num",
                      "αρ.πρωτ.αποστολεα"],
        "priority":  ["προτεραιότητα", "προτεραιοτητα", "priority"],
        "status":    ["κατάσταση", "κατασταση", "status"],
        "summary":   ["περίληψη", "περιληψη", "σημειώσεις", "σημειωσεις", "summary", "notes"],
    }

    def _find_col_index(self, headers: list[str], field: str) -> int | None:
        aliases = self._HEADER_ALIASES.get(field, [field])
        for alias in aliases:
            alias_l = alias.lower()
            for i, h in enumerate(headers):
                if alias_l in h or h in alias_l:
                    return i
        return None

    def _parse_rows(self, headers: list[str], rows_iter, is_excel: bool) -> list[dict]:
        idx = {f: self._find_col_index(headers, f)
               for f in ("direction", "date", "subject", "sender",
                         "ext_num", "priority", "status", "summary")}
        result = []
        for row in rows_iter:
            def cell(f):
                i = idx.get(f)
                if i is None or i >= len(row):
                    return ""
                val = row[i].value if is_excel else row[i]
                return str(val).strip() if val is not None else ""

            subject = cell("subject")
            if not subject:
                continue

            raw_dir = cell("direction").upper()
            direction = _DIR_DEFAULT
            for d in _DIRECTIONS:
                if raw_dir in d.upper() or d.upper() in raw_dir:
                    direction = d
                    break

            raw_pri = cell("priority").upper()
            priority = _PRI_DEFAULT
            for p in _PRIORITIES:
                if raw_pri in p.upper() or p.upper() in raw_pri:
                    priority = p
                    break

            raw_sta = cell("status").upper()
            status = _STA_DEFAULT
            for s in _STATUSES:
                if raw_sta in s.upper() or s.upper() in raw_sta:
                    status = s
                    break

            date_str = cell("date")
            parsed_date = _parse_date(date_str)
            if parsed_date is None:
                # try Excel serial date
                if is_excel:
                    raw = idx.get("date")
                    if raw is not None and raw < len(row):
                        v = list(row)[raw].value
                        if hasattr(v, "year"):
                            parsed_date = v.date() if hasattr(v, "date") else v
                if parsed_date is None:
                    parsed_date = date.today()

            result.append(dict(
                direction=direction,
                date=parsed_date,
                date_str=parsed_date.strftime("%d/%m/%Y"),
                subject=subject,
                sender_name=cell("sender"),
                ext_protocol_number=cell("ext_num"),
                priority=priority,
                status=status,
                summary=cell("summary"),
            ))
        return result

    def _normalize_row(self, raw: dict) -> dict:
        """Normalize a CSV row dict to standard format."""
        def get(*keys):
            for k in keys:
                for rk in raw:
                    if k.lower() in rk.lower() or rk.lower() in k.lower():
                        return raw[rk].strip()
            return ""

        subject = get("θέμα", "θεμα", "subject")
        if not subject:
            return {}

        raw_dir = get("κατεύθυνση", "direction").upper()
        direction = _DIR_DEFAULT
        for d in _DIRECTIONS:
            if raw_dir in d.upper() or d.upper() in raw_dir:
                direction = d
                break

        raw_pri = get("προτεραιότητα", "priority").upper()
        priority = _PRI_DEFAULT
        for p in _PRIORITIES:
            if raw_pri in p.upper() or p.upper() in raw_pri:
                priority = p
                break

        raw_sta = get("κατάσταση", "status").upper()
        status = _STA_DEFAULT
        for s in _STATUSES:
            if raw_sta in s.upper() or s.upper() in raw_sta:
                status = s
                break

        date_str = get("ημερομηνία", "date")
        parsed_date = _parse_date(date_str) or date.today()

        return dict(
            direction=direction,
            date=parsed_date,
            date_str=parsed_date.strftime("%d/%m/%Y"),
            subject=subject,
            sender_name=get("αποστολέας", "sender"),
            ext_protocol_number=get("αρ.πρωτ", "ext_num"),
            priority=priority,
            status=status,
            summary=get("περίληψη", "summary"),
        )

    def _do_import(self):
        if not self._import_data:
            QMessageBox.warning(self, "Κενό", "Φορτώστε αρχείο πρώτα.")
            return

        registry_type = self._cb_import_registry.currentData()
        from database.db import get_session, create_protocol
        from database.models import (
            DocumentDirection, DocumentPriority, ProcessingStatus, Contact,
        )
        from config.settings import load_config

        dir_map = {d.value: d for d in DocumentDirection}
        pri_map = {p.value: p for p in DocumentPriority}
        sta_map = {s.value: s for s in ProcessingStatus}
        config  = load_config()
        prefix  = config.get("protocol_prefix", "")

        session = get_session()
        saved = 0
        errors = []

        try:
            for i, row in enumerate(self._import_data):
                if not row.get("subject"):
                    continue
                try:
                    direction = dir_map.get(row["direction"], DocumentDirection.INCOMING)
                    priority  = pri_map.get(row["priority"],  DocumentPriority.NORMAL)
                    status    = sta_map.get(row["status"],    ProcessingStatus.RECEIVED)
                    kwargs = dict(
                        registry_type=registry_type, prefix=prefix,
                        priority=priority, status=status,
                    )
                    if row.get("summary"):
                        kwargs["summary"] = row["summary"]
                    if row.get("ext_protocol_number"):
                        kwargs["ext_protocol_number"] = row["ext_protocol_number"]
                    if row.get("sender_name"):
                        contact = session.query(Contact).filter(
                            Contact.name.ilike(f"%{row['sender_name']}%")
                        ).first()
                        if contact:
                            kwargs["sender_contact_id"] = contact.id

                    create_protocol(
                        session,
                        direction=direction,
                        subject=row["subject"],
                        protocol_date=row["date"],
                        **kwargs,
                    )
                    saved += 1
                    # Color preview row green
                    for col in range(self._preview_table.columnCount()):
                        item = self._preview_table.item(i, col)
                        if item:
                            item.setBackground(QColor("#c6f6d5"))
                except Exception as ex:
                    errors.append(f"Γραμμή {i+1}: {ex}")
                    for col in range(self._preview_table.columnCount()):
                        item = self._preview_table.item(i, col)
                        if item:
                            item.setBackground(QColor("#fed7d7"))

            if saved > 0:
                session.commit()
                self.saved.emit(saved)
                msg = f"✅  Εισήχθησαν {saved} εγγραφές."
                if errors:
                    msg += f"  ⚠️ {len(errors)} σφάλμα/τα."
                self._lbl_import_status.setText(msg)
                self._lbl_import_status.setStyleSheet(
                    "color:#276749; font-size:12px; font-weight:bold;")
                QMessageBox.information(
                    self, "Αποτέλεσμα Εισαγωγής",
                    f"Εισήχθησαν επιτυχώς: {saved}\n" +
                    (f"Σφάλματα: {len(errors)}\n\n" + "\n".join(errors[:10]) if errors else "")
                )
            else:
                session.rollback()
                self._lbl_import_status.setText("❌  Καμία εισαγωγή.")
                self._lbl_import_status.setStyleSheet("color:#c53030; font-size:12px;")
                if errors:
                    QMessageBox.critical(self, "Σφάλμα", "\n".join(errors[:10]))
        except Exception as ex:
            session.rollback()
            QMessageBox.critical(self, "Σφάλμα", str(ex))
        finally:
            session.close()
