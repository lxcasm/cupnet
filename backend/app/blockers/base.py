from abc import ABC, abstractmethod

from app.models.device import BlockMethod


class BaseBlocker(ABC):
    method: BlockMethod
    label: str
    description: str
    requires_admin: bool = True

    @abstractmethod
    def block(self, ip: str, mac: str) -> None:
        pass

    @abstractmethod
    def unblock(self, ip: str, mac: str) -> None:
        pass

    @abstractmethod
    def is_active(self, ip: str, mac: str) -> bool:
        pass

    def to_dict(self) -> dict:
        return {
            "id": self.method.value,
            "label": self.label,
            "description": self.description,
            "requires_admin": self.requires_admin,
        }
