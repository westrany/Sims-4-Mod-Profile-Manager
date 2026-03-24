# Sims 4 Mod Profile Manager

Manage mods with symlinks — toggle them on/off and switch between mod lists without touching a single file

---

## Requirements

- Python 3.10+
- Tkinter (usually bundled with Python)
- No third-party packages needed

---

## Running the App

Open a terminal window on the same folder where `main.py` is and run the following:

```bash
python main.py
```

---

## First-Time Setup

1. Open **Settings** (bottom of sidebar)
2. Set **Master Mods Folder** — this is where ALL your mods live (your giant collection)
   - Recommended: `C:\Users\<You>\Documents\Sims 4 Master Mods`
4. Set **Sims 4 Mods Folder** — usually: 
   - Windows: `C:\Users\<You>\Documents\Electronic Arts\The Sims 4\Mods`
5. Save settings

---

## How to Use

### Importing Mods into the Library

- **Mod Library** → **Import Folder** to copy mods into your master library.
- Click ↻ Scan Library to index all mods (do this after adding files manually).

### Creating Profiles

- **Profiles** → **+ New** → name it → **Edit Mods…** to pick mods.
- Use search, double‑click, or **Add Selected** → to include mods.
- Save changes.

### Activating a Profile

- Select profile → **▶ Activate Profile**.
- The app **removes previously created symlinks** and **creates new symlinks** from your Sims 4 Mods folder to the Master Folder library so only selected mods are visible to the game. 

### Sharing Profiles

- **Export** a profile to a `.json` file; **Import** warns about missing mods. 

### Mod Config Files

- **Mod Configs** → select profile → **Upload Config File** to store per‑profile configs.
- **Set Borrow Source…** to share a config between profiles. Configs are symlinked into the Mods folder on activation. 

### Duplicate Detection

- **Duplicates** → **↻ Check Duplicates** compares file **hashes** (not just names) to find identical files. Delete duplicates from the master folder and re‑scan.

---

## Data Storage
All app data (profiles, library index, stored configs) lives in:
- **Windows:** `%APPDATA%\Sims4ModManager`
The settings panel shows the exact path.

---

## Developer Notes & Distribution
- I have not checked wether this works on Linux/MAC and I myself do not plan to do so. If anyone wants to double check this, that would be greatly appreciated and credit shall be duly given.
- Currently this program requires Python installed and needs to be accessed via a terminal, which is not very user friendly for non-tech literate folks. If anyone wishes to make a more friendly way to access this, do get in touch :)

---

## Troubleshooting & Notes
- **Windows symlink creation** may require Administrator privileges or Developer Mode. That is why by default this program will ask you to run it with Admin privileges.
- If Windows Defender blocks Python, allow python.exe through Controlled Folder Access. 

