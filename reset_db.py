"""
reset_db.py  –  Καθαρισμός δοκιμαστικών εγγραφών Πρωτοκόλλου
=============================================================
Τρέξε από τον φάκελο της εφαρμογής:
    python reset_db.py

Τι κάνει:
  ✔  Δημιουργεί αυτόματα backup της βάσης πριν από οποιαδήποτε αλλαγή
  ✔  Διαγράφει όλα τα πρωτόκολλα (protocols)
  ✔  Μηδενίζει τους μετρητές αριθμών (protocol_counters)
  ✔  Διαγράφει συνημμένα αρχεία εγγραφών (attachments)
  ✔  Διαγράφει ιστορικό αλλαγών (protocol_history)
  ✔  Διαγράφει logs email (email_logs)
  ✔  Κρατάει: χρήστες, τύπους εγγράφων, τμήματα, θέσεις,
              υπαλλήλους, επαφές, φακέλους, θέματα, ρυθμίσεις

"""
import sys
import shutil
from datetime import datetime
from pathlib import Path

# ── Βεβαιώσου ότι τρέχει από τον σωστό φάκελο ───────────────────────────────
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

try:
    from config.settings import DB_PATH, DATA_DIR
    from database.db import init_db, get_session
    from database.models import (
        Protocol, ProtocolCounter, Attachment,
        ProtocolHistory, EmailLog,
    )
except ImportError as e:
    print(f"[ΣΦΑΛΜΑ] Δεν βρέθηκαν τα modules της εφαρμογής: {e}")
    print("Βεβαιώσου ότι το reset_db.py βρίσκεται στον κεντρικό φάκελο της εφαρμογής.")
    sys.exit(1)


def backup_database() -> Path:
    """Δημιουργεί αντίγραφο ασφαλείας και επιστρέφει το path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DATA_DIR / f"protokol_backup_{timestamp}.db"
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def reset_protocols():
    """Διαγράφει μόνο τα πρωτόκολλα και τα σχετικά δεδομένα τους."""
    session = get_session()
    try:
        # Μέτρηση πριν
        total = session.query(Protocol).count()
        attachments = session.query(Attachment).count()
        history = session.query(ProtocolHistory).count()
        email_logs = session.query(EmailLog).count()
        counters = session.query(ProtocolCounter).count()

        print(f"\n  Βρέθηκαν:")
        print(f"    • {total:>5} πρωτόκολλα")
        print(f"    • {attachments:>5} συνημμένα")
        print(f"    • {history:>5} εγγραφές ιστορικού")
        print(f"    • {email_logs:>5} logs email")
        print(f"    • {counters:>5} μετρητές αριθμών")

        if total == 0 and attachments == 0:
            print("\n  ✔  Η βάση είναι ήδη καθαρή. Δεν χρειάζεται διαγραφή.")
            return

        confirm = input("\n  Θέλεις να συνεχίσεις με τη διαγραφή; (ναι/όχι): ").strip().lower()
        if confirm not in ("ναι", "nai", "yes", "y", "ν"):
            print("\n  Ακύρωση. Δεν έγινε καμία αλλαγή.")
            return

        # Διαγραφή με σωστή σειρά (foreign keys)
        session.query(EmailLog).delete(synchronize_session=False)
        session.query(ProtocolHistory).delete(synchronize_session=False)
        session.query(Attachment).delete(synchronize_session=False)
        session.query(Protocol).delete(synchronize_session=False)

        # Μηδενισμός μετρητών (ξεκινάει από 1 η νέα αρίθμηση)
        session.query(ProtocolCounter).delete(synchronize_session=False)

        session.commit()
        print("\n  ✔  Διαγραφή ολοκληρώθηκε επιτυχώς!")
        print("  ✔  Οι μετρητές αριθμών μηδενίστηκαν.")
        print("  ✔  Χρήστες, ρυθμίσεις και λοιπά δεδομένα διατηρήθηκαν.")

    except Exception as e:
        session.rollback()
        print(f"\n  [ΣΦΑΛΜΑ] {e}")
        raise
    finally:
        session.close()


def main():
    print("=" * 60)
    print("  ΚΑΘΑΡΙΣΜΟΣ ΔΟΚΙΜΑΣΤΙΚΩΝ ΕΓΓΡΑΦΩΝ ΠΡΩΤΟΚΟΛΛΟΥ")
    print("=" * 60)

    # Έλεγχος ύπαρξης βάσης
    if not DB_PATH.exists():
        print(f"\n  [ΣΦΑΛΜΑ] Δεν βρέθηκε βάση δεδομένων στο:\n  {DB_PATH}")
        print("  Εκκίνησε πρώτα την εφαρμογή για να δημιουργηθεί η βάση.")
        sys.exit(1)

    print(f"\n  Βάση δεδομένων: {DB_PATH}")

    # Backup
    try:
        backup = backup_database()
        print(f"  Backup αποθηκεύτηκε: {backup.name}")
    except Exception as e:
        print(f"\n  [ΣΦΑΛΜΑ] Αποτυχία backup: {e}")
        sys.exit(1)

    # Σύνδεση & διαγραφή
    try:
        init_db()
        reset_protocols()
    except Exception as e:
        print(f"\n  [ΣΦΑΛΜΑ] {e}")
        print(f"\n  Το backup σου είναι ασφαλές στο: {backup}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  Η εφαρμογή είναι έτοιμη για κανονική χρήση.")
    print("=" * 60)


if __name__ == "__main__":
    main()
