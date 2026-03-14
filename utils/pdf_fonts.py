"""ReportLab Greek font registration.

Registers Greek-capable TrueType fonts with ReportLab.
Call `register_greek_fonts()` once before building any PDF; afterwards use:
    FONT_NORMAL   ("GreekNormal")
    FONT_BOLD     ("GreekBold")
"""
from __future__ import annotations
import os
from pathlib import Path

FONT_NORMAL = "GreekNormal"
FONT_BOLD   = "GreekBold"

_registered = False

# ── Font search directories (Windows / macOS / Linux) ────────────────────────
_WIN_FONTS = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
_FONT_SEARCH_DIRS = [
    # App-bundled fonts (highest priority – guaranteed to work)
    Path(__file__).parent.parent / "resources" / "fonts",
    Path(__file__).parent.parent / "fonts",
    # Windows – two possible locations
    _WIN_FONTS,
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts",
    # macOS
    Path("/Library/Fonts"),
    Path("/System/Library/Fonts"),
    Path(os.path.expanduser("~/Library/Fonts")),
    # Linux
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts/truetype/liberation"),
    Path("/usr/share/fonts/truetype"),
    Path("/usr/share/fonts"),
]

# ── Candidate font filenames (tried in order; first hit wins) ────────────────
# All of these support the full Greek Unicode range on Windows 10/11.
_FONT_CANDIDATES_NORMAL = [
    # Bundled DejaVu (best choice if shipped with app)
    "DejaVuSans.ttf",
    # Windows – Arial (always present)
    "arial.ttf",
    "Arial.ttf",
    # Windows – Calibri (Office default, excellent Greek)
    "calibri.ttf",
    "Calibri.ttf",
    # Windows – Segoe UI
    "segoeui.ttf",
    # Windows – Times New Roman
    "times.ttf",
    "Times New Roman.ttf",
    # Windows – Tahoma
    "tahoma.ttf",
    # Linux
    "LiberationSans-Regular.ttf",
    "FreeSans.ttf",
]
_FONT_CANDIDATES_BOLD = [
    "DejaVuSans-Bold.ttf",
    # Arial Bold
    "arialbd.ttf",
    "Arial Bold.ttf",
    # Calibri Bold
    "calibrib.ttf",
    "Calibri Bold.ttf",
    # Segoe UI Bold
    "segoeuib.ttf",
    # Times New Roman Bold
    "timesbd.ttf",
    "Times New Roman Bold.ttf",
    # Tahoma Bold
    "tahomabd.ttf",
    # Linux
    "LiberationSans-Bold.ttf",
    "FreeSansBold.ttf",
]


def _find_font(candidates: list[str]) -> str | None:
    """Return the first existing font file from candidates × search dirs."""
    for d in _FONT_SEARCH_DIRS:
        if not d.exists():
            continue
        for name in candidates:
            p = d / name
            if p.exists():
                return str(p)
    return None


def register_greek_fonts() -> bool:
    """
    Register Greek-capable TTF fonts with ReportLab.
    Returns True on success, False if no suitable font was found.
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

    # Last resort: try registering only the normal font for both roles
    if normal_path:
        try:
            pdfmetrics.registerFont(TTFont(FONT_NORMAL, normal_path))
            pdfmetrics.registerFont(TTFont(FONT_BOLD,   normal_path))
            _registered = True
            return True
        except Exception:
            pass

    # Could not find any Greek font — ReportLab will use Helvetica
    # (Greek characters will appear as boxes, but the app won't crash)
    _registered = False
    return False
