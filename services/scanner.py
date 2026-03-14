"""
scanner.py - WIA (Windows Image Acquisition) scanner integration
Χρησιμοποιεί WIA μέσω win32com - δουλεύει με Python x64.
Απαίτηση: pip install pywin32
"""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path
from typing import List

from config.settings import SCANS_DIR


def scan_document(parent=None) -> List[str]:
    if sys.platform != "win32":
        return _scan_fallback(parent)
    return _scan_wia(parent)


def _scan_wia(parent=None) -> List[str]:
    """Σάρωση μέσω WIA CommonDialog - x64 compatible."""
    try:
        import win32com.client
    except ImportError:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(
            parent, "Scanner",
            "Το pywin32 δεν είναι εγκατεστημένο.\n"
            "Τρέξε: pip install pywin32\n\n"
            "Θα ανοίξει επιλογή αρχείου."
        )
        return _scan_fallback(parent)

    try:
        wia = win32com.client.Dispatch("WIA.CommonDialog")

        # ShowAcquireImage με positional args (η WIA COM API δεν δέχεται keywords)
        # Signature: ShowAcquireImage(DeviceType, Intent, Bias, FormatID,
        #                             AlwaysSelectDevice, UseCommonUI, CancelError)
        WIA_DEVICE_SCANNER  = 1
        WIA_INTENT_IMAGE    = 1      # Color scan
        WIA_FORMAT_PNG      = "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}"

        image = wia.ShowAcquireImage(
            WIA_DEVICE_SCANNER,  # DeviceType
            WIA_INTENT_IMAGE,    # Intent
            0,                   # Bias
            WIA_FORMAT_PNG,      # FormatID
            False,               # AlwaysSelectDevice
            True,                # UseCommonUI
            True,                # CancelError
        )

        if image is None:
            return []

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = str(SCANS_DIR / f"scan_{ts}.png")
        image.SaveFile(out_path)
        return [out_path]

    except Exception as ex:
        err = str(ex)
        # Ο χρήστης πάτησε Άκυρο — δεν είναι σφάλμα
        if any(x in err for x in ["cancel", "Cancel", "-2145320939", "0x80210000", "COMException"]):
            return []

        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.warning(
            parent, "Scanner",
            f"Σφάλμα WIA:\n{err}\n\n"
            "Βεβαιώσου ότι:\n"
            "• Ο σαρωτής είναι συνδεδεμένος και ενεργός\n"
            "• Τα drivers Epson είναι εγκατεστημένα\n\n"
            "Θέλεις να επιλέξεις αρχείο χειροκίνητα;",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            return _scan_fallback(parent)
        return []


def _scan_fallback(parent=None) -> List[str]:
    """Fallback: επιλογή αρχείου από τον χρήστη."""
    from PyQt6.QtWidgets import QFileDialog
    paths, _ = QFileDialog.getOpenFileNames(
        parent, "Επιλογή Αρχείου Σάρωσης", str(SCANS_DIR),
        "Εικόνες (*.png *.jpg *.jpeg *.tif *.tiff *.bmp);;PDF (*.pdf);;Όλα (*.*)"
    )
    return paths


def get_available_scanners() -> List[str]:
    """Επιστρέφει λίστα διαθέσιμων WIA σαρωτών."""
    if sys.platform != "win32":
        return []
    try:
        import win32com.client
        mgr = win32com.client.Dispatch("WIA.DeviceManager")
        scanners = []
        for i in range(mgr.DeviceInfos.Count):
            info = mgr.DeviceInfos.Item(i + 1)
            if info.Type == 1:  # Scanner
                scanners.append(info.Properties("Name").Value)
        return scanners
    except Exception:
        return []
