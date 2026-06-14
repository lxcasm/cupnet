$ErrorActionPreference = "Stop"
$backend = Join-Path $PSScriptRoot "backend"
$python = Join-Path $backend ".venv\Scripts\python.exe"
$main = Join-Path $backend "main.py"

if (-not (Test-Path $python)) {
    Write-Host "ERREUR: Python venv introuvable. Relancez LANCER-CupNet.bat"
    Read-Host "Entree pour fermer"
    exit 1
}

Start-Process -FilePath $python -ArgumentList "`"$main`"" -WorkingDirectory $backend -Verb RunAs
