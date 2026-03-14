# Sims 4 Mod Profile Manager

Manage mods with symlinks — toggle them on/off and switch between mod lists without touching a single file

---

## Requirements

- Python 3.10+
- Tkinter (usually bundled with Python)
- No third-party packages needed

---

## Running the App

```bash
python main.py
```

---

## First-Time Setup

1. Open **Settings** (bottom of sidebar)
2. Set **Master Mods Folder** — this is where ALL your mods live (your giant collection)
3. Set **Sims 4 Mods Folder** — usually:
   - Windows: `C:\Users\<You>\Documents\Electronic Arts\The Sims 4\Mods`
4. Save settings

---

## How to Use

### Importing Mods into the Library

- Go to **Mod Library**
- Click **Import Folder** to copy mods from any folder into your master library
- Click **↻ Scan Library** to index all mods (do this after adding files manually too)

### Creating Profiles

- Go to **Profiles** → **+ New**
- Name it (e.g. "Main Mods", "Medieval Mods")
- Click **Edit Mods…** to open the mod picker:
  - Search and double-click or select + click "Add Selected →"
  - Right side shows what's enabled; remove mods with "← Remove Selected"
  - Click **Save & Close**

### Activating a Profile

- Select your profile → **▶ Activate Profile**
- This creates symlinks in your Sims 4 Mods folder pointing to your master library
- Only the mods you selected will be visible to the game
- Switching profiles clears old symlinks and creates new ones instantly

### Sharing Profiles

- **Export**: Select a profile → **Export…** → share the `.json` file with friends
- **Import**: **Import** button in the Profiles panel → the app will warn which mods your friend has that you're missing

### Mod Config Files (MCCC, Wicked Whims, etc.)

- Go to **Mod Configs**
- Select a profile
- Click **Upload Config File** to store a mod's config for that profile
- To share a config between profiles: select a config → **Set Borrow Source…** → pick another profile
- When activating a profile, its config files are also symlinked into the Mods folder

### Duplicate Detection

- Go to **Duplicates** → **↻ Check Duplicates**
- Compares file hashes (not just names) — finds truly identical files
- Manually delete the duplicates from your master folder, then re-scan

---

## How Symlinks Work

When you activate a profile, the app:
1. Removes all symlinks it previously created in your Sims 4 Mods folder
2. Creates new symlinks pointing from the Mods folder → your master library files
3. Sims 4 sees the mods as if they were physically there

Your master library is **never modified**. Your Sims 4 folder stays clean.
If you uninstall this app, just delete the symlinks from your Mods folder.

---

## Data Storage

All app data (profiles, library index, stored configs) lives in:
- Windows: `%APPDATA%\Sims4ModManager\`
- Mac/Linux: `~/.local/share/Sims4ModManager/`

The settings panel shows the exact path.

---

## Notes

- On **Windows**, creating symlinks may require running as Administrator, or enabling Developer Mode in Windows Settings → For Developers → Developer Mode
- The app stores mod metadata (filename, size, hash) but never copies your mod files — only indexes them
- Config files you upload ARE copied into the app data directory, one copy per profile
- You may encounter Python permission issues where Windows Defender blocks your python.exe from running; you can fix this by
            1. Click "Controlled folder access settings" in that same notification (or go to Windows Security → Virus & threat protection → Manage ransomware protection)
            2. Click "Allow an app through Controlled folder access"
            3. Click "Add an allowed app" → "Browse all apps"
            4. Navigate to your Python install and select python.exe — likely at C:\Python312\python.exe
            5. Click Open, then confirm 
