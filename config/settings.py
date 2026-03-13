"""Application settings and configuration."""
import os
import json
from pathlib import Path

APP_NAME = "Σύστημα Πρωτοκόλλου"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Protokol2026"

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.environ.get("APPDATA", BASE_DIR)) / APP_NAME if os.name == "nt" else BASE_DIR / "data"
DB_PATH = DATA_DIR / "protokol.db"
ATTACHMENTS_DIR = DATA_DIR / "attachments"
SCANS_DIR = DATA_DIR / "scans"
EXPORTS_DIR = DATA_DIR / "exports"
CONFIG_FILE = DATA_DIR / "config.json"

# Ensure directories exist
for d in [DATA_DIR, ATTACHMENTS_DIR, SCANS_DIR, EXPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Default configuration
DEFAULT_CONFIG = {
    "organization_name": "Οργανισμός",
    "organization_address": "",
    "organization_phone": "",
    "organization_email": "",
    "organization_logo": "",
    "protocol_prefix": "",
    "protocol_year_reset": True,
    "smtp_host": "",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_password": "",
    "smtp_use_tls": True,
    "default_paper_size": "A4",
    "theme": "light",
    "language": "el",
    "auto_backup": True,
    "backup_days": 7,
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(saved)
            return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
