"""Document archiving service.

For each protocol with attachments, creates a subfolder named after the
protocol number and copies all attached files there.
"""
from __future__ import annotations
import os
import shutil
from pathlib import Path

from config.settings import ATTACHMENTS_DIR, load_config


def _sanitize_folder_name(name: str) -> str:
    """Replace characters that are invalid in folder names."""
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "-")
    return name.strip()


def archive_protocol_attachments(protocol, config: dict | None = None) -> tuple[bool, str]:
    """
    Archive all attachments of a protocol into a dedicated folder.

    Creates: <archive_path>/<protocol_number>/<filename>

    Returns (success, message).
    """
    if config is None:
        config = load_config()

    if not config.get("archive_enabled", False):
        return False, "Η αρχειοθέτηση δεν είναι ενεργοποιημένη."

    archive_root = config.get("archive_path", "").strip()
    if not archive_root:
        return False, "Δεν έχει οριστεί διαδρομή αρχειοθέτησης."

    archive_root_path = Path(archive_root)
    if not archive_root_path.exists():
        try:
            archive_root_path.mkdir(parents=True, exist_ok=True)
        except Exception as ex:
            return False, f"Αδυναμία δημιουργίας φακέλου αρχειοθέτησης: {ex}"

    # Folder name = sanitized protocol number (e.g. "123-2026" or "AK-5-2026")
    proto_folder_name = _sanitize_folder_name(
        protocol.protocol_full or str(protocol.protocol_number or "unknown")
    )
    proto_folder = archive_root_path / proto_folder_name

    try:
        proto_folder.mkdir(parents=True, exist_ok=True)
    except Exception as ex:
        return False, f"Αδυναμία δημιουργίας φακέλου πρωτοκόλλου: {ex}"

    if not protocol.attachments:
        return True, f"Φάκελος δημιουργήθηκε: {proto_folder}"

    copied = 0
    errors = []
    for att in protocol.attachments:
        src = Path(att.file_path) if att.file_path else None
        if src is None or not src.exists():
            # Try relative to ATTACHMENTS_DIR
            if att.file_path:
                src = ATTACHMENTS_DIR / att.file_path
            if src is None or not src.exists():
                errors.append(f"Δεν βρέθηκε: {att.original_name or att.file_path}")
                continue

        dest_name = att.original_name or src.name
        dest = proto_folder / dest_name
        # Avoid overwriting with a suffix counter
        counter = 1
        stem = Path(dest_name).stem
        suffix = Path(dest_name).suffix
        while dest.exists():
            dest = proto_folder / f"{stem}_{counter}{suffix}"
            counter += 1

        try:
            shutil.copy2(str(src), str(dest))
            copied += 1
        except Exception as ex:
            errors.append(f"{att.original_name}: {ex}")

    msg = f"Αρχειοθετήθηκαν {copied} αρχεία στον φάκελο:\n{proto_folder}"
    if errors:
        msg += "\n\nΣφάλματα:\n" + "\n".join(errors)

    return True, msg
