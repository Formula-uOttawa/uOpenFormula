import dearpygui.dearpygui as dpg
import time



class RenderManager():

    def __init__(self):
        self.show_brake_temps=False
        self.brake_temps=[]


    def start(self):

        last_update = time.perf_counter()
        update_interval = 1 / 20  # 20 FPS
        i = 1
        while dpg.is_dearpygui_running():

            if self.show_brake_temps:
                current_time = time.perf_counter()
                 
                if current_time - last_update >= update_interval:

                    temps = self.brake_temps[i]
                    # Update the heatmap
                    dpg.set_value("heatmap", value = [temps])
                    i = (i+1)%len(self.brake_temps)
                    last_update = current_time

            dpg.render_dearpygui_frame()


    

