import subprocess

from app.blockers.base import BaseBlocker
from app.models.device import BlockMethod

RULE_PREFIX = "CupNet-Block"


class FirewallBlocker(BaseBlocker):
    """
    Bloque le trafic vers/depuis une IP via le pare-feu Windows (netsh).
    Méthode la plus sûre et réversible pour un usage local.
    """

    method = BlockMethod.FIREWALL
    label = "Pare-feu local (PC)"
    description = (
        "Bloque uniquement le trafic entre CE PC et l'IP cible via netsh. "
        "Ne coupe PAS l'Internet de l'appareil sur le réseau — préférez "
        "« Coupure réseau (ARP) » pour une vraie coupure."
    )
    requires_admin = True

    def _rule_name(self, ip: str, direction: str) -> str:
        return f"{RULE_PREFIX}-{ip}-{direction}"

    def block(self, ip: str, mac: str) -> None:
        for direction in ("in", "out"):
            name = self._rule_name(ip, direction)
            subprocess.run(
                [
                    "netsh", "advfirewall", "firewall", "add", "rule",
                    f"name={name}",
                    f"dir={direction}",
                    "action=block",
                    f"remoteip={ip}",
                    "enable=yes",
                ],
                capture_output=True,
                text=True,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )

    def unblock(self, ip: str, mac: str) -> None:
        for direction in ("in", "out"):
            name = self._rule_name(ip, direction)
            subprocess.run(
                [
                    "netsh", "advfirewall", "firewall", "delete", "rule",
                    f"name={name}",
                ],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )

    def is_active(self, ip: str, mac: str) -> bool:
        name = self._rule_name(ip, "in")
        result = subprocess.run(
            [
                "netsh", "advfirewall", "firewall", "show", "rule",
                f"name={name}",
            ],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        return "Aucune règle" not in result.stdout and "No rules" not in result.stdout
