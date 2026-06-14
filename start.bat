@echo off
setlocal
title CupNet (sans admin)
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
    echo Installation...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
)

echo CupNet v2.0 — par lxcasm
.venv\Scripts\python.exe main.py
if errorlevel 1 pause
