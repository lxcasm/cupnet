@echo off
setlocal EnableExtensions
title CupNet v2.0
cd /d "%~dp0"

:: --- Installation automatique (1ere fois) ---
if not exist "backend\.venv\Scripts\python.exe" (
    echo.
    echo  [1/2] Premiere installation, patientez 1-2 min...
    where python >nul 2>&1
    if errorlevel 1 (
        echo.
        echo  Python manquant : installez-le sur https://python.org
        echo  Cochez "Add Python to PATH" a l'installation.
        pause
        exit /b 1
    )
    cd backend
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt -q
    cd ..
    echo  Installation terminee.
)

:: --- Lancement ---
echo.
echo  [2/2] CupNet v2.0 — par lxcasm
echo  Cliquez OUI sur la fenetre UAC Windows.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\launch.ps1"

exit /b 0
