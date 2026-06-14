from dataclasses import dataclass


@dataclass
class AppSettings:
    hide_ip: bool = False
    splash_seconds: float = 2.0
    expand_table: bool = False

    def toggle_hide_ip(self) -> None:
        self.hide_ip = not self.hide_ip

    def toggle_expand_table(self) -> None:
        self.expand_table = not self.expand_table
