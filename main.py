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

    # ── Login / Main window loop (supports log-off and re-login) ─────────────
    from ui.styles import MAIN_STYLE
    app.setStyleSheet(MAIN_STYLE)

    do_logoff = True  # start with login screen
    while do_logoff:
        do_logoff = False

        # Show login dialog
        try:
            from ui.login_dialog import LoginDialog
            login = LoginDialog()
            result = login.exec()
            if result != 1:
                break  # user closed/cancelled login → exit
            current_user = login.current_user
            registry_type = login.selected_registry_type
            if current_user is None:
                show_error("Σφάλμα Σύνδεσης", "Δεν επιστράφηκε χρήστης. Δοκιμάστε ξανά.")
                break
        except Exception:
            show_error("Σφάλμα Login",
                       f"Σφάλμα κατά τη σύνδεση:\n\n{traceback.format_exc()}")
            break

        # Show main window
        try:
            from ui.main_window import MainWindow
            window = MainWindow(current_user=current_user, registry_type=registry_type)

            try:
                role_label = current_user.role.value
                full_name = current_user.full_name
                window.setWindowTitle(
                    f"{APP_NAME} v{APP_VERSION}  —  {full_name} ({role_label})"
                )
            except Exception:
                window.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")

            logoff_ref = [False]

            def on_logoff():
                logoff_ref[0] = True
                app.quit()

            window.logoff_requested.connect(on_logoff)
            window.show()
            app.exec()

            if logoff_ref[0]:
                do_logoff = True  # show login again

        except Exception:
            show_error("Σφάλμα Εκκίνησης",
                       f"Αδυναμία φόρτωσης κύριου παραθύρου:\n\n{traceback.format_exc()}")
            break

    sys.exit(0)


if __name__ == "__main__":
    main()
