"""
Core logic: mod library, profiles, symlinks, config management.
"""
import os
import json
import shutil
import hashlib
import platform
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
import re


# ── Paths ────────────────────────────────────────────────────────────────────

def default_documents_path() -> Path:
    system = platform.system()
    if system == "Windows":
        import ctypes.wintypes
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, 5, 0, 0, buf)
        return Path(buf.value)
    elif system == "Darwin":
        return Path.home() / "Documents"
    else:
        return Path.home() / "Documents"

def default_sims_mods_path() -> Path:
    return default_documents_path() / "Electronic Arts" / "The Sims 4" / "Mods"

def app_data_path() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    p = base / "Sims4ModManager"
    p.mkdir(parents=True, exist_ok=True)
    return p


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class ModEntry:
    filename: str           # relative to master_mods_dir
    display_name: str
    file_hash: str = ""
    size_bytes: int = 0
    tags: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)


@dataclass
class ProfileConfig:
    """Represents one mod config file (e.g. MCCC settings)."""
    config_filename: str       # e.g. "MCCC_settings.cfg"
    source_profile: Optional[str] = None   # None = use own copy; str = borrow from that profile

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)


@dataclass
class Profile:
    name: str
    enabled_mods: list[str] = field(default_factory=list)   # filenames
    config_files: list[ProfileConfig] = field(default_factory=list)
    description: str = ""

    def to_dict(self):
        return {
            "name": self.name,
            "enabled_mods": self.enabled_mods,
            "config_files": [c.to_dict() for c in self.config_files],
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            name=d["name"],
            enabled_mods=d.get("enabled_mods", []),
            config_files=[ProfileConfig.from_dict(c) for c in d.get("config_files", [])],
            description=d.get("description", ""),
        )


# ── Settings ─────────────────────────────────────────────────────────────────

@dataclass
class AppSettings:
    master_mods_dir: str = ""
    sims_mods_dir: str = ""
    active_profile: str = ""
    clear_logs_on_switch: bool = True

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ── Manager ───────────────────────────────────────────────────────────────────

