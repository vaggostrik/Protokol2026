"""Backup and restore service."""
from __future__ import annotations
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from config.settings import DB_PATH, ATTACHMENTS_DIR, SCANS_DIR, DATA_DIR, EXPORTS_DIR


def create_backup(dest_dir: str | None = None) -> str:
    """
    Create a ZIP backup of the database and all attachments.
    Returns the path to the created ZIP file.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"protokol_backup_{ts}.zip"
    dest = Path(dest_dir) if dest_dir else EXPORTS_DIR
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / filename

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # Database
        if DB_PATH.exists():
            zf.write(DB_PATH, "database/protokol.db")

        # Attachments
        for folder, arcname in [(ATTACHMENTS_DIR, "attachments"), (SCANS_DIR, "scans")]:
            if folder.exists():
                for file in folder.rglob("*"):
                    if file.is_file():
                        zf.write(file, f"{arcname}/{file.name}")

    return str(zip_path)


def restore_backup(zip_path: str) -> tuple[bool, str]:
    """
    Restore from a backup ZIP.
    Returns (success, message).
    """
    zp = Path(zip_path)
    if not zp.exists():
        return False, "Το αρχείο backup δεν βρέθηκε."

    try:
        # Backup current db first
        if DB_PATH.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(DB_PATH, DB_PATH.with_suffix(f".db.bak_{ts}"))

        with zipfile.ZipFile(zp, "r") as zf:
            for member in zf.namelist():
                if member.startswith("database/"):
                    target = DATA_DIR / Path(member).name
                    with zf.open(member) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                elif member.startswith("attachments/"):
                    target = ATTACHMENTS_DIR / Path(member).name
                    with zf.open(member) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                elif member.startswith("scans/"):
                    target = SCANS_DIR / Path(member).name
                    with zf.open(member) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)

        return True, "Η επαναφορά ολοκληρώθηκε. Επανεκκινήστε την εφαρμογή."
    except Exception as ex:
        return False, str(ex)


def get_backup_info(zip_path: str) -> dict:
    """Return info about a backup file."""
    zp = Path(zip_path)
    if not zp.exists():
        return {}
    stat = zp.stat()
    try:
        with zipfile.ZipFile(zp, "r") as zf:
            files = zf.namelist()
            db_files = [f for f in files if f.startswith("database/")]
            att_files = [f for f in files if f.startswith("attachments/")]
    except Exception:
        files, db_files, att_files = [], [], []
    return {
        "filename": zp.name,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
        "total_files": len(files),
        "attachments": len(att_files),
        "has_db": len(db_files) > 0,
    }
