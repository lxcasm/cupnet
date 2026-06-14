import subprocess
import threading

from app.blockers.base import BaseBlocker
from app.models.device import BlockMethod

_active_threads: dict[str, threading.Thread] = {}
_stop_flags: dict[str, threading.Event] = {}


def _key(ip: str) -> str:
    return ip


class PingFloodBlocker(BaseBlocker):
    """
    Sature la cible avec des pings continus.
    Méthode de déni de service légère — démonstration pédagogique uniquement.
    """

    method = BlockMethod.PING_FLOOD
    label = "Ping Flood"
    description = (
        "Envoie un flux continu de pings ICMP vers la cible pour saturer "
        "sa pile réseau. DoS léger à des fins de démonstration."
    )
    requires_admin = False

    def _run_flood(self, ip: str, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            subprocess.run(
                ["ping", "-n", "1", "-w", "100", ip],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )

    def block(self, ip: str, mac: str) -> None:
        key = _key(ip)
        if key in _active_threads and _active_threads[key].is_alive():
            return

        stop_event = threading.Event()
        _stop_flags[key] = stop_event
        thread = threading.Thread(
            target=self._run_flood,
            args=(ip, stop_event),
            daemon=True,
        )
        _active_threads[key] = thread
        thread.start()

    def unblock(self, ip: str, mac: str) -> None:
        key = _key(ip)
        if key in _stop_flags:
            _stop_flags[key].set()
        if key in _active_threads:
            _active_threads[key].join(timeout=3)
            del _active_threads[key]
        if key in _stop_flags:
            del _stop_flags[key]

    def is_active(self, ip: str, mac: str) -> bool:
        key = _key(ip)
        return key in _active_threads and _active_threads[key].is_alive()
