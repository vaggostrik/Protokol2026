@echo off
title Build EXE - Protokol2026

echo ============================================
echo   Protokol2026 - Build Windows EXE
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo.
    echo Please download Python from: https://www.python.org/downloads/
    echo During installation, check "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [1/4] Updating pip...
python -m pip install --upgrade pip --quiet

echo [2/4] Installing libraries (this may take a few minutes)...
python -m pip install PyQt6 SQLAlchemy reportlab python-docx openpyxl Pillow python-dateutil pywin32 pyinstaller --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install libraries!
    pause
    exit /b 1
)

echo [3/4] Building EXE (please wait 2-5 minutes)...
python -m PyInstaller protokol.spec --noconfirm
if errorlevel 1 (
    echo [ERROR] Failed to build EXE!
    pause
    exit /b 1
)

echo [4/4] Creating ZIP archive...
powershell -Command "Compress-Archive -Path 'dist\Protokol2026\*' -DestinationPath 'Protokol2026_Windows.zip' -Force"

echo.
echo ============================================
echo   SUCCESS!
echo ============================================
echo.
echo EXE location:
echo   dist\Protokol2026\Protokol2026.exe
echo.
echo ZIP file:
echo   Protokol2026_Windows.zip
echo.

explorer dist\Protokol2026

pause
