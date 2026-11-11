"""Open the native Tk file picker used by Load Project."""

import json
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog


def ask_project_filename():
    root = tk.Tk()
    try:
        root.withdraw()
        return filedialog.askopenfilename()
    finally:
        root.destroy()


def choose_project_file():
    if sys.platform != "darwin":
        return ask_project_filename()

    # Tk and Dear PyGui both initialize AppKit. Start Tk on the main thread
    # of a separate process so it can create its own application object.
    command = [sys.executable]
    if not getattr(sys, "frozen", False):
        command.append(str(Path(__file__).resolve().parents[1] / "main.py"))
    command.append("--choose-project-file")
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)
