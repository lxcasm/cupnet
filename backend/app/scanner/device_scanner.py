import concurrent.futures
import ipaddress
import re
import socket
import subprocess
import time
from dataclasses import dataclass
from typing import Callable

from app.core.network_utils import get_default_gateway
from app.models.device import Device

OUI_VENDORS: dict[str, str] = {
    "00:50:56": "VMware",
    "00:0C:29": "VMware",
    "00:1A:2B": "Apple",
    "3C:22:FB": "Apple",
    "A4:83:E7": "Apple",
    "DC:A6:32": "Raspberry Pi",
    "B8:27:EB": "Raspberry Pi",
    "00:1B:44": "Samsung",
    "34:CE:00": "Samsung",
    "00:17:88": "Philips Hue",
    "44:65:0D": "Amazon",
    "50:DC:E7": "Amazon",
    "18:B4:30": "Google/Nest",
    "AC:BC:32": "Google",
    "00:1E:C9": "Sony",
    "28:6C:07": "Xiaomi",
    "64:09:80": "Xiaomi",
    "00:E0:4C": "Realtek",
    "00:25:90": "Super Micro",
    "F4:F5:D8": "Google",
    "E4:5F:01": "Raspberry Pi",
}

SKIP_ADAPTER_KEYWORDS = (
    "npcap",
    "loopback",
    "virtualbox",
    "vmware",
    "hyper-v",
    "vethernet",
    "bluetooth",
    "tunnel",
    "pseudo-interface",
    "mobile broadband",
    "tap-windows",
    "wireguard",
    "docker",
    "wsl",
    "miniport",
    "isatap",
    "teredo",
)

ProgressCallback = Callable[[int, str], None]


@dataclass
class NetworkInfo:
    interface: str
    ip: str
    network: ipaddress.IPv4Network


@dataclass
class _AdapterBlock:
    name: str
    ip: str | None = None
    mask: str | None = None


def _normalize_mac(mac: str) -> str:
    mac = mac.upper().replace("-", ":")
    parts = mac.split(":")
    return ":".join(p.zfill(2) for p in parts)


def _lookup_vendor(mac: str) -> str | None:
    prefix = ":".join(_normalize_mac(mac).split(":")[:3])
    return OUI_VENDORS.get(prefix)


def _resolve_hostname(ip: str) -> str | None:
    try:
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(0.8)
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, socket.gaierror, OSError, TimeoutError):
        return None
    finally:
        socket.setdefaulttimeout(old_timeout)


def _parse_ipconfig_adapters(output: str) -> list[_AdapterBlock]:
    adapters: list[_AdapterBlock] = []
    current: _AdapterBlock | None = None

    for line in output.splitlines():
        if re.match(r"^[^\s].*:\s*$", line):
            title = line.rstrip(":").strip()
            if "configuration" in title.lower() or title.lower().startswith("windows ip"):
                continue
            if current and current.ip and current.mask:
                adapters.append(current)
            current = _AdapterBlock(name=title)
            continue

        if not current:
            continue

        stripped = line.strip()
        lower = stripped.lower()

        if "ipv4" in lower and ":" in stripped:
            if "autoconfiguration" in lower or "link-local" in lower:
                continue
            ip = stripped.split(":", 1)[1].strip()
            if ip and ip != "0.0.0.0":
                current.ip = ip
        elif ("masque" in lower or "subnet mask" in lower) and ":" in stripped:
            current.mask = stripped.split(":", 1)[1].strip()

    if current and current.ip and current.mask:
        adapters.append(current)

    return adapters


def _should_skip_adapter(name: str, ip: str) -> bool:
    lower = name.lower()
    if any(keyword in lower for keyword in SKIP_ADAPTER_KEYWORDS):
        return True
    if ip.startswith("169.254."):
        return True
    return False


def _get_local_network() -> NetworkInfo:
    """Choisit la vraie carte réseau (Wi-Fi/Ethernet), pas Npcap/VirtualBox."""
    result = subprocess.run(
        ["ipconfig"],
        capture_output=True,
        text=True,
        encoding="cp850",
        errors="replace",
    )
    adapters = _parse_ipconfig_adapters(result.stdout)
    gateway = get_default_gateway()

    candidates = [
        a
        for a in adapters
        if a.ip and a.mask and not _should_skip_adapter(a.name, a.ip)
    ]

    if not candidates:
        raise RuntimeError(
            "Impossible de détecter le réseau local. Vérifiez votre connexion Wi-Fi/Ethernet."
        )

    if gateway:
        for adapter in candidates:
            network = ipaddress.IPv4Network(f"{adapter.ip}/{adapter.mask}", strict=False)
            try:
                if ipaddress.IPv4Address(gateway) in network:
                    return NetworkInfo(interface=adapter.name, ip=adapter.ip, network=network)
            except ValueError:
                continue

    for adapter in candidates:
        if adapter.ip.startswith(("192.168.", "10.")):
            network = ipaddress.IPv4Network(f"{adapter.ip}/{adapter.mask}", strict=False)
            return NetworkInfo(interface=adapter.name, ip=adapter.ip, network=network)

    adapter = candidates[0]
    network = ipaddress.IPv4Network(f"{adapter.ip}/{adapter.mask}", strict=False)
    return NetworkInfo(interface=adapter.name, ip=adapter.ip, network=network)


