"""Détection et installation de Npcap (Windows)."""

from __future__ import annotations

import os
import subprocess
import tempfile
import urllib.request
import winreg
from collections.abc import Callable
from pathlib import Path

NPCAP_VERSION = "1.88"
NPCAP_URL = f"https://npcap.com/dist/npcap-{NPCAP_VERSION}.exe"
NPCAP_SITE = "https://npcap.com/"

ProgressCallback = Callable[[int, str], None]

_EXIT_MESSAGES = {
    0: "Npcap installé.",
    1: "Installation annulée.",
    2: "Installation interrompue.",
    350: "Échec — redémarrez le PC puis réessayez.",
    3010: "Npcap installé — un redémarrage peut être nécessaire.",
}


def is_npcap_installed() -> bool:
    """Vérifie si Npcap est installé (registre + fichiers système)."""
    for subkey in (r"SOFTWARE\Npcap", r"SOFTWARE\WOW6432Node\Npcap"):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey) as key:
                installed, _ = winreg.QueryValueEx(key, "Installed")
                if installed:
                    return True
        except OSError:
            pass

    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    if os.path.isfile(os.path.join(program_files, "Npcap", "Uninstall.exe")):
        return True

    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    if os.path.isfile(os.path.join(system_root, "System32", "Npcap", "wpcap.dll")):
        return True

    return False


def default_installer_path() -> Path:
    return Path(tempfile.gettempdir()) / "cupnet" / f"npcap-{NPCAP_VERSION}.exe"


def download_npcap(
    dest: Path | None = None,
    on_progress: ProgressCallback | None = None,
) -> Path:
    """Télécharge l'installateur officiel Npcap."""
    target = dest or default_installer_path()
    target.parent.mkdir(parents=True, exist_ok=True)

    request = urllib.request.Request(NPCAP_URL, headers={"User-Agent": "CupNet/2.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        total = int(response.headers.get("Content-Length", 0) or 0)
        downloaded = 0
        chunk_size = 256 * 1024

        with open(target, "wb") as handle:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                handle.write(chunk)
                downloaded += len(chunk)
                if on_progress:
                    if total > 0:
                        pct = min(100, int(downloaded * 100 / total))
                        on_progress(pct, f"Téléchargement Npcap… {pct} %")
                    else:
                        on_progress(0, "Téléchargement Npcap…")

    if on_progress:
        on_progress(100, "Téléchargement terminé")

    return target


def run_npcap_installer(installer: Path) -> tuple[int, str]:
    """
    Lance l'installateur graphique Npcap et attend la fin.
    L'utilisateur doit accepter la licence (pas de mode silencieux en version gratuite).
    """
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    proc = subprocess.Popen(
        [str(installer), "/winpcap_mode=yes"],
        startupinfo=startupinfo,
    )
    code = proc.wait()
    message = _EXIT_MESSAGES.get(code, f"Installateur terminé (code {code}).")
    return code, message
