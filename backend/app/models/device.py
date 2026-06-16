from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class BlockMethod(str, Enum):
    FIREWALL = "firewall"
    ARP_SPOOF = "arp_spoof"
    PING_FLOOD = "ping_flood"


class Device(BaseModel):
    ip: str
    mac: str
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    status: str = "online"
    blocked: bool = False
    block_method: Optional[BlockMethod] = None
    first_seen_at: Optional[float] = None
    last_seen_at: Optional[float] = None
    online_duration_sec: Optional[int] = None
    ping_ms: Optional[int] = None
    blocked_at: Optional[float] = None
    block_duration_sec: Optional[int] = None


class BlockRequest(BaseModel):
    method: BlockMethod = Field(description="Méthode de coupure à appliquer")


class ScanResult(BaseModel):
    devices: list[Device]
    network: str
    interface: str
    scan_duration_ms: int
    warning: Optional[str] = None