def detect_network_warning(net_info: NetworkInfo) -> str | None:
    network_str = str(net_info.network)

    if network_str == "10.0.2.0/24":
        return (
            "Réseau VirtualBox NAT détecté (10.0.2.0/24).\n\n"
            "La VM est isolée : CupNet ne voit PAS votre Wi-Fi réel.\n\n"
            "Passez l'adaptateur VirtualBox en « Accès par pont » (Bridged)."
        )

    if network_str == "192.168.56.0/24":
        return (
            "Réseau VirtualBox privé hôte détecté (192.168.56.0/24).\n\n"
            "Passez en « Accès par pont » pour voir votre Wi-Fi."
        )

    if "virtualbox" in net_info.interface.lower():
        return (
            f"Interface VirtualBox détectée ({net_info.interface}).\n\n"
            "Si vous ne voyez que 1-2 appareils, passez en « Accès par pont »."
        )

    if net_info.network.prefixlen < 24:
        return (
            f"Grand sous-réseau détecté ({network_str}).\n\n"
            "CupNet limite le scan au /24 local pour rester rapide."
        )

    return None


def _ping_host(ip: str) -> bool:
    result = subprocess.run(
        ["ping", "-n", "1", "-w", "80", ip],
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    )
    return result.returncode == 0


def _parse_arp_table() -> dict[str, str]:
    result = subprocess.run(
        ["arp", "-a"],
        capture_output=True,
        text=True,
        encoding="cp850",
        errors="replace",
    )
    entries: dict[str, str] = {}
    pattern = re.compile(
        r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-fA-F\-]{17})\s+"
    )
    for match in pattern.finditer(result.stdout):
        ip, mac = match.groups()
        if mac.replace("-", "").replace(":", "") == "ffffffffffff":
            continue
        entries[ip] = _normalize_mac(mac)
    return entries


def _scan_hosts(hosts: list[str], progress_cb: ProgressCallback | None) -> None:
    total = len(hosts)
    if total == 0:
        return

    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=80) as executor:
        futures = {executor.submit(_ping_host, ip): ip for ip in hosts}
        for future in concurrent.futures.as_completed(futures):
            done += 1
            if progress_cb and (done == total or done % 16 == 0):
                pct = 10 + int((done / total) * 55)
                progress_cb(pct, f"Ping des hôtes… {done}/{total}")


def _quick_arp_discovery(base: ipaddress.IPv4Network, gateway: str | None) -> dict[str, str]:
    """Réveille le réseau puis lit la table ARP (rapide)."""
    if gateway and gateway in [str(h) for h in base.hosts()]:
        _ping_host(gateway)
    _ping_host(str(base.broadcast_address))

    arp = _parse_arp_table()
    return {
        ip: mac
        for ip, mac in arp.items()
        if ipaddress.IPv4Address(ip) in base
    }


def scan_network(
    progress_cb: ProgressCallback | None = None,
) -> tuple[list[Device], NetworkInfo, int]:
    start = time.perf_counter()

    if progress_cb:
        progress_cb(5, "Détection du réseau…")

    net_info = _get_local_network()

    if net_info.network.prefixlen < 24:
        base = ipaddress.IPv4Network(
            f"{net_info.ip}/{24}",
            strict=False,
        )
    else:
        base = net_info.network

    hosts = [str(h) for h in base.hosts() if str(h) != net_info.ip]

    gateway = get_default_gateway()

    if progress_cb:
        progress_cb(10, f"Scan rapide de {base}…")

    arp_found = _quick_arp_discovery(base, gateway)

    if progress_cb:
        progress_cb(40, f"ARP : {len(arp_found)} appareil(s), complément…")

    if len(arp_found) < 3:
        _scan_hosts(hosts, progress_cb)
        arp_found = _quick_arp_discovery(base, gateway)

    if progress_cb:
        progress_cb(75, "Lecture de la table ARP…")

    devices: list[Device] = []
    arp_entries = sorted(arp_found.items(), key=lambda x: ipaddress.IPv4Address(x[0]))

    if progress_cb:
        progress_cb(85, f"Identification de {len(arp_entries)} appareil(s)…")

    for ip, mac in arp_entries:
        devices.append(
            Device(
                ip=ip,
                mac=mac,
                hostname=_resolve_hostname(ip),
                vendor=_lookup_vendor(mac),
                status="online",
            )
        )

    if progress_cb:
        progress_cb(100, f"{len(devices)} appareil(s) trouvé(s)")

    duration_ms = int((time.perf_counter() - start) * 1000)
    return devices, net_info, duration_ms
