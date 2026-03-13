"""TWAIN scanner integration for document scanning."""
from __future__ import annotations
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

from config.settings import SCANS_DIR


def scan_document(parent=None) -> List[str]:
    """
    Open scanner UI and return list of saved image paths.
    Falls back to file-open dialog if TWAIN is unavailable.
    """
    if sys.platform == "win32":
        return _scan_twain(parent)
    else:
        return _scan_fallback(parent)


def _scan_twain(parent=None) -> List[str]:
    """Use pytwain for Windows TWAIN scanning."""
    try:
        import twain
    except ImportError:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(
            parent, "Scanner",
            "Το module 'pytwain' δεν είναι εγκατεστημένο.\n"
            "Εκτελέστε: pip install pytwain\n\n"
            "Θα ανοίξει παράθυρο επιλογής αρχείου αντί σαρωτή."
        )
        return _scan_fallback(parent)

    try:
        sm = twain.SourceManager(0)
        source = sm.OpenSource()
        if source is None:
            return []

        saved_paths = []
        source.SetCapability(twain.ICAP_PIXELTYPE, twain.TWTY_UINT16, twain.TWPT_RGB)
        source.SetCapability(twain.ICAP_XRESOLUTION, twain.TWTY_FIX32, 300.0)
        source.SetCapability(twain.ICAP_YRESOLUTION, twain.TWTY_FIX32, 300.0)

        source.RequestAcquire(0, 0)
        rv = source.XferImageNatively()
        if rv:
            handle, count = rv
            bmp = twain.DIBToBMFile(handle)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = SCANS_DIR / f"scan_{ts}.bmp"
            with open(out_path, "wb") as f:
                f.write(bmp)
            # Convert to PNG using Pillow if available
            try:
                from PIL import Image
                img = Image.open(out_path)
                png_path = out_path.with_suffix(".png")
                img.save(png_path)
                out_path.unlink()
                out_path = png_path
            except ImportError:
                pass
            saved_paths.append(str(out_path))

        source.destroy()
        sm.destroy()
        return saved_paths

    except Exception as ex:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(parent, "Scanner", f"Σφάλμα σάρωσης:\n{ex}\n\nΕπιλέξτε αρχείο.")
        return _scan_fallback(parent)


def _scan_fallback(parent=None) -> List[str]:
    """File picker fallback for systems without TWAIN."""
    from PyQt6.QtWidgets import QFileDialog
    paths, _ = QFileDialog.getOpenFileNames(
        parent, "Επιλογή Αρχείου Σάρωσης", str(SCANS_DIR),
        "Εικόνες (*.png *.jpg *.jpeg *.tif *.tiff *.bmp);;PDF (*.pdf);;Όλα (*.*)"
    )
    return paths


def get_available_scanners() -> List[str]:
    """Return list of available TWAIN scanner names (Windows only)."""
    if sys.platform != "win32":
        return []
    try:
        import twain
        sm = twain.SourceManager(0)
        sources = sm.GetSourceList()
        sm.destroy()
        return sources
    except Exception:
        return []
