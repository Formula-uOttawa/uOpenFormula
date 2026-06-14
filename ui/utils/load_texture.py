import dearpygui.dearpygui as dpg

def load_texture(file_path):
        w, h, channels, data = dpg.load_image(file_path)
        with dpg.texture_registry():
            texture = dpg.add_static_texture(w, h, data)
        return (texture)