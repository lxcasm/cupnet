@echo off
setlocal EnableExtensions
title CupNet v2.0
cd /d "%~dp0backend"

set "PY=%CD%\.venv\Scripts\python.exe"
set "PYW=%CD%\.venv\Scripts\pythonw.exe"

:: --- 1ere installation ---
if not exist "%PY%" (
    echo.
    echo  [1/2] Installation, patientez 1-2 min...
    where python >nul 2>&1
    if errorlevel 1 (
        echo.
        echo  ERREUR : installez Python depuis https://python.org
        echo  Cochez "Add Python to PATH".
        goto :erreur
    )
    python -m venv .venv
    if errorlevel 1 goto :erreur
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    if errorlevel 1 goto :erreur
    echo  Installation OK.
)

:: --- Verification ---
"%PY%" -c "from app.gui.theme import GIRO" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERREUR : fichiers manquants. Relancez CupNet.bat.
    goto :erreur
)

:: --- Lancement ---
echo.
echo  [2/2] CupNet v2.1 — par lxcasm
echo  Cliquez OUI sur la fenetre UAC ^(admin^).
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\launch.ps1"
if errorlevel 1 goto :erreur

echo.
echo  CupNet demarre. Verifiez la barre des taches.
echo  Cette fenetre se ferme dans 5 secondes...
timeout /t 5 /nobreak >nul
exit /b 0

:erreur
echo.
pause
exit /b 1
