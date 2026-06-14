import threading
import tkinter.ttk as ttk
from tkinter import messagebox

import customtkinter as ctk

from app.core.device_manager import DeviceManager
from app.core.network_utils import format_duration
from app.gui.theme import GIRO
from app.models.device import BlockMethod, Device

APP_VERSION = "2.0"
CREATOR = "lxcasm"

METHOD_LABELS = {
    BlockMethod.ARP_SPOOF: "Coupure réseau (ARP)",
    BlockMethod.FIREWALL: "Pare-feu local (PC)",
    BlockMethod.PING_FLOOD: "Ping Flood",
}


class CupNetApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.manager = DeviceManager()
        self._scanning = False
        self._tick_job: str | None = None

        self.title(f"CupNet v{APP_VERSION} — contrôle réseau")
        self.geometry("1180x740")
        self.minsize(980, 640)
        self.configure(fg_color=GIRO["bg"])

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self._build_ui()
        self._load_methods_info()
        self._check_admin()
        self._start_tick()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # Bandeau rose
        stripe = ctk.CTkFrame(self, height=5, fg_color=GIRO["pink"], corner_radius=0)
        stripe.grid(row=0, column=0, sticky="ew")

        # Header
        header = ctk.CTkFrame(self, fg_color=GIRO["bg_header"], corner_radius=0, height=88)
        header.grid(row=1, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="w", padx=22, pady=14)

        ctk.CTkLabel(
            brand,
            text="CupNet",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=GIRO["pink"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand,
            text=f"par {CREATOR} · v{APP_VERSION} · surveillance & coupure réseau",
            font=ctk.CTkFont(size=13),
            text_color=GIRO["accent"],
        ).pack(anchor="w")

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=2, sticky="e", padx=22, pady=14)

        self.admin_label = ctk.CTkLabel(
            actions,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.admin_label.pack(side="top", anchor="e", pady=(0, 6))

        row = ctk.CTkFrame(actions, fg_color="transparent")
        row.pack(side="top", anchor="e")

        self.network_label = ctk.CTkLabel(
            row,
            text="Réseau : —",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=GIRO["text_muted"],
        )
        self.network_label.pack(side="left", padx=(0, 12))

        self.scan_btn = ctk.CTkButton(
            row,
            text="⟳  Scanner le réseau",
            width=175,
            height=38,
            fg_color=GIRO["pink"],
            hover_color=GIRO["pink_dark"],
            border_width=1,
            border_color=GIRO["pink_light"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_scan_click,
        )
        self.scan_btn.pack(side="left")

        # Stats
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.grid(row=2, column=0, sticky="ew", padx=20, pady=(12, 6))
        stats.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.stat_devices = self._stat_card(stats, "Appareils", "0", 0)
        self.stat_blocked = self._stat_card(stats, "Bloqués", "0", 1, GIRO["violet"])
        self.stat_duration = self._stat_card(stats, "Durée scan", "—", 2)
        self.stat_session = self._stat_card(stats, "Session", "0s", 3, GIRO["accent"])

        # Barre de progression scan
        progress_frame = ctk.CTkFrame(self, fg_color=GIRO["bg_card"], corner_radius=10)
        progress_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 6))
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=GIRO["pink_light"],
        )
        self.progress_label.grid(row=0, column=0, sticky="w", padx=14, pady=(10, 4))

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=10,
            fg_color=GIRO["violet_dark"],
            progress_color=GIRO["pink"],
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
        self.progress_bar.set(0)
        self.progress_frame = progress_frame
        self.progress_frame.grid_remove()

        # Table
        table_frame = ctk.CTkFrame(
            self,
            fg_color=GIRO["bg_card"],
            border_width=1,
            border_color=GIRO["violet_dark"],
        )
        table_frame.grid(row=4, column=0, sticky="nsew", padx=20, pady=(0, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            table_frame,
            text="Appareils détectés",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=GIRO["pink_light"],
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Giro.Treeview",
            background=GIRO["bg_table"],
            foreground=GIRO["text"],
            fieldbackground=GIRO["bg_table"],
            borderwidth=0,
            rowheight=30,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Giro.Treeview.Heading",
            background=GIRO["bg_header"],
            foreground=GIRO["pink"],
            font=("Segoe UI", 9, "bold"),
            relief="flat",
        )
        style.map(
            "Giro.Treeview",
            background=[("selected", GIRO["selection"])],
            foreground=[("selected", "#FFFFFF")],
        )

        columns = ("status", "ip", "mac", "hostname", "vendor", "online", "ping", "blocked", "method")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Giro.Treeview",
            selectmode="browse",
        )

        headings = {
            "status": ("Statut", 80),
            "ip": ("IP", 110),
            "mac": ("MAC", 130),
            "hostname": ("Hôte", 120),
            "vendor": ("Fabricant", 110),
            "online": ("Temps réseau", 100),
            "ping": ("Latence", 70),
            "blocked": ("Temps bloqué", 100),
            "method": ("Méthode", 120),
        }
        for col, (text, width) in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w")

        self.tree.bind("<<TreeviewSelect>>", self._on_select_device)

        scrollbar = ctk.CTkScrollbar(
            table_frame,
            command=self.tree.yview,
            button_color=GIRO["violet"],
            button_hover_color=GIRO["pink"],
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(12, 0), pady=(0, 12))
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 12), padx=(4, 12))

        self.detail_label = ctk.CTkLabel(
            table_frame,
            text="Sélectionnez un appareil pour voir les détails",
            font=ctk.CTkFont(size=11),
            text_color=GIRO["text_muted"],
            anchor="w",
            justify="left",
        )
        self.detail_label.grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 12))

        # Actions
        action_bar = ctk.CTkFrame(
            self,
            fg_color=GIRO["bg_card"],
            border_width=1,
            border_color=GIRO["violet_dark"],
        )
        action_bar.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 10))
        action_bar.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(action_bar, text="Méthode :", text_color=GIRO["text_muted"]).grid(
            row=0, column=0, padx=(14, 6), pady=14
        )

        self.method_var = ctk.StringVar(value=METHOD_LABELS[BlockMethod.ARP_SPOOF])
        self.method_menu = ctk.CTkOptionMenu(
            action_bar,
            variable=self.method_var,
            values=list(METHOD_LABELS.values()),
            width=220,
            fg_color=GIRO["violet_dark"],
            button_color=GIRO["violet"],
            button_hover_color=GIRO["pink"],
            text_color=GIRO["text"],
        )
        self.method_menu.grid(row=0, column=1, padx=(0, 14), pady=14)

        self.block_btn = ctk.CTkButton(
            action_bar,
            text="✂  Couper la connexion",
            fg_color=GIRO["danger"],
            hover_color=GIRO["danger_dark"],
            width=185,
            font=ctk.CTkFont(weight="bold"),
            command=self._on_block_click,
        )
        self.block_btn.grid(row=0, column=3, padx=6, pady=14)

        self.unblock_btn = ctk.CTkButton(
            action_bar,
            text="↩  Débloquer",
            fg_color=GIRO["success"],
            hover_color=GIRO["success_dark"],
            width=130,
            command=self._on_unblock_click,
        )
        self.unblock_btn.grid(row=0, column=4, padx=(6, 14), pady=14)

        # Footer
        methods_frame = ctk.CTkFrame(self, fg_color=GIRO["bg_card"])
        methods_frame.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 8))

        ctk.CTkLabel(
            methods_frame,
            text="Méthodes de coupure",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=GIRO["violet"],
        ).pack(anchor="w", padx=14, pady=(10, 4))

        self.methods_text = ctk.CTkTextbox(
            methods_frame,
            height=72,
            font=ctk.CTkFont(size=12),
            fg_color=GIRO["bg_table"],
            text_color=GIRO["text_muted"],
            activate_scrollbars=False,
        )
        self.methods_text.pack(fill="x", padx=14, pady=(0, 10))
        self.methods_text.configure(state="disabled")

        ctk.CTkLabel(
            self,
            text=f"⚠️ Usage éducatif — par {CREATOR} · github.com/{CREATOR}",
            font=ctk.CTkFont(size=11),
            text_color=GIRO["text_muted"],
        ).grid(row=7, column=0, pady=(0, 4))

        self.status_label = ctk.CTkLabel(
            self,
            text="Prêt — cliquez sur « Scanner le réseau »",
            font=ctk.CTkFont(size=11),
            text_color=GIRO["text_muted"],
        )
        self.status_label.grid(row=8, column=0, pady=(0, 12))

    def _stat_card(
        self, parent: ctk.CTkFrame, label: str, value: str, col: int, color: str | None = None
    ) -> ctk.CTkLabel:
        card = ctk.CTkFrame(
            parent,
            fg_color=GIRO["bg_card"],
            border_width=1,
            border_color=GIRO["pink_dark"],
            corner_radius=10,
        )
        card.grid(row=0, column=col, sticky="ew", padx=5, pady=4)

        value_lbl = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=color or GIRO["pink"],
        )
        value_lbl.pack(pady=(12, 0))

        ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=11),
            text_color=GIRO["text_muted"],
        ).pack(pady=(0, 12))

        return value_lbl

    def _check_admin(self) -> None:
        if self.manager.is_admin:
            self.admin_label.configure(text="● Admin", text_color=GIRO["success"])
        else:
            self.admin_label.configure(
                text="● Pas admin — coupez en ARP impossible",
                text_color=GIRO["pink_light"],
            )

    def _show_progress(self, visible: bool) -> None:
        if visible:
            self.progress_frame.grid()
        else:
            self.progress_frame.grid_remove()
            self.progress_bar.set(0)
            self.progress_label.configure(text="")

    def _update_progress(self, pct: int, message: str) -> None:
        self.progress_bar.set(max(0.0, min(1.0, pct / 100)))
        self.progress_label.configure(text=message)
        self._set_status(message)

    def _start_tick(self) -> None:
        self._tick()

    def _tick(self) -> None:
        self.stat_session.configure(text=format_duration(self.manager.session_duration_sec))
        if self.manager.has_blocked_devices() and not self._scanning:
            self._refresh_table(self.manager.get_devices(), keep_selection=True)
        self._tick_job = self.after(1000, self._tick)

    def _load_methods_info(self) -> None:
        lines = []
        for method in self.manager.get_methods():
            admin = " [Admin]" if method["requires_admin"] else ""
            lines.append(f"• {method['label']}{admin} — {method['description']}")

        self.methods_text.configure(state="normal")
        self.methods_text.delete("1.0", "end")
        self.methods_text.insert("1.0", "\n".join(lines))
        self.methods_text.configure(state="disabled")

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.scan_btn.configure(state=state)
        self.block_btn.configure(state=state)
        self.unblock_btn.configure(state=state)

    def _method_from_label(self, label: str) -> BlockMethod:
        for method, name in METHOD_LABELS.items():
            if name == label:
                return method
        return BlockMethod.ARP_SPOOF

    def _get_selected_mac(self) -> str | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return selection[0]

    def _device_to_row(self, device: Device) -> tuple:
        status = "🔴 Bloqué" if device.blocked else "🟢 En ligne"
        online = (
            format_duration(device.online_duration_sec)
            if device.online_duration_sec
            else "—"
        )
        ping = f"{device.ping_ms} ms" if device.ping_ms is not None else "—"
        blocked_time = (
            format_duration(device.block_duration_sec)
            if device.blocked and device.block_duration_sec is not None
            else "—"
        )
        method = METHOD_LABELS.get(device.block_method, "—") if device.blocked else "—"
        return (
            status,
            device.ip,
            device.mac,
            device.hostname or "—",
            device.vendor or "—",
            online,
            ping,
            blocked_time,
            method,
        )

    def _refresh_table(self, devices: list[Device], keep_selection: bool = False) -> None:
        selected = self._get_selected_mac() if keep_selection else None

        for item in self.tree.get_children():
            self.tree.delete(item)

        for device in devices:
            self.tree.insert("", "end", iid=device.mac, values=self._device_to_row(device))

        if selected and selected in [d.mac for d in devices]:
            self.tree.selection_set(selected)

        blocked = sum(1 for d in devices if d.blocked)
        self.stat_devices.configure(text=str(len(devices)))
        self.stat_blocked.configure(text=str(blocked))

    def _on_select_device(self, _event=None) -> None:
        mac = self._get_selected_mac()
        if mac:
            self.detail_label.configure(text=self.manager.get_device_summary(mac))

    def _on_scan_click(self) -> None:
        if self._scanning:
            return

        self._scanning = True
        self._set_busy(True)
        self._show_progress(True)
        self._update_progress(0, "Scan du réseau en cours…")

        def progress(pct: int, message: str) -> None:
            self.after(0, lambda: self._update_progress(pct, message))

        def run() -> None:
            try:
                result = self.manager.scan(progress_cb=progress)
                self.after(0, lambda: self._on_scan_done(result.devices, result.warning, None))
            except Exception as exc:
                self.after(0, lambda: self._on_scan_done([], None, str(exc)))

        threading.Thread(target=run, daemon=True).start()

    def _on_scan_done(
        self, devices: list[Device], warning: str | None, error: str | None
    ) -> None:
        self._scanning = False
        self._set_busy(False)
        self._show_progress(False)

        if error:
            self._set_status(f"Erreur : {error}")
            messagebox.showerror("Scan échoué", error)
            return

        self._refresh_table(devices)
        duration = self.manager.last_duration_ms / 1000
        self.stat_duration.configure(text=f"{duration:.1f}s")
        self.network_label.configure(
            text=f"Réseau : {self.manager.last_network} ({self.manager.last_interface})"
        )
        self._set_status(f"{len(devices)} appareil(s) détecté(s) en {duration:.1f}s")

        if warning:
            messagebox.showwarning("Attention réseau", warning)

    def _on_block_click(self) -> None:
        mac = self._get_selected_mac()
        if not mac:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un appareil dans la liste.")
            return

        device = next((d for d in self.manager.get_devices() if d.mac == mac), None)
        if device and device.blocked:
            messagebox.showinfo("Déjà bloqué", f"{device.ip} est déjà bloqué.")
            return

        method = self._method_from_label(self.method_var.get())
        ip = device.ip if device else mac

        if not messagebox.askyesno(
            "Confirmer la coupure",
            f"Couper la connexion de {ip} via « {METHOD_LABELS[method]} » ?",
        ):
            return

        self._set_busy(True)
        self._set_status(f"Coupure de {ip}…")

        def run() -> None:
            try:
                _updated, msg = self.manager.block(mac, method)
                self.after(0, lambda: self._on_action_done(msg, None))
            except Exception as exc:
                self.after(0, lambda: self._on_action_done("", str(exc)))

        threading.Thread(target=run, daemon=True).start()

    def _on_unblock_click(self) -> None:
        mac = self._get_selected_mac()
        if not mac:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un appareil dans la liste.")
            return

        self._set_busy(True)
        self._set_status("Déblocage en cours…")

        def run() -> None:
            try:
                _updated, msg = self.manager.unblock(mac)
                self.after(0, lambda: self._on_action_done(msg, None))
            except Exception as exc:
                self.after(0, lambda: self._on_action_done("", str(exc)))

        threading.Thread(target=run, daemon=True).start()

    def _on_action_done(self, message: str, error: str | None) -> None:
        self._set_busy(False)

        if error:
            self._set_status(f"Erreur : {error}")
            messagebox.showerror("Échec", error)
            return

        self._refresh_table(self.manager.get_devices())
        mac = self._get_selected_mac()
        if mac:
            self.detail_label.configure(text=self.manager.get_device_summary(mac))
        self._set_status(message)
        messagebox.showinfo("Succès", message)

    def destroy(self) -> None:
        if self._tick_job:
            self.after_cancel(self._tick_job)
        super().destroy()


def run_app() -> None:
    app = CupNetApp()
    app.mainloop()
