@echo off
setlocal EnableExtensions
title CupNet — compilation (optionnel)
cd /d "%~dp0.."

echo.
echo  ==========================================
echo   COMPILATION EXE — developpeurs seulement
echo  ==========================================
echo.
echo  Vous n'avez PAS besoin de compiler !
echo  Double-cliquez simplement sur CupNet.bat a la racine.
echo.
choice /C ON /M "Continuer quand meme"
if errorlevel 2 exit /b 0

cd backend
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt pyinstaller -q
) else (
    call .venv\Scripts\activate.bat
    pip install pyinstaller -q
)

taskkill /IM CupNet.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

pyinstaller CupNet.spec --noconfirm

if exist "dist\CupNet.exe" (
    echo.
    echo  OK : backend\dist\CupNet.exe
    echo  Attention : preferer CupNet.bat pour la version a jour.
) else (
    echo  Echec compilation.
)
echo.
pause
