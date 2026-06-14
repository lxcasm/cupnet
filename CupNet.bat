@echo off
setlocal EnableExtensions
title CupNet v2.0
cd /d "%~dp0"

set "BACKEND=%~dp0backend"
set "PYTHON=%BACKEND%\.venv\Scripts\python.exe"
set "MAIN=%BACKEND%\main.py"

:: --- Installation automatique (1ere fois) ---
if not exist "%PYTHON%" (
    echo.
    echo  [1/2] Premiere installation, patientez 1-2 min...
    where python >nul 2>&1
    if errorlevel 1 (
        echo.
        echo  ERREUR : Python non installe.
        echo  Telechargez-le sur https://python.org
        echo  Cochez "Add Python to PATH" a l'installation.
        echo.
        pause
        exit /b 1
    )
    pushd "%BACKEND%"
    python -m venv .venv
    if errorlevel 1 (
        echo ERREUR creation environnement Python.
        pause
        popd
        exit /b 1
    )
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERREUR installation des dependances.
        pause
        popd
        exit /b 1
    )
    popd
    echo  Installation terminee.
)

:: --- Test demarrage ---
"%PYTHON%" -c "from app.gui.theme import GIRO" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERREUR : application corrompue ou incomplete.
    echo  Relancez CupNet.bat ou reinstallez les dependances.
    echo.
    pause
    exit /b 1
)

:: --- Lancement admin ---
echo.
echo  [2/2] CupNet v2.0 — par lxcasm
echo.
echo  >>> Cliquez OUI sur la fenetre UAC Windows <<<
echo  (obligatoire pour couper la connexion ARP)
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Start-Process -FilePath '%PYTHON%' -ArgumentList '\"%MAIN%\"' -WorkingDirectory '%BACKEND%' -Verb RunAs"

timeout /t 2 /nobreak >nul

:: Si l'admin a ete refuse, proposer sans admin
tasklist /FI "WINDOWTITLE eq CupNet*" 2>nul | find /I "python" >nul
if errorlevel 1 (
    echo.
    echo  Lancement sans admin ^(scan OK, coupure ARP limitee^)...
    echo.
    pushd "%BACKEND%"
    start "" "%PYTHON%" "%MAIN%"
    popd
)

echo.
echo  CupNet demarre. Si rien ne s'affiche, verifiez la barre des taches.
echo.
timeout /t 4 /nobreak >nul
exit /b 0
