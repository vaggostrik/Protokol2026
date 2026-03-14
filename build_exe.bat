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
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] %PYVER% found

echo.
echo [1/4] Updating pip...
python -m pip install --upgrade pip --quiet

echo [2/4] Installing libraries...
python -m pip install PyQt6 SQLAlchemy reportlab Pillow python-dateutil pywin32 pyinstaller --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install libraries! Try running as Administrator.
    pause
    exit /b 1
)
echo [OK] Libraries installed

echo.
echo [3/4] Cleaning previous build...
if exist "dist\Protokol2026" rmdir /s /q "dist\Protokol2026"
if exist "build\Protokol2026" rmdir /s /q "build\Protokol2026"

echo [4/4] Building EXE (3-5 minutes)...
python -m PyInstaller protokol.spec --noconfirm
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo   1. Run as Administrator
    echo   2. Disable antivirus temporarily
    echo   3. Check build\warn-Protokol2026.txt
    pause
    exit /b 1
)
echo [OK] EXE created!

powershell -Command "Compress-Archive -Path 'dist\Protokol2026\*' -DestinationPath 'Protokol2026_Windows.zip' -Force" >nul 2>&1
echo [OK] ZIP: Protokol2026_Windows.zip

echo.
echo ============================================
echo   SUCCESS!  dist\Protokol2026\Protokol2026.exe
echo ============================================
echo.
explorer dist\Protokol2026
pause
