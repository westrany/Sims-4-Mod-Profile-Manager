"""
Sims 4 Mod Profile Manager - Entry Point
"""
import sys
import ctypes
import subprocess
import tkinter as tk
from tkinter import messagebox
from app.gui import ModManagerApp

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def ask_elevation():
    
    root = tk.Tk()
    root.withdraw()
    result = messagebox.askyesno(
        "Run as Administrator?",
        "Creating symlinks requires Administrator priviledges on Windoes.\n\n"
        "Run as Administrator?\n\n"
        "(Choose No if you have Developer Mode enabled in Windows Settings)"
    )
    root.destroy()
    return result     

def main():
    app = ModManagerApp()
    app.mainloop()

if __name__ == "__main__":
    if sys.platform == "win32" and not is_admin():
        if ask_elevation():
            # Re-launch the script with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
    main()
