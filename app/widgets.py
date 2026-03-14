"""
Widgets and panels for Sims 4 Mod Manager.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path
import threading
from app.manager import ModManager, Profile, ProfileConfig

# ── Design tokens ─────────────────────────────────────────────────────────────
 
COLORS = {
    "bg":       "#1a1520",
    "surface":  "#231c2e",
    "surface2": "#2e2440",
    "accent":   "#c084fc",
    "accent2":  "#f0abfc",
    "positive": "#86efac",
    "warning":  "#fcd34d",
    "danger":   "#f87171",
    "fg":       "#f3e8ff",
    "muted":    "#9d7fc4",
    "border":   "#3d2f57",
}
 
FONTS = {
    "logo":    ("Georgia", 16, "bold"),
    "heading": ("Georgia", 12, "bold"),
    "body":    ("Helvetica", 11),
    "small":   ("Helvetica", 10),
    "mono":    ("Courier", 10),
}
 
NAV_ITEMS = [
    ("profiles",   "⊞  Profiles"),
    ("library",    "⊟  Mod Library"),
    ("duplicates", "⊜  Duplicates"),
    ("configs",    "⚙  Mod Configs"),
    ("settings",   "◈  Settings"),
]
 
 
# ── Reusable components ──────────────────────────────────────────────────────
 
class StyledButton(tk.Button):
    def __init__(self, parent, text, command=None, style="primary", **kwargs):
        palette = {
            "primary":  (COLORS["accent"],  "#1a1520"),
            "success":  (COLORS["positive"], "#1a1520"),
            "danger":   (COLORS["danger"],   "#1a1520"),
            "ghost":    (COLORS["surface2"], COLORS["fg"]),
            "muted":    (COLORS["surface2"], COLORS["muted"]),
        }
        bg, fg = palette.get(style, palette["primary"])
        super().__init__(
            parent, text=text, command=command,
            bg=bg, fg=fg, activebackground=COLORS["accent2"],
            activeforeground="#1a1520", relief="flat", cursor="hand2",
            font=FONTS["body"], padx=14, pady=6, bd=0,
            **kwargs
        )
        self.bind("<Enter>", lambda e: self.config(bg=COLORS["accent2"] if style == "primary" else bg))
        self.bind("<Leave>", lambda e: self.config(bg=bg))
 
 
class StyledEntry(ttk.Entry):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="TEntry", **kwargs)
 
 
class SectionHeader(tk.Label):
    def __init__(self, parent, text, **kwargs):
        super().__init__(parent, text=text, bg=COLORS["bg"],
                         fg=COLORS["accent"], font=FONTS["heading"],
                         anchor="w", **kwargs)
 
 
class Sidebar(tk.Frame):
    def __init__(self, parent, on_nav, **kwargs):
        super().__init__(parent, width=190, **kwargs)
        self.pack_propagate(False)
        self.on_nav = on_nav
        self.buttons: dict[str, tk.Label] = {}
 
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")
 
        for key, label in NAV_ITEMS:
            btn = tk.Label(self, text=label, bg=COLORS["surface"],
                           fg=COLORS["muted"], font=FONTS["body"],
                           anchor="w", padx=20, pady=12, cursor="hand2")
            btn.pack(fill="x")
            btn.bind("<Button-1>", lambda e, k=key: self.on_nav(k))
            btn.bind("<Enter>", lambda e, b=btn: b.config(fg=COLORS["accent"]) if b.cget("fg") != "#f3e8ff" else None)
            btn.bind("<Leave>", lambda e, b=btn, k=key: b.config(fg=COLORS["fg"] if self._active == k else COLORS["muted"]))
            self.buttons[key] = btn
 
        self._active = None
 
    def set_active(self, key: str):
        self._active = key
        for k, btn in self.buttons.items():
            if k == key:
                btn.config(fg=COLORS["fg"], bg=COLORS["surface2"])
            else:
                btn.config(fg=COLORS["muted"], bg=COLORS["surface"])
 
 
class StatusBar(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=28, **kwargs)
        self.pack_propagate(False)
        self.label = tk.Label(self, text="Ready", bg=COLORS["surface"],
                              fg=COLORS["muted"], font=FONTS["small"], padx=12)
        self.label.pack(side="left", fill="y")
 
    def set(self, msg: str, color: str = None):
        self.label.config(text=msg, fg=color or COLORS["muted"])
 
 
# ── Profiles Panel ────────────────────────────────────────────────────────────
 
class ProfilePanel(tk.Frame):
    def __init__(self, parent, manager, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.manager = manager
        self.app = app
        self._build()
 
    def _build(self):
        left = tk.Frame(self, bg=COLORS["bg"], width=260)
        left.pack(side="left", fill="y", padx=(20, 0), pady=20)
        left.pack_propagate(False)
 
        SectionHeader(left, "Profiles").pack(fill="x", pady=(0, 8))
 
        # Profile list
        list_frame = tk.Frame(left, bg=COLORS["surface"], bd=0)
        list_frame.pack(fill="both", expand=True)
 
        self.profile_lb = tk.Listbox(list_frame, bg=COLORS["surface"],
                                     fg=COLORS["fg"], selectbackground=COLORS["accent"],
                                     selectforeground="#fff", font=FONTS["body"],
                                     relief="flat", bd=0, highlightthickness=0,
                                     activestyle="none")
        self.profile_lb.pack(fill="both", expand=True, padx=4, pady=4)
        self.profile_lb.bind("<<ListboxSelect>>", self._on_select)
 
        # Profile action buttons
        btn_frame = tk.Frame(left, bg=COLORS["bg"])
        btn_frame.pack(fill="x", pady=8)
        StyledButton(btn_frame, "+ New", self._new_profile, "primary").pack(side="left", padx=(0, 4))
        StyledButton(btn_frame, "Import", self._import_profile, "ghost").pack(side="left", padx=(0, 4))
        StyledButton(btn_frame, "Rename", self._rename_profile, "ghost").pack(side="left", padx=(0, 4))
        StyledButton(btn_frame, "Delete", self._delete_profile, "danger").pack(side="right")
 
        # Right side
        right = tk.Frame(self, bg=COLORS["bg"])
        right.pack(side="left", fill="both", expand=True, padx=20, pady=20)
 
        SectionHeader(right, "Profile Details").pack(fill="x", pady=(0, 8))
 
        self.detail_frame = tk.Frame(right, bg=COLORS["bg"])
        self.detail_frame.pack(fill="both", expand=True)
        self._show_empty_detail()
 
    def _show_empty_detail(self):
        for w in self.detail_frame.winfo_children():
            w.destroy()
        tk.Label(self.detail_frame, text="Select or create a profile",
                 bg=COLORS["bg"], fg=COLORS["muted"], font=FONTS["body"]).pack(pady=40)
 
    def _show_detail(self, profile_name: str):
        for w in self.detail_frame.winfo_children():
            w.destroy()
 
        p = self.manager.profiles.get(profile_name)
        if not p:
            return
 
        # Header row
        header = tk.Frame(self.detail_frame, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 12))
 
        tk.Label(header, text=p.name, bg=COLORS["bg"], fg=COLORS["fg"],
                 font=FONTS["heading"]).pack(side="left")
 
        is_active = self.manager.settings.active_profile == profile_name
        if is_active:
            tk.Label(header, text=" ▶ ACTIVE", bg=COLORS["bg"],
                     fg=COLORS["positive"], font=FONTS["small"]).pack(side="left", padx=6)
 
        # Description
        desc_frame = tk.Frame(self.detail_frame, bg=COLORS["surface2"])
        desc_frame.pack(fill="x", pady=(0, 12))
        tk.Label(desc_frame, text="Description", bg=COLORS["surface2"],
                 fg=COLORS["muted"], font=FONTS["small"], anchor="w").pack(fill="x", padx=8, pady=(6, 2))
        self._desc_var = tk.StringVar(value=p.description)
        desc_entry = ttk.Entry(desc_frame, textvariable=self._desc_var, font=FONTS["body"])
        desc_entry.pack(fill="x", padx=8, pady=(0, 6))
        self._desc_var.trace_add("write", lambda *_: self._save_desc(profile_name))
 
        # Mod count
        tk.Label(self.detail_frame,
                 text=f"{len(p.enabled_mods)} mods enabled",
                 bg=COLORS["bg"], fg=COLORS["muted"], font=FONTS["small"]).pack(anchor="w")
 
        # Mod list with remove button
        mod_frame = tk.Frame(self.detail_frame, bg=COLORS["surface"])
        mod_frame.pack(fill="both", expand=True, pady=8)
 
        cols = ("mod",)
        self.mod_tree = ttk.Treeview(mod_frame, columns=cols, show="headings",
                                     selectmode="extended")
        self.mod_tree.heading("mod", text="Enabled Mods")
        self.mod_tree.column("mod", width=400)
        scroll = ttk.Scrollbar(mod_frame, orient="vertical", command=self.mod_tree.yview)
        self.mod_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.mod_tree.pack(fill="both", expand=True)
 
        for mod in sorted(p.enabled_mods):
            in_lib = mod in self.manager.library
            tag = "ok" if in_lib else "missing"
            self.mod_tree.insert("", "end", values=(mod,), tags=(tag,))
 
        self.mod_tree.tag_configure("missing", foreground=COLORS["danger"])
 
        # Buttons
        act_frame = tk.Frame(self.detail_frame, bg=COLORS["bg"])
        act_frame.pack(fill="x", pady=8)
 
        if not is_active:
            StyledButton(act_frame, "▶  Activate Profile",
                         lambda: self._activate(profile_name), "success").pack(side="left", padx=(0, 6))
        else:
            StyledButton(act_frame, "⏹  Deactivate",
                         self._deactivate, "ghost").pack(side="left", padx=(0, 6))
 
        StyledButton(act_frame, "Export…",
                     lambda: self._export(profile_name), "ghost").pack(side="left", padx=(0, 6))
        StyledButton(act_frame, "Edit Mods…",
                     lambda: self._open_mod_editor(profile_name), "ghost").pack(side="left")
        StyledButton(act_frame, "Remove Selected",
                     lambda: self._remove_mods(profile_name), "danger").pack(side="right")
 
    def _save_desc(self, name):
        p = self.manager.profiles.get(name)
        if p:
            p.description = self._desc_var.get()
            self.manager.save_profile(p)
 
    def _on_select(self, e=None):
        sel = self.profile_lb.curselection()
        if not sel:
            return
        name = self.profile_lb.get(sel[0])
        self._show_detail(name)
 
    def _new_profile(self):
        name = simpledialog.askstring("New Profile", "Profile name:", parent=self)
        if not name:
            return
        if name in self.manager.profiles:
            messagebox.showerror("Error", f"Profile '{name}' already exists.")
            return
        p = Profile(name=name)
        self.manager.profiles[name] = p
        self.manager.save_profile(p)
        self.refresh()
        # Select the new profile
        items = list(self.profile_lb.get(0, "end"))
        if name in items:
            idx = items.index(name)
            self.profile_lb.selection_set(idx)
            self._show_detail(name)
        self.app.set_status(f"Created profile '{name}'")
        
    def _rename_profile(self):
        sel = self.profile_lb.curselection()
        if not sel:
            return
        old_name = self.profile_lb.get(sel[0])
        new_name = simpledialog.askstring("Rename Profile", "New name:", 
                                        initialvalue=old_name, parent=self)
        if not new_name or new_name == old_name:
            return
        if new_name in self.manager.profiles:
            messagebox.showerror("Error", f"A profile named '{new_name}' already exists.")
            return
        # Update the profile object
        profile = self.manager.profiles[old_name]
        profile.name = new_name
        # Remove old file, save under new name
        import re
        old_safe = re.sub(r'[^\w\-]', '_', old_name)
        old_path = self.manager.profiles_dir / f"{old_safe}.json"
        if old_path.exists():
            old_path.unlink()
        del self.manager.profiles[old_name]
        self.manager.profiles[new_name] = profile
        self.manager.save_profile(profile)
        # Update active profile name if it was the renamed one
        if self.manager.settings.active_profile == old_name:
            self.manager.settings.active_profile = new_name
            self.manager.save_settings()
        self.refresh()
        # Re-select the renamed profile
        items = list(self.profile_lb.get(0, "end"))
        if new_name in items:
            self.profile_lb.selection_set(items.index(new_name))
        self._show_detail(new_name)
        self.app.set_status(f"Renamed '{old_name}' to '{new_name}'")
 
    def _delete_profile(self):
        sel = self.profile_lb.curselection()
        if not sel:
            return
        name = self.profile_lb.get(sel[0])
        if not messagebox.askyesno("Delete Profile", f"Delete profile '{name}'?"):
            return
        if self.manager.settings.active_profile == name:
            self.manager.deactivate_current()
        self.manager.delete_profile(name)
        self.refresh()
        self._show_empty_detail()
        self.app.set_status(f"Deleted profile '{name}'")
 
    def _activate(self, name: str):
        def do():
            try:
                result = self.manager.activate_profile(name)
                msg = f"Activated '{name}': {result['linked']} mods linked."
                if result["missing"]:
                    msg += f" ({len(result['missing'])} missing from library)"
                self.after(0, lambda: self.app.set_status(msg, COLORS["positive"]))
                self.after(0, lambda: self.app.refresh())
                self.after(0, lambda: self._show_detail(name))
            except Exception as ex:
                self.after(0, lambda e=ex: messagebox.showerror("Error", str(e)))
 
        self.app.set_status("Activating profile…")
        threading.Thread(target=do, daemon=True).start()
 
    def _deactivate(self):
        self.manager.deactivate_current()
        self.app.refresh()
        sel = self.profile_lb.curselection()
        if sel:
            self._show_detail(self.profile_lb.get(sel[0]))
        self.app.set_status("Profile deactivated.")
 
    def _export(self, name: str):
        path = filedialog.asksaveasfilename(
            title="Export Profile",
            defaultextension=".json",
            filetypes=[("Profile JSON", "*.json")],
            initialfile=f"{name}_profile.json",
        )
        if path:
            self.manager.export_profile(name, Path(path))
            self.app.set_status(f"Exported profile to {path}", COLORS["positive"])
 
    def _import_profile(self):
        path = filedialog.askopenfilename(
            title="Import Profile",
            filetypes=[("Profile JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            profile, missing = self.manager.import_profile(Path(path))
            msg = f"Imported '{profile.name}'."
            if missing:
                msg += f"\n{len(missing)} mods not in your library:\n" + "\n".join(missing[:10])
                if len(missing) > 10:
                    msg += f"\n…and {len(missing)-10} more."
                messagebox.showwarning("Import complete (with missing mods)", msg)
            else:
                messagebox.showinfo("Import complete", msg)
            self.refresh()
        except Exception as ex:
            messagebox.showerror("Import failed", str(ex))
 
    def _remove_mods(self, profile_name: str):
        sel = self.mod_tree.selection()
        if not sel:
            return
        p = self.manager.profiles[profile_name]
        to_remove = [self.mod_tree.item(i)["values"][0] for i in sel]
        p.enabled_mods = [m for m in p.enabled_mods if m not in to_remove]
        self.manager.save_profile(p)
        self._show_detail(profile_name)
 
    def _open_mod_editor(self, profile_name: str):
        ModEditorDialog(self, self.manager, profile_name, self.app)
        self._show_detail(profile_name)
 
    def refresh(self):
        sel_name = None
        sel = self.profile_lb.curselection()
        if sel:
            sel_name = self.profile_lb.get(sel[0])
 
        self.profile_lb.delete(0, "end")
        for name in sorted(self.manager.profiles.keys()):
            display = name
            if name == self.manager.settings.active_profile:
                display = f"▶ {name}"
            self.profile_lb.insert("end", name)
            # Highlight active
            if name == self.manager.settings.active_profile:
                idx = self.profile_lb.size() - 1
                self.profile_lb.itemconfig(idx, fg=COLORS["positive"])
 
        if sel_name and sel_name in self.manager.profiles:
            items = list(self.profile_lb.get(0, "end"))
            if sel_name in items:
                self.profile_lb.selection_set(items.index(sel_name))
 
 
# ── Mod Editor Dialog ─────────────────────────────────────────────────────────
 
class ModEditorDialog(tk.Toplevel):
    """Dialog to add/remove mods from a profile."""
    def __init__(self, parent, manager, profile_name, app):
        super().__init__(parent)
        self.manager = manager
        self.profile_name = profile_name
        self.app = app
        self.title(f"Edit Mods — {profile_name}")
        self.geometry("900x600")
        self.configure(bg=COLORS["bg"])
        self.grab_set()
        self._build()
 
    def _build(self):
        profile = self.manager.profiles[self.profile_name]
        enabled_set = set(profile.enabled_mods)
 
        # Search bar
        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", padx=16, pady=12)
        tk.Label(top, text="Search library:", bg=COLORS["bg"],
                 fg=COLORS["muted"], font=FONTS["small"]).pack(side="left")
        self._search_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self._search_var, width=30)
        entry.pack(side="left", padx=8)
        self._search_var.trace_add("write", lambda *_: self._filter())
        StyledButton(top, "Add Selected →", self._add_selected, "primary").pack(side="right")
        StyledButton(top, "Add All Visible", self._add_all_visible, "ghost").pack(side="right", padx=6)
 
        panes = tk.Frame(self, bg=COLORS["bg"])
        panes.pack(fill="both", expand=True, padx=16, pady=(0, 12))
 
        # Library (left)
        left = tk.Frame(panes, bg=COLORS["surface"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(left, text="All Library Mods", bg=COLORS["surface"],
                 fg=COLORS["accent"], font=FONTS["heading"], anchor="w", padx=8, pady=6).pack(fill="x")
        self.lib_tree = ttk.Treeview(left, columns=("mod",), show="headings",
                                     selectmode="extended")
        self.lib_tree.heading("mod", text="Filename")
        sc = ttk.Scrollbar(left, orient="vertical", command=self.lib_tree.yview)
        self.lib_tree.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        self.lib_tree.pack(fill="both", expand=True)
        self.lib_tree.bind("<Double-1>", lambda e: self._add_selected())
 
        # Enabled (right)
        right = tk.Frame(panes, bg=COLORS["surface"])
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="Enabled in Profile", bg=COLORS["surface"],
                 fg=COLORS["accent"], font=FONTS["heading"], anchor="w", padx=8, pady=6).pack(fill="x")
        self.enabled_tree = ttk.Treeview(right, columns=("mod",), show="headings",
                                         selectmode="extended")
        self.enabled_tree.heading("mod", text="Filename")
        sc2 = ttk.Scrollbar(right, orient="vertical", command=self.enabled_tree.yview)
        self.enabled_tree.configure(yscrollcommand=sc2.set)
        sc2.pack(side="right", fill="y")
        self.enabled_tree.pack(fill="both", expand=True)
 
        StyledButton(right, "← Remove Selected",
                     self._remove_selected, "danger").pack(pady=6)
 
        self._all_mods = sorted(self.manager.library.keys())
        self._enabled_set = enabled_set
        self._populate_lib(self._all_mods)
        self._populate_enabled()
 
        # Save / close
        bot = tk.Frame(self, bg=COLORS["bg"])
        bot.pack(fill="x", padx=16, pady=8)
        StyledButton(bot, "Save & Close", self._save, "success").pack(side="right")
 
    def _populate_lib(self, mods):
        self.lib_tree.delete(*self.lib_tree.get_children())
        for m in mods:
            already = "✓ " if m in self._enabled_set else ""
            self.lib_tree.insert("", "end", iid=m, values=(f"{already}{m}",),
                                 tags=("enabled" if m in self._enabled_set else "",))
        self.lib_tree.tag_configure("enabled", foreground=COLORS["muted"])
 
    def _populate_enabled(self):
        self.enabled_tree.delete(*self.enabled_tree.get_children())
        for m in sorted(self._enabled_set):
            self.enabled_tree.insert("", "end", iid=m, values=(m,))
 
    def _filter(self):
        q = self._search_var.get().lower()
        filtered = [m for m in self._all_mods if q in m.lower()]
        self._populate_lib(filtered)
 
    def _add_selected(self):
        sel = self.lib_tree.selection()
        for iid in sel:
            self._enabled_set.add(iid)
        self._populate_enabled()
        self._filter()
 
    def _add_all_visible(self):
        for iid in self.lib_tree.get_children():
            self._enabled_set.add(iid)
        self._populate_enabled()
        self._filter()
 
    def _remove_selected(self):
        sel = self.enabled_tree.selection()
        for iid in sel:
            self._enabled_set.discard(iid)
        self._populate_enabled()
        self._filter()
 
    def _save(self):
        p = self.manager.profiles[self.profile_name]
        p.enabled_mods = sorted(self._enabled_set)
        self.manager.save_profile(p)
        self.app.set_status(f"Saved profile '{self.profile_name}': {len(p.enabled_mods)} mods enabled.")
        self.destroy()
 
 
# ── Mod Library Panel ─────────────────────────────────────────────────────────
 
class ModLibraryPanel(tk.Frame):
    def __init__(self, parent, manager, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.manager = manager
        self.app = app
        self._build()
 
    def _build(self):
        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", padx=20, pady=(16, 8))
        SectionHeader(top, "Mod Library").pack(side="left")
 
        btn_row = tk.Frame(top, bg=COLORS["bg"])
        btn_row.pack(side="right")
        StyledButton(btn_row, "↻ Scan Library", self._scan, "primary").pack(side="left", padx=4)
        StyledButton(btn_row, "+ Import Folder", self._import_folder, "ghost").pack(side="left", padx=4)
 
        # Search
        search_row = tk.Frame(self, bg=COLORS["bg"])
        search_row.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(search_row, text="🔍", bg=COLORS["bg"], fg=COLORS["muted"]).pack(side="left")
        self._search_var = tk.StringVar()
        ttk.Entry(search_row, textvariable=self._search_var, width=40).pack(side="left", padx=6)
        self._search_var.trace_add("write", lambda *_: self._filter())
 
        # Tree
        tree_frame = tk.Frame(self, bg=COLORS["surface"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))
 
        cols = ("filename", "size", "tags")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="extended")
        self.tree.heading("filename", text="Filename")
        self.tree.heading("size", text="Size")
        self.tree.heading("tags", text="Tags")
        self.tree.column("filename", width=500)
        self.tree.column("size", width=90, anchor="e")
        self.tree.column("tags", width=180)
 
        sc = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
 
        self._stats_label = tk.Label(self, text="", bg=COLORS["bg"],
                                     fg=COLORS["muted"], font=FONTS["small"])
        self._stats_label.pack(anchor="w", padx=20, pady=(0, 8))
 
    def _scan(self):
        def do():
            self.app.set_status("Scanning library…")
            stats = self.manager.scan_master_library()
            msg = (f"Scan complete: {stats['total']} mods total, "
                   f"{stats['new']} new, {stats['removed']} removed, "
                   f"{len(stats['duplicates'])} duplicate pairs found.")
            self.after(0, lambda: self.app.set_status(msg, COLORS["positive"]))
            self.after(0, self.refresh)
            # Auto-populate duplicates panel if any were found
            if stats['duplicates']:
                groups = self.manager.find_duplicates()
                self.after(0, lambda: self.app.panels["duplicates"]._populate(groups))
        threading.Thread(target=do, daemon=True).start()
 
    def _import_folder(self):
        folder = filedialog.askdirectory(title="Select folder of mods to import")
        if not folder:
            return
        count = self.manager.add_mods_from_folder(Path(folder))
        self.app.set_status(f"Imported {count} new mods. Run Scan to update library.")
 
    def _filter(self):
        q = self._search_var.get().lower()
        self._populate(q)
 
    def _populate(self, query=""):
        self.tree.delete(*self.tree.get_children())
        for rel, entry in sorted(self.manager.library.items()):
            if query and query not in rel.lower():
                continue
            size = self._fmt_size(entry.size_bytes)
            tags = ", ".join(entry.tags) if entry.tags else ""
            self.tree.insert("", "end", values=(rel, size, tags))
        count = len(self.tree.get_children())
        self._stats_label.config(text=f"{count} mods shown  ·  {len(self.manager.library)} total in library")
 
    def _fmt_size(self, b: int) -> str:
        if b < 1024:
            return f"{b} B"
        elif b < 1024**2:
            return f"{b/1024:.1f} KB"
        else:
            return f"{b/1024**2:.1f} MB"
 
    def refresh(self):
        self._populate()
 
 
# ── Duplicates Panel ──────────────────────────────────────────────────────────
 
class DuplicatesPanel(tk.Frame):
    def __init__(self, parent, manager, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.manager = manager
        self.app = app
        self._build()
 
    def _build(self):
        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", padx=20, pady=(16, 8))
        SectionHeader(top, "Duplicate Mods").pack(side="left")
        StyledButton(top, "↻ Check Duplicates", self._check, "primary").pack(side="right")
 
        info = tk.Label(self, text="Duplicate detection compares file contents by hash — not just filenames.",
                        bg=COLORS["bg"], fg=COLORS["muted"], font=FONTS["small"])
        info.pack(anchor="w", padx=20, pady=(0, 8))
        
        # Pack buttons and label BEFORE tree so they're never pushed off screen
        btn_row = tk.Frame(self, bg=COLORS["bg"])
        btn_row.pack(fill="x", padx=20, pady=(0, 4), side="bottom")
        StyledButton(btn_row, "\U0001f5d1  Send Selected to Recycle Bin", lambda: self._recycle_selected(), "danger").pack(side="left")
        StyledButton(btn_row, "\U0001f5d1  Send All Duplicates to Recycle Bin", lambda: self._recycle_all_dupes(), "danger").pack(side="left", padx=8)
        
        self._result_label = tk.Label(self, text="Run a check to find duplicate mods.",
                                      bg=COLORS["bg"], fg=COLORS["muted"], font=FONTS["small"])
        self._result_label.pack(anchor="w", padx=20, pady=(0, 4), side="bottom")
 
        tree_frame = tk.Frame(self, bg=COLORS["surface"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 4))

        self.tree = ttk.Treeview(tree_frame, columns=("path", "note"),
                                 show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Group")
        self.tree.heading("path", text="File Path")
        self.tree.heading("note", text="")
        self.tree.column("#0", width=80)
        self.tree.column("path", width=520)
        self.tree.column("note", width=120)

        sc = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

    def _send_to_recycle(self, path):
        import platform
        system = platform.system()
        if system == "Windows":
            import ctypes
            from ctypes import wintypes
            class SHFILEOPSTRUCT(ctypes.Structure):
                _fields_ = [
                    ("hwnd",                  wintypes.HWND),
                    ("wFunc",                 wintypes.UINT),
                    ("pFrom",                 wintypes.LPCWSTR),
                    ("pTo",                   wintypes.LPCWSTR),
                    ("fFlags",                wintypes.WORD),
                    ("fAnyOperationsAborted", wintypes.BOOL),
                    ("hNameMappings",         ctypes.c_void_p),
                    ("lpszProgressTitle",     wintypes.LPCWSTR),
                ]
            FO_DELETE = 3
            FOF_ALLOWUNDO = 0x0040
            FOF_NOCONFIRMATION = 0x0010
            FOF_SILENT = 0x0004
            op = SHFILEOPSTRUCT()
            op.wFunc = FO_DELETE
            op.pFrom = str(path) + "\0\0"
            op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT
            ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
        elif system == "Darwin":
            import subprocess
            subprocess.run(["osascript", "-e",
                            f'tell application "Finder" to delete POSIX file "{path}"'])
        else:
            import shutil
            trash = Path.home() / ".local/share/Trash/files"
            trash.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), trash / Path(path).name)
 
        def _recycle_selected(self):
            sel = self.tree.selection()
            if not sel:
                messagebox.showinfo("Nothing selected", "Click a duplicate file row to select it first.")
                return
            iid = sel[0]
            if not self.tree.parent(iid):
                messagebox.showinfo("Select a file", "Select an individual file row, not a group header.")
                return
            path_str = self.tree.item(iid)["values"][0]
            note = str(self.tree.item(iid)["values"][1])
            if "keep" in note:
                if not messagebox.askyesno("Delete original?",
                        f"'{path_str}' is marked as the original to keep.\nSend it to the Recycle Bin anyway?"):
                    return
            else:
                if not messagebox.askyesno("Send to Recycle Bin?", f"Send to Recycle Bin?\n\n{path_str}"):
                    return
            full_path = Path(self.manager.settings.master_mods_dir) / path_str
            try:
                self._send_to_recycle(full_path)
                self.tree.delete(iid)
                if path_str in self.manager.library:
                    del self.manager.library[path_str]
                    self.manager.save_library()
                self.app.set_status(f"Sent to Recycle Bin: {path_str}", COLORS["positive"])
            except Exception as ex:
                messagebox.showerror("Error", f"Could not recycle file:\n{ex}")
                
        def _recycle_all_dupes(self):
            to_delete = []
            for group_iid in self.tree.get_children():
                for iid in self.tree.get_children(group_iid):
                    note = str(self.tree.item(iid)["values"][1])
                    if "duplicate" in note:
                        to_delete.append((iid, self.tree.item(iid)["values"][0]))
            if not to_delete:
                messagebox.showinfo("Nothing to delete", "No duplicates found to remove.")
                return
            preview = "\n".join(p for _, p in to_delete[:10])
            if len(to_delete) > 10:
                preview += f"\n\u2026and {len(to_delete) - 10} more"
            if not messagebox.askyesno("Send all duplicates to Recycle Bin?",
                    f"Send {len(to_delete)} duplicate file(s) to the Recycle Bin?\n\n{preview}"):
                return
            failed = []
            for iid, path_str in to_delete:
                full_path = Path(self.manager.settings.master_mods_dir) / path_str
                try:
                    self._send_to_recycle(full_path)
                    self.tree.delete(iid)
                    if path_str in self.manager.library:
                        del self.manager.library[path_str]
                except Exception as ex:
                    failed.append(f"{path_str}: {ex}")
                self.manager.save_library()
                if failed:
                    messagebox.showwarning("Some files failed", "\n".join(failed))
                else:
                    self.app.set_status(f"Sent {len(to_delete)} duplicate(s) to Recycle Bin.", COLORS["positive"])
                self._result_label.config(
                    text=f"Removed {len(to_delete)} duplicate(s). Re-scan to verify.",
                    fg=COLORS["positive"])
    
 
    def _check(self):
        def do():
            self.after(0, lambda: self.app.set_status("Checking for duplicates\u2026"))
            groups = self.manager.find_duplicates()
            self.after(0, lambda: self._populate(groups))
        # Re-scan hashes first
        self.manager.scan_master_library()
        threading.Thread(target=do, daemon=True).start()
 
    def _populate(self, groups):
        self.tree.delete(*self.tree.get_children())
        for i, group in enumerate(groups, 1):
            parent = self.tree.insert("", "end", text=f"#{i}", values=("", ""))
            for j, path in enumerate(group):
                note = "keep (original)" if j == 0 else "\u26a0 duplicate"
                self.tree.insert(parent, "end", values=(path, note))
            self.tree.item(parent, open=True)
 
        if groups:
            self._result_label.config(
                text=f"Found {len(groups)} duplicate group(s). Select a file and use the buttons below.",
                fg=COLORS["warning"])
            self.app.set_status(f"{len(groups)} duplicate groups found.", COLORS["warning"])
        else:
            self._result_label.config(text="\u2713 No duplicates found!", fg=COLORS["positive"])
            self.app.set_status("No duplicates found.", COLORS["positive"])
 
    def refresh(self):
        pass
 
 
# ── Mod Configs Panel ─────────────────────────────────────────────────────────
 
class ConfigsPanel(tk.Frame):
    """Manage per-profile config files (MCCC settings etc.)."""
    def __init__(self, parent, manager, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.manager = manager
        self.app = app
        self._build()
 
    def _build(self):
        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", padx=20, pady=(16, 8))
        SectionHeader(top, "Mod Config Files").pack(side="left")
 
        info = tk.Label(self,
            text="Manage per-profile config files (e.g. MCCC_settings.cfg). "
                 "Each profile can have its own copy, or borrow one from another profile.",
            bg=COLORS["bg"], fg=COLORS["muted"], font=FONTS["small"], wraplength=700, justify="left")
        info.pack(anchor="w", padx=20, pady=(0, 10))
 
        # Profile selector
        sel_row = tk.Frame(self, bg=COLORS["bg"])
        sel_row.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(sel_row, text="Profile:", bg=COLORS["bg"],
                 fg=COLORS["muted"], font=FONTS["body"]).pack(side="left")
        self._profile_var = tk.StringVar()
        self._profile_combo = ttk.Combobox(sel_row, textvariable=self._profile_var,
                                           state="readonly", width=24)
        self._profile_combo.pack(side="left", padx=8)
        self._profile_combo.bind("<<ComboboxSelected>>", lambda e: self._load_profile_configs())
 
        StyledButton(sel_row, "Upload Config File", self._upload_config, "ghost").pack(side="right")
 
        # Config list
        tree_frame = tk.Frame(self, bg=COLORS["surface"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 8))
 
        self.tree = ttk.Treeview(tree_frame, columns=("filename", "source"),
                                 show="headings", selectmode="browse")
        self.tree.heading("filename", text="Config Filename")
        self.tree.heading("source", text="Source (own / borrowed from)")
        self.tree.column("filename", width=280)
        self.tree.column("source", width=320)
        sc = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
 
        btn_row = tk.Frame(self, bg=COLORS["bg"])
        btn_row.pack(fill="x", padx=20, pady=8)
        StyledButton(btn_row, "Set Borrow Source…", self._set_borrow, "ghost").pack(side="left", padx=(0, 6))
        StyledButton(btn_row, "Use Own Copy", self._use_own, "ghost").pack(side="left", padx=(0, 6))
        StyledButton(btn_row, "Remove Config Entry", self._remove_config, "danger").pack(side="right")
 
    def _load_profile_configs(self):
        self.tree.delete(*self.tree.get_children())
        name = self._profile_var.get()
        if not name or name not in self.manager.profiles:
            return
        p = self.manager.profiles[name]
        for cfg in p.config_files:
            src = cfg.source_profile if cfg.source_profile else "own copy"
            self.tree.insert("", "end", iid=cfg.config_filename,
                             values=(cfg.config_filename, src))
        # Also show stored config files not yet in profile
        stored = self.manager.list_config_files(name)
        for fname in stored:
            if not self.tree.exists(fname):
                self.tree.insert("", "end", iid=fname, values=(fname, "stored (not linked to profile)"),
                                 tags=("unlinked",))
        self.tree.tag_configure("unlinked", foreground=COLORS["muted"])
 
    def _upload_config(self):
        name = self._profile_var.get()
        if not name:
            messagebox.showwarning("No Profile", "Select a profile first.")
            return
        path = filedialog.askopenfilename(title="Select config file",
                                          filetypes=[("Config files", "*.cfg *.ini *.xml *.json"), ("All", "*.*")])
        if not path:
            return
        src = Path(path)
        with open(src, "rb") as f:
            content = f.read()
        self.manager.save_config_file(name, src.name, content)
        # Add to profile config list if not already
        p = self.manager.profiles[name]
        existing = {c.config_filename for c in p.config_files}
        if src.name not in existing:
            p.config_files.append(ProfileConfig(config_filename=src.name))
            self.manager.save_profile(p)
        self._load_profile_configs()
        self.app.set_status(f"Saved config '{src.name}' for profile '{name}'", COLORS["positive"])
 
    def _set_borrow(self):
        name = self._profile_var.get()
        sel = self.tree.selection()
        if not sel:
            return
        filename = sel[0]
        other_profiles = [n for n in self.manager.profiles if n != name]
        if not other_profiles:
            messagebox.showinfo("No Other Profiles", "You need at least two profiles to borrow configs.")
            return
        dlg = BorrowDialog(self, other_profiles)
        self.wait_window(dlg)
        if dlg.result:
            p = self.manager.profiles[name]
            for cfg in p.config_files:
                if cfg.config_filename == filename:
                    cfg.source_profile = dlg.result
                    break
            else:
                p.config_files.append(ProfileConfig(config_filename=filename, source_profile=dlg.result))
            self.manager.save_profile(p)
            self._load_profile_configs()
            self.app.set_status(f"'{filename}' will borrow config from '{dlg.result}'")
 
    def _use_own(self):
        name = self._profile_var.get()
        sel = self.tree.selection()
        if not sel:
            return
        filename = sel[0]
        p = self.manager.profiles[name]
        for cfg in p.config_files:
            if cfg.config_filename == filename:
                cfg.source_profile = None
                break
        self.manager.save_profile(p)
        self._load_profile_configs()
        self.app.set_status(f"'{filename}' set to use own copy.")
 
    def _remove_config(self):
        name = self._profile_var.get()
        sel = self.tree.selection()
        if not sel:
            return
        filename = sel[0]
        p = self.manager.profiles[name]
        p.config_files = [c for c in p.config_files if c.config_filename != filename]
        self.manager.save_profile(p)
        self._load_profile_configs()
 
    def refresh(self):
        profiles = sorted(self.manager.profiles.keys())
        self._profile_combo["values"] = profiles
        current = self._profile_var.get()
        if current not in profiles and profiles:
            self._profile_var.set(profiles[0])
        self._load_profile_configs()
 
 
class BorrowDialog(tk.Toplevel):
    def __init__(self, parent, profiles: list[str]):
        super().__init__(parent)
        self.title("Borrow Config From")
        self.geometry("320x160")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.result = None
 
        tk.Label(self, text="Borrow config from which profile?",
                 bg=COLORS["bg"], fg=COLORS["fg"], font=FONTS["body"]).pack(pady=(16, 8))
        self._var = tk.StringVar(value=profiles[0])
        ttk.Combobox(self, textvariable=self._var, values=profiles,
                     state="readonly", width=28).pack()
        btn_row = tk.Frame(self, bg=COLORS["bg"])
        btn_row.pack(pady=16)
        StyledButton(btn_row, "OK", self._ok, "primary").pack(side="left", padx=6)
        StyledButton(btn_row, "Cancel", self.destroy, "ghost").pack(side="left")
 
    def _ok(self):
        self.result = self._var.get()
        self.destroy()
 
 
# ── Settings Panel ────────────────────────────────────────────────────────────
 
class SettingsPanel(tk.Frame):
    def __init__(self, parent, manager, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.manager = manager
        self.app = app
        self._build()
 
    def _build(self):
        content = tk.Frame(self, bg=COLORS["bg"])
        content.pack(padx=40, pady=24, fill="both", expand=True)
 
        SectionHeader(content, "Settings").pack(fill="x", pady=(0, 20))
 
        def path_row(parent, label, var, browse_fn):
            row = tk.Frame(parent, bg=COLORS["surface2"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, bg=COLORS["surface2"],
                     fg=COLORS["muted"], font=FONTS["small"], width=22, anchor="w").pack(side="left", padx=10, pady=8)
            ttk.Entry(row, textvariable=var, width=48).pack(side="left", padx=(0, 8), pady=8)
            StyledButton(row, "Browse…", browse_fn, "ghost").pack(side="left", pady=8)
 
        self._master_var = tk.StringVar(value=self.manager.settings.master_mods_dir)
        self._sims_var = tk.StringVar(value=self.manager.settings.sims_mods_dir)
 
        path_row(content, "Master Mods Folder", self._master_var, self._browse_master)
        path_row(content, "Sims 4 Mods Folder", self._sims_var, self._browse_sims)
 
        note = tk.Label(content,
            text="Master Mods Folder: your giant collection of all mods.\n"
                 "Sims 4 Mods Folder: where Sims 4 looks for mods (symlinks go here).",
            bg=COLORS["bg"], fg=COLORS["muted"], font=FONTS["small"], justify="left")
        note.pack(anchor="w", pady=12)
        
        # Log clearing toggle
        toggle_frame = tk.Frame(content, bg=COLORS["surface2"])
        toggle_frame.pack(fill="x", pady=(0, 12))
        self._clear_logs_var = tk.BooleanVar(value=self.manager.settings.clear_logs_on_switch)
        tk.Checkbutton(
            toggle_frame,
            text="  Clear mod log files when switching profiles",
            variable=self._clear_logs_var,
            bg=COLORS["surface2"], fg=COLORS["fg"],
            selectcolor=COLORS["bg"], activebackground=COLORS["surface2"],
            activeforeground=COLORS["accent"], font=FONTS["body"],
            cursor="hand2", bd=0, highlightthickness=0,
        ).pack(anchor="w", padx=10, pady=8)
        tk.Label(toggle_frame,
                 text="Removes .log and lastexception files from your Sims 4 Mods folder on each profile switch. "
                        "Recommended on for most players.",
                 bg=COLORS["surface2"], fg=COLORS["muted"], font=FONTS["small"],
                 wraplength=580, justify="left").pack(anchor="w", padx=10, pady=(0, 8))
 
        StyledButton(content, "Save Settings", self._save, "success").pack(anchor="w", pady=8)
 
        # App data location info
        tk.Label(content, text=f"App data: {self.manager.data_dir}",
                 bg=COLORS["bg"], fg=COLORS["border"], font=FONTS["small"]).pack(anchor="w", pady=(20, 0))
 
    def _browse_master(self):
        folder = filedialog.askdirectory(title="Select Master Mods Folder")
        if folder:
            self._master_var.set(folder)
 
    def _browse_sims(self):
        folder = filedialog.askdirectory(title="Select Sims 4 Mods Folder")
        if folder:
            self._sims_var.set(folder)
 
    def _save(self):
        self.manager.settings.master_mods_dir = self._master_var.get()
        self.manager.settings.sims_mods_dir = self._sims_var.get()
        self.manager.settings.clear_logs_on_switch = self._clear_logs_var.get()
        self.manager.save_settings()
        self.app.set_status("Settings saved.", COLORS["positive"])
 
    def refresh(self):
        self._master_var.set(self.manager.settings.master_mods_dir)
        self._sims_var.set(self.manager.settings.sims_mods_dir)
        self._clear_logs_var.set(self.manager.settings.clear_logs_on_switch)
 