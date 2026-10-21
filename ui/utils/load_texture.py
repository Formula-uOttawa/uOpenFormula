import os
import sys
import dearpygui.dearpygui as dpg


def resource_path(relative_path):
    # Inside the exe, bundled files are unpacked to a temp folder (sys._MEIPASS).
    # From source, use the folder you ran the program from.
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)


def load_texture(file_path):
    full_path = resource_path(file_path)
    result = dpg.load_image(full_path)
    if result is None:
        raise FileNotFoundError(f"Could not load image: {full_path}")
    w, h, channels, data = result
    with dpg.texture_registry():
        texture = dpg.add_static_texture(w, h, data)
    return texture
