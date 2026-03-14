"""
scanner.py - WIA scanner με επιλογή μορφής αρχείου
Απαίτηση: pip install pywin32 Pillow
"""
from __future__ import annotations
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List

from config.settings import SCANS_DIR


def scan_document(parent=None) -> List[str]:
    if sys.platform != "win32":
        return _scan_fallback(parent)
    return _scan_wia(parent)


def _ask_format(parent=None) -> str | None:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox
    )
    dlg = QDialog(parent)
    dlg.setWindowTitle("Μορφή Αποθήκευσης")
    dlg.setMinimumWidth(260)
    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel("Αποθήκευση σαρωμένου εγγράφου ως:"))
    cb = QComboBox()
    cb.addItems(["PDF", "PNG", "JPEG", "TIFF"])
    layout.addWidget(cb)
    btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    btns.button(QDialogButtonBox.StandardButton.Ok).setText("Αποθήκευση")
    btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Ακύρωση")
    btns.accepted.connect(dlg.accept)
    btns.rejected.connect(dlg.reject)
    layout.addWidget(btns)
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return None
    return cb.currentText().lower()


def _scan_wia(parent=None) -> List[str]:
    try:
        import win32com.client
    except ImportError:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(parent, "Scanner",
            "Το pywin32 δεν είναι εγκατεστημένο.\nΤρέξε: pip install pywin32")
        return _scan_fallback(parent)

    WIA_FORMAT_PNG = "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}"
    tmp_path = None

    try:
        wia = win32com.client.Dispatch("WIA.CommonDialog")
        image = wia.ShowAcquireImage(1, 1, 0, WIA_FORMAT_PNG, False, True, True)
        if image is None:
            return []

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        tmp_path = SCANS_DIR / f"scan_{ts}_tmp.png"
        image.SaveFile(str(tmp_path))

        # ── Αφήνουμε το WIA να αφήσει το αρχείο ──────────────────────────────
        del image
        del wia
        time.sleep(0.5)  # μικρή αναμονή για να ελευθερωθεί το handle

    except Exception as ex:
        err = str(ex)
        if any(x in err for x in ["cancel", "Cancel", "-2145320939", "0x80210000"]):
            return []
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.warning(
            parent, "Scanner",
            f"Σφάλμα WIA:\n{err}\n\nΘέλεις να επιλέξεις αρχείο χειροκίνητα;",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            return _scan_fallback(parent)
        return []

    # ── Επιλογή μορφής (εκτός του try ώστε το WIA να έχει ήδη κλείσει) ───────
    fmt = _ask_format(parent)
    if fmt is None:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        return []

    out_path = _convert_image(tmp_path, fmt)
    return [str(out_path)]


def _convert_image(src: Path, fmt: str) -> Path:
    try:
        from PIL import Image
        img = Image.open(src)
        out_path = src.parent / f"{src.stem.replace('_tmp', '')}.{fmt}"

        if fmt == "pdf":
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(str(out_path), "PDF")
        elif fmt == "jpeg":
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(str(out_path), "JPEG", quality=95)
        elif fmt == "tiff":
            img.save(str(out_path), "TIFF")
        else:
            img.save(str(out_path), "PNG")

        img.close()
        src.unlink(missing_ok=True)
        return out_path

    except ImportError:
        out_path = src.parent / f"{src.stem.replace('_tmp', '')}.png"
        src.rename(out_path)
        return out_path


def _scan_fallback(parent=None) -> List[str]:
    from PyQt6.QtWidgets import QFileDialog
    paths, _ = QFileDialog.getOpenFileNames(
        parent, "Επιλογή Αρχείου Σάρωσης", str(SCANS_DIR),
        "Εικόνες (*.png *.jpg *.jpeg *.tif *.tiff *.bmp);;PDF (*.pdf);;Όλα (*.*)"
    )
    return paths


def get_available_scanners() -> List[str]:
    if sys.platform != "win32":
        return []
    try:
        import win32com.client
        mgr = win32com.client.Dispatch("WIA.DeviceManager")
        scanners = []
        for i in range(mgr.DeviceInfos.Count):
            info = mgr.DeviceInfos.Item(i + 1)
            if info.Type == 1:
                scanners.append(info.Properties("Name").Value)
        return scanners
    except Exception:
        return []
