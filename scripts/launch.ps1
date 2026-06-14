$ErrorActionPreference = "Stop"

$root = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $root "backend"
$pythonw = Join-Path $backend ".venv\Scripts\pythonw.exe"
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (Test-Path $pythonw) {
    $exe = $pythonw
} elseif (Test-Path $python) {
    $exe = $python
} else {
    Write-Host ""
    Write-Host "  ERREUR : Python introuvable."
    Write-Host "  Relancez CupNet.bat pour installer."
    Write-Host ""
    Read-Host "Entree pour fermer"
    exit 1
}

try {
    Start-Process -FilePath $exe -ArgumentList "main.py" -WorkingDirectory $backend -Verb RunAs
    exit 0
} catch {
    Write-Host ""
    Write-Host "  Echec lancement admin : $_"
    Write-Host "  Lancement sans admin..."
    Start-Process -FilePath $exe -ArgumentList "main.py" -WorkingDirectory $backend
    exit 0
}
