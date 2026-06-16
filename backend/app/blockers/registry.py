from app.blockers.arp_spoof import ArpSpoofBlocker
from app.blockers.base import BaseBlocker
from app.blockers.firewall import FirewallBlocker
from app.blockers.ping_flood import PingFloodBlocker
from app.models.device import BlockMethod

BLOCKERS: dict[BlockMethod, BaseBlocker] = {
    BlockMethod.FIREWALL: FirewallBlocker(),
    BlockMethod.ARP_SPOOF: ArpSpoofBlocker(),
    BlockMethod.PING_FLOOD: PingFloodBlocker(),
}


def get_blocker(method: BlockMethod) -> BaseBlocker:
    return BLOCKERS[method]


def list_blockers() -> list[dict]:
    return [b.to_dict() for b in BLOCKERS.values()]
