import ctypes
import re
import subprocess
import time


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def get_default_gateway() -> str | None:
    """Retourne l'IP de la passerelle par défaut (Windows)."""
    result = subprocess.run(
        ["route", "print", "0.0.0.0"],
        capture_output=True,
        text=True,
        encoding="cp850",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    )
    for line in result.stdout.splitlines():
        if "0.0.0.0" in line and "On-link" not in line:
            parts = line.split()
            if len(parts) >= 3 and parts[0] == "0.0.0.0":
                gateway = parts[2]
                if re.match(r"\d{1,3}(\.\d{1,3}){3}$", gateway):
                    return gateway
    return None


def ping_latency_ms(ip: str, timeout_ms: int = 800) -> int | None:
    """Mesure la latence ICMP vers une IP (ms), ou None si injoignable."""
    start = time.perf_counter()
    result = subprocess.run(
        ["ping", "-n", "1", "-w", str(timeout_ms), ip],
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    )
    if result.returncode != 0:
        return None
    elapsed = int((time.perf_counter() - start) * 1000)
    match = re.search(r"(?:temps?|time)[=<]\s*(\d+)\s*ms", result.stdout.decode("cp850", errors="replace"), re.I)
    if match:
        return int(match.group(1))
    return elapsed


def format_duration(seconds: float) -> str:
    """Formate une durée en texte lisible (ex: 2h 15m, 45s)."""
    total = max(0, int(seconds))
    if total < 60:
        return f"{total}s"
    minutes, secs = divmod(total, 60)
    if minutes < 60:
        return f"{minutes}m {secs}s" if secs else f"{minutes}m"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {minutes}m"
    days, hours = divmod(hours, 24)
    return f"{days}j {hours}h"
