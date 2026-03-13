#!/usr/bin/env python3
"""
Σύστημα Πρωτοκόλλου - Main entry point.
"""
import sys
import os
import traceback

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config.settings import APP_NAME, APP_VERSION


def show_error(title: str, message: str):
    """Show a critical error message box."""
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, title, message)
    except Exception:
        pass


def main():
    # Windows high-DPI
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Protokol2026")
    app.setFont(QFont("Segoe UI", 9))

    # ── Init database ─────────────────────────────────────────────────────────
    try:
        from database.db import init_db
        init_db()
    except Exception:
        show_error("Σφάλμα Βάσης Δεδομένων",
                   f"Αδυναμία αρχικοποίησης βάσης δεδομένων:\n\n{traceback.format_exc()}")
        sys.exit(1)

    # ── Login ─────────────────────────────────────────────────────────────────
    try:
        from ui.login_dialog import LoginDialog
        login = LoginDialog()
        result = login.exec()
        # Accept = 1, Reject = 0
        if result != 1:
            sys.exit(0)
        current_user = login.current_user
        if current_user is None:
            show_error("Σφάλμα Σύνδεσης", "Δεν επιστράφηκε χρήστης. Δοκιμάστε ξανά.")
            sys.exit(1)
    except Exception:
        show_error("Σφάλμα Login",
                   f"Σφάλμα κατά τη σύνδεση:\n\n{traceback.format_exc()}")
        sys.exit(1)

    # ── Main window ───────────────────────────────────────────────────────────
    try:
        from ui.main_window import MainWindow
        from ui.styles import MAIN_STYLE
        app.setStyleSheet(MAIN_STYLE)

        window = MainWindow(current_user=current_user)

        try:
            role_label = current_user.role.value
            full_name  = current_user.full_name
            window.setWindowTitle(
                f"{APP_NAME} v{APP_VERSION}  —  {full_name} ({role_label})"
            )
        except Exception:
            window.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")

        window.show()
    except Exception:
        show_error("Σφάλμα Εκκίνησης",
                   f"Αδυναμία φόρτωσης κύριου παραθύρου:\n\n{traceback.format_exc()}")
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
