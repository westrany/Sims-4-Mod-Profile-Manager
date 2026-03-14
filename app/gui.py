"""
Main GUI — Sims 4 Mod Profile Manager
Aesthetic: plum/rose soft luxury with clean geometric forms.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import threading

from app.manager import ModManager, Profile, ProfileConfig
from app.widgets import (
    Sidebar, ModLibraryPanel, ProfilePanel,
    DuplicatesPanel, SettingsPanel, ConfigsPanel,
    StatusBar, StyledButton, COLORS, FONTS,
)


class ModManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.manager = ModManager()
        self.title("Sims 4 Mod Manager")
        self.geometry("1200x760")
        self.minsize(900, 620)
        self._restore_or_maximize()
        self.bind("<Configure>", self._save_geometry)
        self.resizable(True, True)
        # Prevent window from snapping to minsize after dialogs
        self.bind("<FocusIn>", lambda e: self._restore_geometry())
        self.configure(bg=COLORS["bg"])

        self._apply_theme()
        self._build_ui()
        self._refresh_all()

    def _apply_theme(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=COLORS["bg"], foreground=COLORS["fg"],
                         font=FONTS["body"], borderwidth=0)
        style.configure("Treeview", background=COLORS["surface"],
                         foreground=COLORS["fg"], fieldbackground=COLORS["surface"],
                         rowheight=28, font=FONTS["body"])
        style.configure("Treeview.Heading", background=COLORS["surface2"],
                         foreground=COLORS["accent"], font=FONTS["heading"],
                         relief="flat")
        style.map("Treeview", background=[("selected", COLORS["accent"])],
                  foreground=[("selected", "#fff")])
        style.configure("Vertical.TScrollbar", background=COLORS["surface2"],
                         troughcolor=COLORS["bg"], arrowcolor=COLORS["accent"],
                         borderwidth=0)
        style.configure("TEntry", fieldbackground=COLORS["surface2"],
                         foreground=COLORS["fg"], insertcolor=COLORS["fg"],
                         borderwidth=0, relief="flat")
        style.configure("TCombobox", fieldbackground=COLORS["surface2"],
                         foreground=COLORS["fg"], selectbackground=COLORS["accent"])
        style.map("TCombobox", fieldbackground=[("readonly", COLORS["surface2"])])

    def _build_ui(self):
        # Top bar
        topbar = tk.Frame(self, bg=COLORS["surface"], height=56)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        logo = tk.Label(topbar, text="✦  Sims 4 Mod Manager",
                        bg=COLORS["surface"], fg=COLORS["accent"],
                        font=FONTS["logo"], padx=20)
        logo.pack(side="left", pady=12)

        self.active_label = tk.Label(topbar, text="No profile active",
                                     bg=COLORS["surface"], fg=COLORS["muted"],
                                     font=FONTS["small"])
        self.active_label.pack(side="right", padx=20)

        # Main area
        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = Sidebar(main, self._on_nav, bg=COLORS["surface"])
        self.sidebar.pack(side="left", fill="y")

        # Content area
        self.content = tk.Frame(main, bg=COLORS["bg"])
        self.content.pack(side="left", fill="both", expand=True)

        # Panels (stacked, shown/hidden)
        self.panels: dict[str, tk.Frame] = {}

        self.panels["library"] = ModLibraryPanel(self.content, self.manager, self)
        self.panels["profiles"] = ProfilePanel(self.content, self.manager, self)
        self.panels["duplicates"] = DuplicatesPanel(self.content, self.manager, self)
        self.panels["configs"] = ConfigsPanel(self.content, self.manager, self)
        self.panels["settings"] = SettingsPanel(self.content, self.manager, self)

        for panel in self.panels.values():
            panel.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.status = StatusBar(self, bg=COLORS["surface"])
        self.status.pack(fill="x", side="bottom")

        self._on_nav("profiles")

    def _on_nav(self, key: str):
        for k, panel in self.panels.items():
            if k == key:
                panel.lift()
            else:
                panel.lower()
        self.sidebar.set_active(key)

    def _refresh_all(self):
        for panel in self.panels.values():
            if hasattr(panel, "refresh"):
                panel.refresh()
        active = self.manager.settings.active_profile
        if active:
            self.active_label.config(text=f"▶  Active: {active}", fg=COLORS["accent"])
        else:
            self.active_label.config(text="No profile active", fg=COLORS["muted"])
    
    def _restore_or_maximize(self):
        """On first launch: maximize. After that: restore saved size/position."""
        prefs_file = self.manager.data_dir / "window.json"
        if prefs_file.exists():
            try:
                import json
                prefs = json.loads(prefs_file.read_text())
                if prefs.get("maximized"):
                    self.state("zoomed")
                else:
                    self.geometry(prefs["geometry"])
                return
            except Exception:
                pass
        # First launch — maximize
        self.state("zoomed")

    def _save_geometry(self, e=None):
        """Save window size/position whenever it changes."""
        import json
        # Only save if the event is for the root window itself
        if e and e.widget is not self:
            return
        try:
            prefs_file = self.manager.data_dir / "window.json"
            maximized = self.state() == "zoomed"
            prefs = {
                "maximized": maximized,
                "geometry": self.geometry() if not maximized else "1200x760",
            }
            prefs_file.write_text(json.dumps(prefs))
        except Exception:
            pass

    def set_status(self, msg: str, color: str = None):
        self.status.set(msg, color or COLORS["fg"])

    def refresh(self):
        self._refresh_all()
    
    def _restore_geometry(self):
        # If window shrank below intended size, restore it
        if self.winfo_width() < 900 or self.winfo_height() < 620:
            self.geometry("1200x760")
