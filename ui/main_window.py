"""Main application window."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QStatusBar, QLabel, QSplitter,
    QListWidget, QListWidgetItem, QStackedWidget,
    QMenuBar, QMenu, QMessageBox, QApplication,
)
from PyQt6.QtCore import Qt, QSize, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon, QPixmap, QColor

from config.settings import APP_NAME, APP_VERSION, load_config
from database.models import DocumentDirection, RegistryType
from ui.styles import MAIN_STYLE


class MainWindow(QMainWindow):
    logoff_requested = pyqtSignal()

    def __init__(self, current_user=None, registry_type: RegistryType = RegistryType.GENERAL):
        super().__init__()
        self._config = load_config()
        self._current_user = current_user
        self._registry_type = registry_type
        is_admin = current_user and current_user.role.value == "Διαχειριστής"
        self._is_admin = is_admin
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = QListWidget()
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setMaximumWidth(200)
        self._sidebar.setMinimumWidth(160)
        self._sidebar.setSpacing(2)
        self._sidebar.currentRowChanged.connect(self._on_nav)

        nav_items = [
            ("📋  Αναζήτηση", "search"),
            ("📥  Εισερχόμενα", "incoming"),
            ("📤  Εξερχόμενα", "outgoing"),
            ("🔄  Εσωτερικά", "internal"),
            ("📊  Βιβλίο Πρωτ.", "book"),
            ("⚙️  Παραμετρικά", "settings"),
            ("👥  Χρήστες", "users"),
            ("💾  Backup", "backup"),
        ]
        self._nav_keys = [k for _, k in nav_items]
        for label, _ in nav_items:
            item = QListWidgetItem(label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self._sidebar.addItem(item)

        # Sidebar header
        sidebar_container = QWidget()
        sidebar_container.setStyleSheet("background:#1a365d;")
        sv = QVBoxLayout(sidebar_container)
        sv.setContentsMargins(0, 0, 0, 0)
        sv.setSpacing(0)

        header_lbl = QLabel(self._config.get("organization_name", APP_NAME))
        header_lbl.setWordWrap(True)
        header_lbl.setStyleSheet(
            "color:white; font-size:12px; font-weight:bold; padding:10px 8px 8px 10px;"
            "border-bottom:1px solid #2a4a7f;"
        )
        sv.addWidget(header_lbl)

        # Registry type label
        reg_lbl = QLabel(f"📂  {self._registry_type.value}")
        reg_lbl.setWordWrap(True)
        reg_lbl.setStyleSheet(
            "color:#bee3f8; font-size:10px; padding:4px 10px 4px 10px;"
            "border-bottom:1px solid #2a4a7f; background:#1e3a5f;"
        )
        sv.addWidget(reg_lbl)

        sv.addWidget(self._sidebar, 1)

        # User info + logoff/exit at bottom
        from PyQt6.QtWidgets import QPushButton
        bottom_widget = QWidget()
        bottom_widget.setStyleSheet("background:#142d50; border-top:1px solid #2a4a7f;")
        bv = QVBoxLayout(bottom_widget)
        bv.setContentsMargins(8, 6, 8, 6)
        bv.setSpacing(4)

        user_name = (self._current_user.full_name if self._current_user else "—")
        user_lbl = QLabel(f"👤  {user_name}")
        user_lbl.setStyleSheet("color:#a0c4e8; font-size:10px; background:transparent;")
        user_lbl.setWordWrap(True)
        bv.addWidget(user_lbl)

        btn_row = QHBoxLayout()
        btn_logoff = QPushButton("🔄 Αλλαγή Χρήστη")
        btn_logoff.setStyleSheet(
            "QPushButton{background:#2a4a7f;color:white;border:none;border-radius:4px;"
            "padding:5px 4px;font-size:10px;}"
            "QPushButton:hover{background:#3a5a8f;}"
        )
        btn_logoff.clicked.connect(self._do_logoff)

        btn_exit = QPushButton("❌ Έξοδος")
        btn_exit.setStyleSheet(
            "QPushButton{background:#6b2737;color:white;border:none;border-radius:4px;"
            "padding:5px 4px;font-size:10px;}"
            "QPushButton:hover{background:#8b3747;}"
        )
        btn_exit.clicked.connect(QApplication.quit)

        btn_row.addWidget(btn_logoff)
        btn_row.addWidget(btn_exit)
        bv.addLayout(btn_row)

        sv.addWidget(bottom_widget)

        version_lbl = QLabel(f"v{APP_VERSION}")
        version_lbl.setStyleSheet("color:#4a6fa5; font-size:10px; padding:4px 10px;"
                                  "background:#1a365d;")
        sv.addWidget(version_lbl)

        main_layout.addWidget(sidebar_container)

        # Content area (stacked pages)
        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack, 1)

        # Pages (lazy loaded)
        self._pages: dict = {}
        self._sidebar.setCurrentRow(0)

    def _get_page(self, key: str) -> QWidget:
        if key not in self._pages:
            try:
                self._pages[key] = self._create_page(key)
            except Exception as ex:
                from PyQt6.QtWidgets import QVBoxLayout, QLabel
                placeholder = QWidget()
                v = QVBoxLayout(placeholder)
                lbl = QLabel(f"⚠️  Σφάλμα φόρτωσης σελίδας:\n{ex}")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet("color:#c53030; font-size:13px; margin:40px;")
                lbl.setWordWrap(True)
                v.addWidget(lbl)
                self._pages[key] = placeholder
            self._stack.addWidget(self._pages[key])
        return self._pages[key]

    def _create_page(self, key: str) -> QWidget:
        if key == "search":
            from ui.search_panel import SearchPanel
            p = SearchPanel()
            p.open_protocol.connect(self._open_protocol)
            p.new_protocol.connect(self._new_protocol_by_direction)
            return p
        elif key == "incoming":
            from ui.search_panel import SearchPanel
            p = SearchPanel()
            p.open_protocol.connect(self._open_protocol)
            p.new_protocol.connect(self._new_protocol_by_direction)
            # Pre-filter
            p._cb_direction.setCurrentIndex(
                next((i for i in range(p._cb_direction.count())
                      if p._cb_direction.itemData(i) == "ΕΙΣΕΡΧΟΜΕΝΟ"), 0))
            p.do_search()
            return p
        elif key == "outgoing":
            from ui.search_panel import SearchPanel
            p = SearchPanel()
            p.open_protocol.connect(self._open_protocol)
            p.new_protocol.connect(self._new_protocol_by_direction)
            p._cb_direction.setCurrentIndex(
                next((i for i in range(p._cb_direction.count())
                      if p._cb_direction.itemData(i) == "ΕΞΕΡΧΟΜΕΝΟ"), 0))
            p.do_search()
            return p
        elif key == "internal":
            from ui.search_panel import SearchPanel
            p = SearchPanel()
            p.open_protocol.connect(self._open_protocol)
            p.new_protocol.connect(self._new_protocol_by_direction)
            p._cb_direction.setCurrentIndex(
                next((i for i in range(p._cb_direction.count())
                      if p._cb_direction.itemData(i) == "ΕΣΩΤΕΡΙΚΟ"), 0))
            p.do_search()
            return p
        elif key == "book":
            from PyQt6.QtWidgets import QVBoxLayout, QPushButton
            from ui.widgets import SectionHeader
            w = QWidget()
            layout = QVBoxLayout(w)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(12)
            layout.addWidget(SectionHeader("Βιβλίο Πρωτοκόλλου"))
            reg_lbl = QLabel(f"Ενεργό βιβλίο: {self._registry_type.value}")
            reg_lbl.setStyleSheet("color:#2b6cb0; font-size:13px; font-weight:bold;")
            layout.addWidget(reg_lbl)
            btn = QPushButton("📖  Εκτύπωση / Εξαγωγή Βιβλίου Πρωτοκόλλου (PDF)")
            btn.setMaximumWidth(400)
            btn.setStyleSheet(
                "QPushButton{background:#2b6cb0;color:white;padding:12px 20px;"
                "border-radius:6px;font-size:13px;font-weight:bold;}"
                "QPushButton:hover{background:#3182ce;}"
            )
            btn.clicked.connect(self._open_print_book)
            layout.addWidget(btn)
            layout.addStretch()
            return w
        elif key == "settings":
            from ui.settings_panel import SettingsPanel
            return SettingsPanel()
        elif key == "users":
            from ui.user_management import UserManagementPanel
            w = UserManagementPanel()
            if not self._is_admin:
                from PyQt6.QtWidgets import QVBoxLayout
                placeholder = QWidget()
                v = QVBoxLayout(placeholder)
                lbl = QLabel("⛔  Μόνο διαχειριστές μπορούν να διαχειριστούν χρήστες.")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet("color:#718096; font-size:14px; margin:40px;")
                v.addWidget(lbl)
                return placeholder
            return w
        elif key == "backup":
            return self._build_backup_page()
        return QWidget()

    def _build_backup_page(self) -> QWidget:
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox
        from ui.widgets import SectionHeader
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(SectionHeader("Backup & Επαναφορά"))

        from PyQt6.QtWidgets import QGroupBox, QFormLayout
        g = QGroupBox("Αντίγραφο Ασφαλείας")
        gv = QVBoxLayout(g)
        lbl = QLabel(
            "Δημιουργεί ZIP αρχείο με τη βάση δεδομένων και όλα τα συνημμένα αρχεία.\n"
            "Αποθηκεύστε το σε ασφαλές μέρος (USB, cloud, κλπ)."
        )
        lbl.setWordWrap(True)
        gv.addWidget(lbl)
        btn_backup = QPushButton("💾  Δημιουργία Backup")
        btn_backup.setStyleSheet(
            "QPushButton{background:#2b6cb0;color:white;padding:12px 24px;"
            "border-radius:6px;font-size:14px;font-weight:bold;max-width:280px;}"
            "QPushButton:hover{background:#3182ce;}"
        )
        btn_backup.clicked.connect(self._do_backup)
        gv.addWidget(btn_backup)
        layout.addWidget(g)

        g2 = QGroupBox("Επαναφορά από Backup")
        g2v = QVBoxLayout(g2)
        lbl2 = QLabel(
            "⚠️  Η επαναφορά αντικαθιστά τα υπάρχοντα δεδομένα!\n"
            "Πριν την επαναφορά δημιουργήστε νέο backup."
        )
        lbl2.setWordWrap(True)
        lbl2.setStyleSheet("color:#c05621;")
        g2v.addWidget(lbl2)
        btn_restore = QPushButton("📂  Επαναφορά από Backup ZIP")
        btn_restore.setStyleSheet(
            "QPushButton{background:#744210;color:white;padding:12px 24px;"
            "border-radius:6px;font-size:14px;font-weight:bold;max-width:280px;}"
            "QPushButton:hover{background:#975a16;}"
        )
        if not self._is_admin:
            btn_restore.setEnabled(False)
            btn_restore.setToolTip("Μόνο διαχειριστές μπορούν να κάνουν επαναφορά.")
        btn_restore.clicked.connect(self._do_restore)
        g2v.addWidget(btn_restore)
        layout.addWidget(g2)

        layout.addStretch()
        return w

    def _on_nav(self, index: int):
        if 0 <= index < len(self._nav_keys):
            key = self._nav_keys[index]
            page = self._get_page(key)
            self._stack.setCurrentWidget(page)

    # ── Menu ──────────────────────────────────────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("Αρχείο")
        act_new_in = QAction("Νέο Εισερχόμενο\tCtrl+N", self)
        act_new_in.setShortcut("Ctrl+N")
        act_new_in.triggered.connect(lambda: self._new_protocol(DocumentDirection.INCOMING))
        act_new_out = QAction("Νέο Εξερχόμενο\tCtrl+Shift+N", self)
        act_new_out.setShortcut("Ctrl+Shift+N")
        act_new_out.triggered.connect(lambda: self._new_protocol(DocumentDirection.OUTGOING))
        act_new_int = QAction("Νέο Εσωτερικό\tCtrl+Alt+N", self)
        act_new_int.triggered.connect(lambda: self._new_protocol(DocumentDirection.INTERNAL))
        file_menu.addAction(act_new_in)
        file_menu.addAction(act_new_out)
        file_menu.addAction(act_new_int)
        file_menu.addSeparator()
        act_logoff = QAction("🔄  Αλλαγή Χρήστη (Log-off)", self)
        act_logoff.triggered.connect(self._do_logoff)
        file_menu.addAction(act_logoff)
        file_menu.addSeparator()
        act_exit = QAction("❌  Έξοδος\tAlt+F4", self)
        act_exit.triggered.connect(QApplication.quit)
        file_menu.addAction(act_exit)

        # Search
        search_menu = mb.addMenu("Αναζήτηση")
        act_search = QAction("Αναζήτηση Εγγράφων\tCtrl+F", self)
        act_search.setShortcut("Ctrl+F")
        act_search.triggered.connect(lambda: self._sidebar.setCurrentRow(0))
        search_menu.addAction(act_search)

        # Reports
        rep_menu = mb.addMenu("Εκτυπώσεις")
        act_book = QAction("Βιβλίο Πρωτοκόλλου...", self)
        act_book.triggered.connect(self._open_print_book)
        rep_menu.addAction(act_book)

        # Settings
        cfg_menu = mb.addMenu("Παραμετρικά")
        act_settings = QAction("Ρυθμίσεις\tCtrl+,", self)
        act_settings.triggered.connect(lambda: self._sidebar.setCurrentRow(5))
        cfg_menu.addAction(act_settings)

        # Help
        help_menu = mb.addMenu("Βοήθεια")
        act_about = QAction("Σχετικά...", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    # ── Toolbar ───────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        tb = QToolBar("Κύρια Εργαλειοθήκη")
        tb.setIconSize(QSize(16, 16))
        tb.setMovable(False)
        self.addToolBar(tb)

        def add_btn(text, slot, style=""):
            act = QAction(text, self)
            act.triggered.connect(slot)
            btn = tb.addAction(act)
            return act

        add_btn("📥 Νέο Εισερχόμενο", lambda: self._new_protocol(DocumentDirection.INCOMING))
        add_btn("📤 Νέο Εξερχόμενο", lambda: self._new_protocol(DocumentDirection.OUTGOING))
        add_btn("🔄 Νέο Εσωτερικό", lambda: self._new_protocol(DocumentDirection.INTERNAL))
        tb.addSeparator()
        add_btn("🔍 Αναζήτηση", lambda: self._sidebar.setCurrentRow(0))
        add_btn("📖 Βιβλίο Πρωτ.", self._open_print_book)
        tb.addSeparator()
        add_btn("⚙️ Παραμετρικά", lambda: self._sidebar.setCurrentRow(5))

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        from database.db import get_session
        from database.models import Protocol
        s = get_session()
        count = s.query(Protocol).count()
        s.close()
        self._status_lbl = QLabel(
            f"  {self._config.get('organization_name', APP_NAME)}  |  "
            f"Σύνολο εγγράφων: {count}  |  {APP_NAME} v{APP_VERSION}"
        )
        sb.addWidget(self._status_lbl)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _new_protocol(self, direction: DocumentDirection):
        from ui.protocol_form import ProtocolForm
        dlg = ProtocolForm(direction=direction, parent=self)
        dlg.saved.connect(self._on_protocol_saved)
        dlg.exec()

    def _new_protocol_by_direction(self, direction_str: str):
        direction_map = {
            "ΕΙΣΕΡΧΟΜΕΝΟ": DocumentDirection.INCOMING,
            "ΕΞΕΡΧΟΜΕΝΟ": DocumentDirection.OUTGOING,
            "ΕΣΩΤΕΡΙΚΟ": DocumentDirection.INTERNAL,
        }
        d = direction_map.get(direction_str, DocumentDirection.INCOMING)
        self._new_protocol(d)

    def _open_protocol(self, protocol_id: int):
        from ui.protocol_form import ProtocolForm
        dlg = ProtocolForm(protocol_id=protocol_id, parent=self)
        dlg.saved.connect(self._on_protocol_saved)
        dlg.exec()

    def _on_protocol_saved(self, protocol_id: int):
        # Refresh all search panels
        for key in ["search", "incoming", "outgoing", "internal"]:
            if key in self._pages:
                try:
                    self._pages[key].refresh()
                except Exception:
                    pass
        # Update status bar count
        from database.db import get_session
        from database.models import Protocol
        s = get_session()
        count = s.query(Protocol).count()
        s.close()
        self._status_lbl.setText(
            f"  {self._config.get('organization_name', APP_NAME)}  |  "
            f"Σύνολο εγγράφων: {count}  |  {APP_NAME} v{APP_VERSION}"
        )

    def _open_print_book(self):
        from ui.print_dialog import PrintBookDialog
        dlg = PrintBookDialog(self, default_registry_type=self._registry_type)
        dlg.exec()

    def _do_logoff(self):
        from ui.widgets import ConfirmDialog
        if ConfirmDialog.ask(self, "Αλλαγή Χρήστη",
                             "Να αποσυνδεθείτε και να συνδεθείτε με άλλο χρήστη;"):
            self.logoff_requested.emit()
            self.close()

    def _do_backup(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        dest = QFileDialog.getExistingDirectory(self, "Επιλογή φακέλου αποθήκευσης backup")
        if not dest:
            return
        from services.backup import create_backup
        from utils.helpers import file_size_human
        try:
            path = create_backup(dest)
            import os
            size = file_size_human(os.path.getsize(path))
            QMessageBox.information(self, "Backup", f"Το backup δημιουργήθηκε:\n{path}\nΜέγεθος: {size}")
        except Exception as ex:
            QMessageBox.critical(self, "Σφάλμα", str(ex))

    def _do_restore(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        path, _ = QFileDialog.getOpenFileName(
            self, "Επιλογή αρχείου Backup", "", "ZIP (*.zip)")
        if not path:
            return
        from ui.widgets import ConfirmDialog
        if not ConfirmDialog.ask(self, "Επαναφορά",
                                  "Η επαναφορά θα αντικαταστήσει ΟΛΑ τα υπάρχοντα δεδομένα!\nΣυνέχεια;"):
            return
        from services.backup import restore_backup
        ok, msg = restore_backup(path)
        if ok:
            QMessageBox.information(self, "Επιτυχία", msg)
        else:
            QMessageBox.critical(self, "Σφάλμα", msg)

    def _show_about(self):
        QMessageBox.about(
            self,
            f"Σχετικά με {APP_NAME}",
            f"<h2>{APP_NAME}</h2>"
            f"<p>Έκδοση: <b>{APP_VERSION}</b></p>"
            f"<p>Σύστημα Ηλεκτρονικής Διαχείρισης Πρωτοκόλλου</p>"
            f"<ul>"
            f"<li>Εισερχόμενα / Εξερχόμενα / Εσωτερικά έγγραφα</li>"
            f"<li>Ψηφιοποίηση (TWAIN Scanner)</li>"
            f"<li>Αυτόματη αποστολή Email</li>"
            f"<li>Εκτύπωση Βιβλίου Πρωτοκόλλου (A4/A3)</li>"
            f"<li>Παραμετρικά τμήματα, υπάλληλοι, επαφές</li>"
            f"</ul>"
            f"<p><small>Δεδομένα: SQLite | UI: PyQt6 | PDF: ReportLab</small></p>"
        )
