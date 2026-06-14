@echo off
setlocal EnableExtensions
title CupNet
cd /d "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
    echo.
    echo  [1/2] Installation des dependances, patientez 1-2 min...
    cd backend
    where python >nul 2>&1
    if errorlevel 1 (
        echo.
        echo  ERREUR : Python non installe.
        echo  Installez Python depuis https://www.python.org/downloads/
        pause
        exit /b 1
    )
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
)

echo.
echo  ========================================
echo   CupNet v2.0 — par lxcasm
echo  ========================================
echo.
echo  Ouverture en administrateur...
echo  ^>^>^> Cliquez OUI sur la fenetre UAC ^<^<^<
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch-admin.ps1"

echo.
echo  Si rien ne s'ouvre, essayez start.bat
echo.
pause
