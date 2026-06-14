$ErrorActionPreference = "Stop"
$backend = Join-Path (Split-Path $PSScriptRoot -Parent) "backend"
$python = Join-Path $backend ".venv\Scripts\python.exe"
$main = Join-Path $backend "main.py"

if (-not (Test-Path $python)) {
    Write-Host ""
    Write-Host "  ERREUR : installation incomplete."
    Write-Host "  Relancez CupNet.bat"
    Write-Host ""
    Read-Host "Entree pour fermer"
    exit 1
}

Start-Process -FilePath $python -ArgumentList "`"$main`"" -WorkingDirectory $backend -Verb RunAs
