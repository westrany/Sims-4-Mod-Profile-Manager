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

<img width="958" height="624" alt="image" src="https://github.com/user-attachments/assets/b9d61823-915a-4a11-941c-5dff854c387c" />

1. Open **Settings** (bottom of sidebar)
2. Set **Master Mods Folder** — this is where ALL your mods live (your giant collection)
   - Recommended: `C:\Users\<You>\Documents\Sims 4 Master Mods`
4. Set **Sims 4 Mods Folder** — usually: 
   - Windows: `C:\Users\<You>\Documents\Electronic Arts\The Sims 4\Mods`
5. Save settings.

---

## How to Use

### Importing Mods into the Library

<img width="2000" height="1063" alt="image" src="https://github.com/user-attachments/assets/90bb7900-ecfd-41f3-befa-ab66e79f65a0" />

- **Mod Library** → **Import Folder** to copy mods into your master library, or you can manually move them there yourself.
   - This is particularly useful if you currently have mods in your Sims 4 Mods Folder and want to move them to your Master Mods folder. 
- Click ↻ Scan Library to index all mods (do this after adding files manually).
   - Note that this may take a couple of seconds, especially if you have a large mods folder. You can check if your mods are still being scanned by looking at the bottom left of the screen where you should see a `Scanning library...` message during this process.

### Creating Profiles

- **Profiles** → **+ New** → name it
<img width="372" height="586" alt="image" src="https://github.com/user-attachments/assets/a777b754-495f-4fb0-8757-0efd303237f0" />
<img width="249" height="210" alt="image" src="https://github.com/user-attachments/assets/ea8dadd1-9ae9-473f-8135-59a4e481cd39" />

- **Edit Mods…** to pick mods.
<img width="2012" height="1068" alt="image" src="https://github.com/user-attachments/assets/8955fdf3-17e8-435d-a1d7-6e2a2b1003a6" />

- Use search, double‑click, or **Add Selected** → to include mods.
- Save changes.
<img width="1125" height="787" alt="image" src="https://github.com/user-attachments/assets/d7a18e3f-d08c-433b-9eda-1dda077b9a5b" />

- You should see all the mods you selected in the `Enabled Mods` window.
<img width="1916" height="1015" alt="image" src="https://github.com/user-attachments/assets/3df3291b-f598-4456-b5e7-46cff03a261e" />


### Activating a Profile

- Select profile → **▶ Activate Profile**.
- The app **removes previously created symlinks** and **creates new symlinks** from your Sims 4 Mods folder to the Master Folder library so only selected mods are visible to the game. 

### Sharing Profiles

- **Export** a profile to a `.json` file; **Import** warns about missing mods. 

### Mod Config Files

<img width="1915" height="1015" alt="image" src="https://github.com/user-attachments/assets/29862250-2157-48c6-9120-1959c5498abb" />

- **Mod Configs** → select profile → **Upload Config File** to store per‑profile configs.
- **Set Borrow Source…** to share a config between profiles. Configs are symlinked into the Mods folder on activation.

### Duplicate Detection

<img width="1916" height="1018" alt="image" src="https://github.com/user-attachments/assets/f5bf7618-59ba-4e10-8eb1-e7e9498adf0b" />

- **Duplicates** → **↻ Check Duplicates** compares file **hashes** (not just names) to find identical files. Delete duplicates from the master folder and re‑scan.
   - Note that when Scanning your library, the find duplicates feature will automatically occur and will let you know with a `X duplicate groups found.` message on the bottom left corner if you have duplicates or not.
   - After deleting a duplicate (which sends the file to the Recycle Bin in case you made a mistake and want to recover your file), a message will appear on the bottom left corner letting you know which file or files were sent to the Recycle Bin.

---

## Data Storage
All app data (profiles, library index, stored configs) lives in:
- **Windows:** `%APPDATA%\Sims4ModManager`
   - The settings panel shows the exact path below the green `Save Settings` button.

---

## Developer Notes & Distribution
- I have not checked wether this works on Linux/MAC and I myself do not plan to do so. If anyone wants to double check this, that would be greatly appreciated and credit shall be duly given.
- Currently this program requires Python installed and needs to be accessed via a terminal, which is not very user friendly for non-tech literate folks. If anyone wishes to make a more friendly way to access this, do get in touch :)

---

## Troubleshooting & Notes
- **Windows symlink creation** may require Administrator privileges or Developer Mode. That is why by default this program will ask you to run it with Admin privileges.
- If Windows Defender blocks Python, allow python.exe through Controlled Folder Access. 

