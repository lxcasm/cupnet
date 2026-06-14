import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable

from app.blockers.registry import get_blocker, list_blockers
from app.core.network_utils import format_duration, is_admin, ping_latency_ms
from app.models.device import BlockMethod, Device, ScanResult
from app.scanner.device_scanner import detect_network_warning, scan_network

ProgressCallback = Callable[[int, str], None]


@dataclass
class _DeviceSession:
    first_seen: float
    last_seen: float
    blocked_at: float | None = None
    last_ping_ms: int | None = None


class DeviceManager:
    def __init__(self) -> None:
        self._blocked: dict[str, Device] = {}
        self._last_scan: list[Device] = []
        self._sessions: dict[str, _DeviceSession] = {}
        self._last_network = "—"
        self._last_interface = "—"
        self._last_duration_ms = 0
        self._last_warning: str | None = None
        self._session_start = time.time()

    @property
    def last_warning(self) -> str | None:
        return self._last_warning

    @property
    def last_network(self) -> str:
        return self._last_network

    @property
    def last_interface(self) -> str:
        return self._last_interface

    @property
    def last_duration_ms(self) -> int:
        return self._last_duration_ms

    @property
    def is_admin(self) -> bool:
        return is_admin()

    @property
    def session_duration_sec(self) -> int:
        return int(time.time() - self._session_start)

    def get_methods(self) -> list[dict]:
        return list_blockers()

    def _enrich_device(self, device: Device, now: float | None = None) -> Device:
        now = now or time.time()
        session = self._sessions.get(device.mac)

        if session:
            device.first_seen_at = session.first_seen
            device.last_seen_at = session.last_seen
            device.online_duration_sec = int(now - session.first_seen)
            device.ping_ms = session.last_ping_ms

        if device.mac in self._blocked:
            blocked = self._blocked[device.mac]
            device.blocked = True
            device.block_method = blocked.block_method
            if blocked.blocked_at:
                device.blocked_at = blocked.blocked_at
                device.block_duration_sec = int(now - blocked.blocked_at)

        return device

    def scan(self, progress_cb: ProgressCallback | None = None) -> ScanResult:
        devices, net_info, duration = scan_network(progress_cb)
        now = time.time()

        if progress_cb:
            progress_cb(95, "Mesure des latences…")

        with ThreadPoolExecutor(max_workers=16) as pool:
            futures = {
                pool.submit(ping_latency_ms, device.ip): device
                for device in devices
            }
            for future in as_completed(futures):
                device = futures[future]
                device.ping_ms = future.result()
                if device.mac not in self._sessions:
                    self._sessions[device.mac] = _DeviceSession(first_seen=now, last_seen=now)
                else:
                    self._sessions[device.mac].last_seen = now
                self._sessions[device.mac].last_ping_ms = device.ping_ms

        for device in devices:
            if device.mac in self._blocked:
                blocked = self._blocked[device.mac]
                device.blocked = True
                device.block_method = blocked.block_method
            self._enrich_device(device, now)

        self._last_scan = devices
        self._last_network = str(net_info.network)
        self._last_interface = net_info.interface
        self._last_duration_ms = duration
        self._last_warning = detect_network_warning(net_info)

        return ScanResult(
            devices=devices,
            network=self._last_network,
            interface=self._last_interface,
            scan_duration_ms=duration,
            warning=self._last_warning,
        )

    def get_devices(self) -> list[Device]:
        now = time.time()
        return [self._enrich_device(device.model_copy(), now) for device in self._last_scan]

    def has_blocked_devices(self) -> bool:
        return bool(self._blocked)

    def get_device_summary(self, mac: str) -> str:
        device = self._find_device(mac)
        if not device:
            return ""

        now = time.time()
        self._enrich_device(device, now)
        lines = [
            f"IP : {device.ip}",
            f"MAC : {device.mac}",
            f"Fabricant : {device.vendor or '—'}",
            f"Nom : {device.hostname or '—'}",
        ]
        if device.online_duration_sec is not None:
            lines.append(f"Présent sur le réseau : {format_duration(device.online_duration_sec)}")
        if device.ping_ms is not None:
            lines.append(f"Latence : {device.ping_ms} ms")
        else:
            lines.append("Latence : injoignable")
        if device.blocked and device.block_duration_sec is not None:
            lines.append(f"Temps bloqué : {format_duration(device.block_duration_sec)}")
        return "\n".join(lines)

    def _find_device(self, mac: str) -> Device | None:
        normalized = mac.upper().replace("-", ":")
        for device in self._last_scan:
            if device.mac.upper().replace("-", ":") == normalized:
                return device
        for device in self._blocked.values():
            if device.mac.upper().replace("-", ":") == normalized:
                return device
        return None

    def block(self, mac: str, method: BlockMethod) -> tuple[Device, str]:
        device = self._find_device(mac)
        if not device:
            raise ValueError("Appareil introuvable. Lancez un scan d'abord.")

        if method == BlockMethod.ARP_SPOOF and not is_admin():
            raise RuntimeError(
                "La coupure ARP nécessite d'exécuter CupNet en tant qu'administrateur."
            )

        blocker = get_blocker(method)
        try:
            blocker.block(device.ip, device.mac)
        except (subprocess.CalledProcessError, RuntimeError) as exc:
            raise RuntimeError(str(exc)) from exc

        if not blocker.is_active(device.ip, device.mac) and method != BlockMethod.FIREWALL:
            raise RuntimeError(
                f"La coupure via {blocker.label} ne semble pas active. "
                "Vérifiez Npcap et les droits admin."
            )

        now = time.time()
        device.blocked = True
        device.block_method = method
        device.blocked_at = now
        self._blocked[device.mac] = device

        if device.mac in self._sessions:
            self._sessions[device.mac].blocked_at = now

        return device, f"{device.ip} — connexion coupée via {blocker.label}"

    def unblock(self, mac: str) -> tuple[Device, str]:
        device = self._find_device(mac)
        if not device:
            raise ValueError("Appareil introuvable.")

        if device.mac not in self._blocked and not device.block_method:
            raise ValueError("Cet appareil n'est pas bloqué.")

        if device.block_method:
            blocker = get_blocker(device.block_method)
            blocker.unblock(device.ip, device.mac)

        device.blocked = False
        device.block_method = None
        device.blocked_at = None
        device.block_duration_sec = None
        self._blocked.pop(device.mac, None)

        if device.mac in self._sessions:
            self._sessions[device.mac].blocked_at = None

        return device, f"{device.ip} — connexion rétablie"