class ModManager:
    def __init__(self):
        self.data_dir = app_data_path()
        self.settings_file = self.data_dir / "settings.json"
        self.library_file = self.data_dir / "library.json"
        self.profiles_dir = self.data_dir / "profiles"
        self.configs_dir = self.data_dir / "mod_configs"
        self.profiles_dir.mkdir(exist_ok=True)
        self.configs_dir.mkdir(exist_ok=True)

        self.settings = self._load_settings()
        self.library: dict[str, ModEntry] = self._load_library()
        self.profiles: dict[str, Profile] = self._load_profiles()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load_settings(self) -> AppSettings:
        if self.settings_file.exists():
            with open(self.settings_file) as f:
                return AppSettings.from_dict(json.load(f))
        s = AppSettings(
            master_mods_dir=str(self.data_dir / "MasterMods"),
            sims_mods_dir=str(default_sims_mods_path()),
        )
        Path(s.master_mods_dir).mkdir(parents=True, exist_ok=True)
        return s

    def save_settings(self):
        with open(self.settings_file, "w") as f:
            json.dump(self.settings.to_dict(), f, indent=2)

    def _load_library(self) -> dict[str, ModEntry]:
        if self.library_file.exists():
            with open(self.library_file) as f:
                raw = json.load(f)
            return {k: ModEntry.from_dict(v) for k, v in raw.items()}
        return {}

    def save_library(self):
        with open(self.library_file, "w") as f:
            json.dump({k: v.to_dict() for k, v in self.library.items()}, f, indent=2)

    def _load_profiles(self) -> dict[str, Profile]:
        profiles = {}
        for p in self.profiles_dir.glob("*.json"):
            with open(p) as f:
                try:
                    pr = Profile.from_dict(json.load(f))
                    profiles[pr.name] = pr
                except Exception:
                    pass
        return profiles

    def save_profile(self, profile: Profile):
        safe = re.sub(r'[^\w\-]', '_', profile.name)
        path = self.profiles_dir / f"{safe}.json"
        with open(path, "w") as f:
            json.dump(profile.to_dict(), f, indent=2)

    def delete_profile(self, name: str):
        if name in self.profiles:
            del self.profiles[name]
        safe = re.sub(r'[^\w\-]', '_', name)
        p = self.profiles_dir / f"{safe}.json"
        if p.exists():
            p.unlink()

    # ── Library management ───────────────────────────────────────────────────

    @property
    def master_dir(self) -> Path:
        return Path(self.settings.master_mods_dir)

    @property
    def sims_dir(self) -> Path:
        return Path(self.settings.sims_mods_dir)

    MOD_EXTENSIONS = {".package", ".ts4script", ".cfg", ".ini", ".xml"}

    def _is_mod_file(self, path: Path) -> bool:
        return path.suffix.lower() in self.MOD_EXTENSIONS

    def _file_hash(self, path: Path) -> str:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def scan_master_library(self) -> dict:
        """Scan master dir, update library, return stats."""
        found: set[str] = set()
        duplicates: list[tuple[str, str]] = []
        hash_map: dict[str, list[str]] = {}
        new_count = 0

        for root, _, files in os.walk(self.master_dir):
            for fname in files:
                fpath = Path(root) / fname
                if not self._is_mod_file(fpath):
                    continue
                rel = str(fpath.relative_to(self.master_dir))
                found.add(rel)
                fhash = self._file_hash(fpath)
                hash_map.setdefault(fhash, []).append(rel)
                if rel not in self.library:
                    self.library[rel] = ModEntry(
                        filename=rel,
                        display_name=fname,
                        file_hash=fhash,
                        size_bytes=fpath.stat().st_size,
                    )
                    new_count += 1
                else:
                    self.library[rel].file_hash = fhash

        # Remove library entries for files no longer on disk
        removed = [k for k in self.library if k not in found]
        for k in removed:
            del self.library[k]

        # Find duplicates (same hash, different filename)
        for fhash, paths in hash_map.items():
            if len(paths) > 1:
                for p in paths[1:]:
                    duplicates.append((paths[0], p))

        self.save_library()
        return {"new": new_count, "removed": len(removed), "duplicates": duplicates, "total": len(self.library)}

    def add_mods_from_folder(self, source_dir: Path) -> int:
        """Copy mod files from source_dir into master library root."""
        count = 0
        for root, _, files in os.walk(source_dir):
            for fname in files:
                src = Path(root) / fname
                if not self._is_mod_file(src):
                    continue
                dest = self.master_dir / fname
                if not dest.exists():
                    shutil.copy2(src, dest)
                    count += 1
        return count

    # ── Symlink management ───────────────────────────────────────────────────

    def _clear_sims_mods_symlinks(self):
        """Remove all symlinks we previously created in the Sims mods folder."""
        if not self.sims_dir.exists():
            return
        for item in self.sims_dir.iterdir():
            if item.is_symlink():
                item.unlink()

    def _clear_sims_config_symlinks(self):
        """Remove config symlinks."""
        if not self.sims_dir.exists():
            return
        for item in self.sims_dir.iterdir():
            if item.is_symlink():
                item.unlink()

    def activate_profile(self, name: str) -> dict:
        """Deactivate current profile and activate the named one."""
        if name not in self.profiles:
            raise ValueError(f"Profile '{name}' not found.")

        # Ensure Sims Mods folder exists
        self.sims_dir.mkdir(parents=True, exist_ok=True)

        # Remove only symlinks previously created by another profile
        self._clear_sims_mods_symlinks()

        # Clear logs left in the Mods folder (if option enabled in settings)
        if self.settings.clear_logs_on_switch:
            self._clear_sims_log_files()

        profile = self.profiles[name]
        linked = 0
        missing = []

        # ── Symlink enabled mods ────────────────────────────────────────────────────────
        for rel_path in profile.enabled_mods:
            src = self.master_dir / rel_path
            if not src.exists():
                missing.append(rel_path)
                continue
            # Flatten to Sims mods root
            link_name = Path(rel_path).name
            dest = self.sims_dir / link_name
            # Handle name collision from different subfolders
            if dest.exists() or dest.is_symlink():
                stem = dest.stem
                suffix = dest.suffix
                dest = self.sims_dir / f"{stem}__{Path(rel_path).parent.name}{suffix}"
            # Create symlink to the master library file
            try:
                os.symlink(src.resolve(), dest)
                linked += 1
            except Exception:
                # If symlink creation fails, continue; attempt to activate other mods/configs
                missing.append(rel_path)

        # ── Config files ──────────────────────────────────────────────────────────────────
        for cfg in profile.config_files:
            # Determine source: profile's own stored copy or borrow from another profile
            if cfg.source_profile:
                cfg_src = self._config_path(cfg.source_profile, cfg.config_filename)
            else:
                cfg_src = self._config_path(name, cfg.config_filename)

            # If profile copy missing, fall back to global library
            if not cfg_src.exists():
                lib_src = self._config_library_path(cfg.config_filename)
                if lib_src.exists():
                    cfg_src = lib_src

            if not cfg_src.exists():
                # Nothing to copy for this config
                continue

            dest = self.sims_dir / cfg.config_filename

            # Backup existing file in Sims Mods folder (if any)
            try:
                if dest.exists() and not dest.is_symlink():
                    backup = self.sims_dir / (cfg.config_filename + ".backup")
                    shutil.copy2(dest, backup)
                # Ensure any existing dest (file or symlink) is removed before copying
                if dest.exists() or dest.is_symlink():
                    dest.unlink()
            except Exception:
                # Best-effort; continue even if backup/unlink fails
                pass

            # Copy chosen source into the Sims Mods folder with the hardcoded filename
            try:
                shutil.copy2(cfg_src, dest)
            except Exception:
                # Ignore copy errors for now; activation will continue for other files
                pass

        self.settings.active_profile = name
        self.save_settings()
        return {"linked": linked, "missing": missing}
    
    LOG_EXTENSIONS = {".log", ".html", ".txt"}
    LOG_KEYWORDS = {"log", "exception", "lastexception", "error"}
    
    def _clear_sims_log_files(self):
        """Delete log files left by mods in the Sims 4 Mods folder."""
        if not self.sims_dir.exists():
            return
        deleted = 0
        for item in self.sims_dir.iterdir():
            if item.is_file() and not item.is_symlink():
                ext = item.suffix.lower()
                name_lower = item.name.lower()
                if ext in self.LOG_EXTENSIONS and any(kw in name_lower for kw in self.LOG_KEYWORDS):
                    try:
                        item.unlink()
                        deleted += 1
                    except Exception:
                        pass
        return deleted

    def deactivate_current(self):
        self._clear_sims_mods_symlinks()
        if self.settings.clear_logs_on_switch:
            self._clear_sims_log_files()
        self.settings.active_profile = ""
        self.save_settings()

    # ── Config file management ───────────────────────────────────────────────

    def _config_path(self, profile_name: str, filename: str) -> Path:
        safe = re.sub(r'[^\w\-]', '_', profile_name)
        d = self.configs_dir / safe
        d.mkdir(exist_ok=True)
        return d / filename

    def save_config_file(self, profile_name: str, filename: str, content: bytes):
        path = self._config_path(profile_name, filename)
        with open(path, "wb") as f:
            f.write(content)

    def list_config_files(self, profile_name: str) -> list[str]:
        safe = re.sub(r'[^\w\-]', '_', profile_name)
        d = self.configs_dir / safe
        if not d.exists():
            return []
        return [p.name for p in d.iterdir() if p.is_file()]
    
    def _config_library_path(self, filename: str) -> Path:
        """Path to a config stored in the global library (configs_dir root)."""

    def save_config_to_library(self, filename : str, content: bytes):
        """Save or overwrite a config file in the global config library."""
        path = self._config_library_path(filename)
        with open(path, "wb") as f:
            f.write(content)

    def list_library_configs(self) -> list[str]:
        """List config files stored in the global config library (not per profile)."""
        return sorted([p.name for p in self.configs_dir.iterdit() if p.is_file()])
    
    def load_library_config(self, filename: str) -> bytes:
        """Return raw bytes of a stored config file in the global library."""
        path = self.config_library_path(filename)
        return path.read_bytes()

    # ── Import / Export ───────────────────────────────────────────────────────

    def export_profile(self, name: str, dest_path: Path):
        """Export profile as a shareable JSON file (no actual mod files, just mod list)."""
        if name not in self.profiles:
            raise ValueError(f"Profile '{name}' not found.")
        export = {
            "schema": "sims4mm_profile_v1",
            "profile": self.profiles[name].to_dict(),
        }
        with open(dest_path, "w") as f:
            json.dump(export, f, indent=2)

    def import_profile(self, src_path: Path) -> tuple[Profile, list[str]]:
        """Import a profile JSON. Returns (profile, missing_mods)."""
        with open(src_path) as f:
            data = json.load(f)
        if data.get("schema") != "sims4mm_profile_v1":
            raise ValueError("Not a valid Sims 4 Mod Manager profile file.")
        profile = Profile.from_dict(data["profile"])
        missing = [m for m in profile.enabled_mods if m not in self.library]
        # Avoid name collision
        base = profile.name
        i = 2
        while profile.name in self.profiles:
            profile.name = f"{base} ({i})"
            i += 1
        self.profiles[profile.name] = profile
        self.save_profile(profile)
        return profile, missing

    # ── Duplicate detection ───────────────────────────────────────────────────

    def find_duplicates(self) -> list[list[str]]:
        """Return groups of files with identical content hashes."""
        hash_map: dict[str, list[str]] = {}
        for rel, entry in self.library.items():
            if entry.file_hash:
                hash_map.setdefault(entry.file_hash, []).append(rel)
        return [paths for paths in hash_map.values() if len(paths) > 1]
