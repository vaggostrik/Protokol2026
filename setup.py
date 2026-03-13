"""
Setup script for building Windows executable with cx_Freeze.
Usage: python setup.py build
"""
import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": [
        "PyQt6", "sqlalchemy", "reportlab", "PIL",
        "smtplib", "email", "pathlib", "json",
        "database", "ui", "services", "utils", "reports", "config",
    ],
    "excludes": ["tkinter", "test", "unittest"],
    "include_files": [],
    "optimize": 2,
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="Πρωτόκολλο",
    version="1.0.0",
    description="Σύστημα Ηλεκτρονικής Διαχείρισης Πρωτοκόλλου",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py",
            base=base,
            target_name="Protokol.exe",
            icon="resources/icon.ico" if sys.platform == "win32" else None,
        )
    ],
)
