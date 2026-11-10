import dearpygui.dearpygui as dpg
import time



class RenderManager():

    def __init__(self):
        self.play_brake_temps = False
        self.brake_temps = []
        self.index = 1
        self.step = 1
        self.update_interval = 1 / 20 

    def start(self):

        last_update = time.perf_counter()
        
        
        while dpg.is_dearpygui_running():

            #TODO: change the susp_brake to brake temp heatmap once other graphs are done
            if self.play_brake_temps:

                if dpg.is_item_shown("susp_brake") == False:
                    self.play_brake_temps = False
                    
                current_time = time.perf_counter()
                    
                if current_time - last_update >= self.update_interval:
                        
                    temps = self.brake_temps[self.index]
                        
                    dpg.set_value("heatmap", value = [temps])
                    self.index = (self.index + 1)%len(self.brake_temps)
                    last_update = current_time



            dpg.render_dearpygui_frame()


    

