"""Stamp protocol number onto documents before opening them.

For image files (scanned documents): uses Pillow to add a header strip.
For PDF files: uses ReportLab to create a stamped copy.
Other files: returned as-is (no stamp possible without modifying the file format).

Returns the path to the (possibly temporary) stamped file.
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

_IMAGE_EXTS  = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif"}
_PDF_EXT     = ".pdf"


def _stamp_image(src: str, proto_num: str, proto_date: str) -> str:
    """Add a header banner with protocol number to an image file."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return src  # Pillow not available

    try:
        img = Image.open(src).convert("RGB")
        w, h = img.size

        # Banner height proportional to image width (roughly 5%)
        banner_h = max(40, w // 20)
        font_size = max(14, banner_h // 2)

        # Try to load a font; fall back to default
        font_bold = None
        font_normal = None
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
        ]
        font_candidates_normal = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ]
        for p in font_candidates:
            if os.path.exists(p):
                try:
                    font_bold = ImageFont.truetype(p, font_size)
                    break
                except Exception:
                    pass
        for p in font_candidates_normal:
            if os.path.exists(p):
                try:
                    font_normal = ImageFont.truetype(p, max(10, font_size - 4))
                    break
                except Exception:
                    pass
        if font_bold is None:
            font_bold = ImageFont.load_default()
        if font_normal is None:
            font_normal = font_bold

        # Create banner
        banner = Image.new("RGB", (w, banner_h), color=(26, 54, 93))  # dark blue
        draw = ImageDraw.Draw(banner)

        left_text  = f"ΑΡ. ΠΡΩΤ.: {proto_num}"
        right_text = proto_date or ""
        margin = 10

        draw.text((margin, banner_h // 2 - font_size // 2),
                  left_text, fill=(255, 255, 255), font=font_bold)
        if right_text:
            try:
                bbox = draw.textbbox((0, 0), right_text, font=font_normal)
                tw = bbox[2] - bbox[0]
            except Exception:
                tw = len(right_text) * (font_size // 2)
            draw.text((w - tw - margin, banner_h // 2 - font_size // 2 + 2),
                      right_text, fill=(180, 210, 240), font=font_normal)

        # Combine
        combined = Image.new("RGB", (w, h + banner_h))
        combined.paste(banner, (0, 0))
        combined.paste(img, (0, banner_h))

        suffix = Path(src).suffix or ".jpg"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        combined.save(tmp.name)
        tmp.close()
        return tmp.name
    except Exception:
        return src  # on any error, open original


def _stamp_pdf(src: str, proto_num: str, proto_date: str) -> str:
    """Add a header stamp with protocol number to a PDF file."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas as rl_canvas
        from utils.pdf_fonts import register_greek_fonts, FONT_BOLD, FONT_NORMAL
    except ImportError:
        return src

    try:
        import io
        register_greek_fonts()

        # Read original PDF pages and add an overlay on every page
        try:
            from pypdf import PdfWriter, PdfReader
        except ImportError:
            try:
                from PyPDF2 import PdfWriter, PdfReader
            except ImportError:
                return src  # no PDF library

        reader = PdfReader(src)
        writer = PdfWriter()

        for page in reader.pages:
            # Build stamp page
            width  = float(page.mediabox.width)
            height = float(page.mediabox.height)

            stamp_buf = io.BytesIO()
            c = rl_canvas.Canvas(stamp_buf, pagesize=(width, height))
            c.setFillColor(colors.HexColor("#1a365d"))
            banner_h = 28
            c.rect(0, height - banner_h, width, banner_h, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont(FONT_BOLD, 11)
            c.drawString(10, height - banner_h + 8,
                         f"ΑΡ. ΠΡΩΤ.: {proto_num}")
            if proto_date:
                c.setFont(FONT_NORMAL, 9)
                c.drawRightString(width - 10, height - banner_h + 9, proto_date)
            c.save()
            stamp_buf.seek(0)

            stamp_reader = PdfReader(stamp_buf)
            stamp_page   = stamp_reader.pages[0]
            page.merge_page(stamp_page)
            writer.add_page(page)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        with open(tmp.name, "wb") as f:
            writer.write(f)
        tmp.close()
        return tmp.name
    except Exception:
        return src


def stamp_and_open(file_path: str, proto_num: str, proto_date: str = ""):
    """Stamp protocol number on file (if image or PDF) and open with default viewer."""
    if not file_path or not os.path.exists(file_path):
        return

    ext = Path(file_path).suffix.lower()
    if ext in _IMAGE_EXTS:
        open_path = _stamp_image(file_path, proto_num, proto_date)
    elif ext == _PDF_EXT:
        open_path = _stamp_pdf(file_path, proto_num, proto_date)
    else:
        open_path = file_path  # Word/Excel etc. – open as-is

    if sys.platform == "win32":
        os.startfile(open_path)
    elif sys.platform == "darwin":
        os.system(f"open '{open_path}'")
    else:
        os.system(f"xdg-open '{open_path}'")
