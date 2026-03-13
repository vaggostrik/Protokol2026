"""General utility helpers."""
from __future__ import annotations
import os
import shutil
import hashlib
from datetime import date, datetime
from pathlib import Path
from typing import Optional


GREEK_MONTHS = [
    "", "Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου",
    "Μαΐου", "Ιουνίου", "Ιουλίου", "Αυγούστου",
    "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου",
]

GREEK_MONTHS_SHORT = [
    "", "Ιαν", "Φεβ", "Μαρ", "Απρ", "Μαΐ", "Ιουν",
    "Ιουλ", "Αυγ", "Σεπ", "Οκτ", "Νοε", "Δεκ",
]


def format_date_greek(d: Optional[date]) -> str:
    if d is None:
        return ""
    return f"{d.day} {GREEK_MONTHS[d.month]} {d.year}"


def format_date_short(d: Optional[date]) -> str:
    if d is None:
        return ""
    return d.strftime("%d/%m/%Y")


def parse_date(s: str) -> Optional[date]:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            pass
    return None


def file_size_human(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def file_extension(path: str) -> str:
    return Path(path).suffix.lower().lstrip(".")


def copy_file_to_store(src: str, dest_dir: Path, prefix: str = "") -> Path:
    """Copy a file into the attachments store with a unique name."""
    src_path = Path(src)
    ext = src_path.suffix
    h = hashlib.md5(f"{src}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:8]
    dest_name = f"{prefix}{src_path.stem}_{h}{ext}"
    dest_path = dest_dir / dest_name
    shutil.copy2(src, dest_path)
    return dest_path


def get_file_icon_name(ext: str) -> str:
    icons = {
        "pdf": "pdf",
        "doc": "word", "docx": "word",
        "xls": "excel", "xlsx": "excel",
        "ppt": "ppt", "pptx": "ppt",
        "jpg": "image", "jpeg": "image", "png": "image", "tif": "image", "tiff": "image",
        "eml": "email", "msg": "email",
        "zip": "archive", "rar": "archive", "7z": "archive",
        "txt": "text",
    }
    return icons.get(ext.lower(), "file")
