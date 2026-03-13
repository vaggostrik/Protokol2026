#!/usr/bin/env python3
"""
Σύστημα Πρωτοκόλλου - Main entry point.
Electronic Document Management System for Greek public administration.
"""
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont, QColor

from config.settings import APP_NAME, APP_VERSION, DATA_DIR
from database.db import init_db


def create_splash(app: QApplication) -> QSplashScreen:
    """Create a simple splash screen."""
    pixmap = QPixmap(500, 300)
    pixmap.fill(QColor("#1a365d"))

    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)

    from PyQt6.QtGui import QPainter
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background gradient effect
    painter.fillRect(0, 0, 500, 300, QColor("#1a365d"))
    painter.fillRect(0, 240, 500, 60, QColor("#2b6cb0"))

    # Title
    font = QFont("Arial", 22, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QColor("white"))
    painter.drawText(0, 0, 500, 180, Qt.AlignmentFlag.AlignCenter, APP_NAME)

    # Version
    font2 = QFont("Arial", 11)
    painter.setFont(font2)
    painter.setPen(QColor("#bee3f8"))
    painter.drawText(0, 160, 500, 80, Qt.AlignmentFlag.AlignCenter,
                     "Σύστημα Ηλεκτρονικής Διαχείρισης Εγγράφων")

    font3 = QFont("Arial", 9)
    painter.setFont(font3)
    painter.setPen(QColor("#a0c4e8"))
    painter.drawText(0, 250, 500, 40, Qt.AlignmentFlag.AlignCenter, f"Έκδοση {APP_VERSION}")

    painter.end()
    splash.setPixmap(pixmap)
    return splash


def main():
    # Windows high-DPI support
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Protokol2026")

    # Set default font
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    # Splash
    splash = create_splash(app)
    splash.show()
    app.processEvents()

    # Initialize database
    splash.showMessage("  Αρχικοποίηση βάσης δεδομένων...",
                       Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
                       QColor("white"))
    app.processEvents()
    init_db()

    # Login
    splash.finish(None)
    from ui.login_dialog import LoginDialog
    login = LoginDialog()
    if login.exec() != login.DialogCode.Accepted:
        sys.exit(0)
    current_user = login.current_user

    # Create main window
    from ui.main_window import MainWindow
    window = MainWindow(current_user=current_user)
    user_label = f"{current_user.full_name} ({current_user.role.value})" if current_user else ""
    window.setWindowTitle(f"{APP_NAME} v{APP_VERSION}  —  {user_label}")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
