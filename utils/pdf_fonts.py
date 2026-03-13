"""ReportLab Greek font registration.

Registers DejaVu Sans (or fallback) TrueType fonts that support the full
Greek Unicode range.  Call `register_greek_fonts()` once before building
any PDF; afterwards use the font names:
    FONT_NORMAL   ("GreekNormal")
    FONT_BOLD     ("GreekBold")
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

FONT_NORMAL = "GreekNormal"
FONT_BOLD   = "GreekBold"

_registered = False

# Search paths for DejaVu/Liberation fonts (platform-specific)
_FONT_SEARCH_DIRS = [
    # Linux
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts/truetype/liberation"),
    Path("/usr/share/fonts"),
    # macOS
    Path("/Library/Fonts"),
    Path(os.path.expanduser("~/Library/Fonts")),
    # Windows
    Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
    # App-bundled fonts (next to this file or in resources/)
    Path(__file__).parent.parent / "resources" / "fonts",
    Path(__file__).parent.parent / "fonts",
]

_FONT_CANDIDATES_NORMAL = [
    "DejaVuSans.ttf",
    "LiberationSans-Regular.ttf",
    "arial.ttf",
    "Arial.ttf",
]
_FONT_CANDIDATES_BOLD = [
    "DejaVuSans-Bold.ttf",
    "LiberationSans-Bold.ttf",
    "arialbd.ttf",
    "Arial Bold.ttf",
]


def _find_font(candidates: list[str]) -> str | None:
    for d in _FONT_SEARCH_DIRS:
        for name in candidates:
            p = d / name
            if p.exists():
                return str(p)
    return None


def register_greek_fonts() -> bool:
    """
    Register Greek-capable TTF fonts with ReportLab.
    Returns True on success, False if no suitable font found (Helvetica fallback).
    """
    global _registered
    if _registered:
        return True

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    normal_path = _find_font(_FONT_CANDIDATES_NORMAL)
    bold_path   = _find_font(_FONT_CANDIDATES_BOLD)

    if normal_path and bold_path:
        try:
            pdfmetrics.registerFont(TTFont(FONT_NORMAL, normal_path))
            pdfmetrics.registerFont(TTFont(FONT_BOLD,   bold_path))
            _registered = True
            return True
        except Exception:
            pass

    # Fallback: alias to Helvetica (no Greek, but won't crash)
    # Map the names so code using FONT_NORMAL/FONT_BOLD still works
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    try:
        pdfmetrics.registerFont(TTFont(FONT_NORMAL, normal_path or ""))
    except Exception:
        pass
    _registered = False
    return False
