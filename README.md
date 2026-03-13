# Σύστημα Πρωτοκόλλου

Ηλεκτρονικό Σύστημα Διαχείρισης Εισερχόμενων/Εξερχόμενων Εγγράφων για Windows.

## Χαρακτηριστικά

- **Ηλεκτρονική Καταχώρηση** εισερχόμενων, εξερχόμενων και εσωτερικών εγγράφων με αυτόματο μοναδικό αριθμό πρωτοκόλλου
- **Γρήγορη Αναζήτηση** με πολλαπλά φίλτρα (ημερομηνία, κατεύθυνση, αποστολέας, θέμα, κατάσταση, προτεραιότητα κ.ά.)
- **Ψηφιοποίηση** – Σύνδεση με σαρωτές TWAIN, εισαγωγή εξωτερικών αρχείων (PDF, Word, Excel, Email)
- **Document Flow Management** – Παρακολούθηση σταδίων διεκπεραίωσης, χαρακτηρισμός (Επείγον, Απόρρητο κλπ)
- **Αυτόματη Αποστολή Email** συνδεδεμένη με τον αριθμό πρωτοκόλλου
- **Βεβαίωση Παραλαβής** – Εκτύπωση επιβεβαίωσης σε PDF
- **Βιβλίο Πρωτοκόλλου** – Εκτύπωση σε A4/A3 (οριζόντια/κατακόρυφα)
- **Παραμετρικό** – Τμήματα, θέσεις, υπάλληλοι, επαφές, πίνακες αποδεκτών, φάκελοι αρχείου, θέματα
- **Βάση SQLite** – Δεν απαιτεί εξωτερικό server

## Εγκατάσταση

### Απαιτήσεις
- Python 3.10+
- Windows 10/11 (συνιστάται) ή Linux/macOS

### Ανάπτυξη

```bash
pip install -r requirements.txt
python main.py
```

### Δημιουργία Windows Executable

```bash
pip install cx_Freeze
python setup.py build
```

### Δημιουργία Windows Installer (Inno Setup)

1. Εκτελέστε `python setup.py build`
2. Ανοίξτε `setup_installer.iss` με το [Inno Setup](https://jrsoftware.org/isinfo.php)
3. Compile → `installer/Protokol2026_Setup.exe`

## Δομή Έργου

```
Protokol2026/
├── main.py                  # Entry point
├── config/
│   └── settings.py          # Application settings
├── database/
│   ├── models.py            # SQLAlchemy ORM models
│   └── db.py                # Database operations
├── ui/
│   ├── main_window.py       # Main window
│   ├── protocol_form.py     # Protocol create/edit form
│   ├── search_panel.py      # Search & results view
│   ├── settings_panel.py    # Parametric settings tabs
│   ├── dialogs.py           # Helper dialogs
│   ├── employee_dialog.py   # Employee CRUD dialog
│   ├── email_dialog.py      # Email compose dialog
│   ├── print_dialog.py      # Protocol book print dialog
│   ├── widgets.py           # Reusable Qt widgets
│   └── styles.py            # Qt stylesheets
├── services/
│   ├── scanner.py           # TWAIN scanner integration
│   └── email_service.py     # SMTP email service
├── reports/
│   ├── receipt.py           # Receipt PDF generation
│   └── protocol_book.py     # Protocol Book PDF
└── utils/
    └── helpers.py           # Utility functions
```

## Χρήση

1. Εκκινήστε την εφαρμογή: `python main.py`
2. Ρυθμίστε τα στοιχεία οργανισμού από **Παραμετρικά → Οργανισμός**
3. Προσθέστε τμήματα, υπαλλήλους, επαφές
4. Καταχωρείστε έγγραφα με **+ Εισερχόμενο / + Εξερχόμενο / + Εσωτερικό**
5. Εκτυπώστε βιβλίο πρωτοκόλλου από **Εκτυπώσεις → Βιβλίο Πρωτοκόλλου**

## Scanner (TWAIN)

Για χρήση φυσικού σαρωτή στα Windows:
```bash
pip install pytwain
```

## Τεχνολογίες

| Στοιχείο | Τεχνολογία |
|----------|-----------|
| UI | PyQt6 |
| Βάση δεδομένων | SQLite + SQLAlchemy |
| PDF | ReportLab |
| Scanner | pytwain (TWAIN) |
| Email | smtplib |
| Αρχεία | python-docx, openpyxl, Pillow |
