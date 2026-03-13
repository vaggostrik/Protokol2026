@echo off
chcp 65001 >nul
title Δημιουργία EXE - Σύστημα Πρωτοκόλλου

echo ============================================
echo   Δημιουργία Εκτελέσιμου (EXE)
echo   Σύστημα Πρωτοκόλλου
echo ============================================
echo.

:: Έλεγχος Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ΣΦΑΛΜΑ] Η Python δεν βρέθηκε!
    echo.
    echo Κατεβάστε Python από: https://www.python.org/downloads/
    echo Κατά την εγκατάσταση, τσεκάρετε το "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [1/4] Ενημέρωση pip...
python -m pip install --upgrade pip --quiet

echo [2/4] Εγκατάσταση βιβλιοθηκών...
pip install PyQt6 SQLAlchemy reportlab python-docx openpyxl Pillow python-dateutil pywin32 pyinstaller --quiet
if errorlevel 1 (
    echo [ΣΦΑΛΜΑ] Αποτυχία εγκατάστασης βιβλιοθηκών!
    pause
    exit /b 1
)

echo [3/4] Δημιουργία EXE (παρακαλώ περιμένετε 2-5 λεπτά)...
pyinstaller protokol.spec --noconfirm
if errorlevel 1 (
    echo [ΣΦΑΛΜΑ] Αποτυχία δημιουργίας EXE!
    pause
    exit /b 1
)

echo [4/4] Συμπίεση σε ZIP...
powershell -Command "Compress-Archive -Path 'dist\Protokol2026\*' -DestinationPath 'Protokol2026_Windows.zip' -Force"

echo.
echo ============================================
echo   ΕΠΙΤΥΧΙΑ!
echo ============================================
echo.
echo Το εκτελέσιμο βρίσκεται στον φάκελο:
echo   dist\Protokol2026\Protokol2026.exe
echo.
echo Το ZIP αρχείο:
echo   Protokol2026_Windows.zip
echo.

:: Άνοιγμα φακέλου
explorer dist\Protokol2026

pause
