import dearpygui.dearpygui as dpg
import numpy as np

class BrakeTempView: 
    
    def __init__(self, DataManager):
        self.dm = DataManager
        self.df = DataManager.df  
        self.path = DataManager.path
        self.size = 150
        self.inner_radius = 22.5
        self.outer_radius = 70
        self.bands = 16

    
    def build(self, parent_tag):
        """Called once to populate the window."""

        if self.path == "":
                     
            dpg.add_text("Brake Temp Analysis", parent=parent_tag)
            dpg.add_separator(parent=parent_tag)
            dpg.add_text("Load a file to see data.", 
                        tag="brake_temp_placeholder", parent=parent_tag) 
            
        else:
            self.refresh()


    def refresh(self):
        """Called after new data loads to update content."""


        

        if dpg.does_item_exist("break_temp_placeholder"):
            dpg.delete_item("break_temp_placeholder")

        temps = []
        time = self.df["Time"].tolist()
        for i in range (len(time)):
            temps.append([float(self.df["RR IR T1"][i]), 
                          float(self.df["RR IR T2"][i]), 
                          float(self.df["RR IR T3"][i]), 
                          float(self.df["RR IR T4"][i]), 
                          float(self.df["RR IR T5"][i]), 
                          float(self.df["RR IR T6"][i]), 
                          float(self.df["RR IR T7"][i]), 
                          float(self.df["RR IR T8"][i]), 
                          float(self.df["RR IR T9"][i]), 
                          float(self.df["RR IR T10"][i]), 
                          float(self.df["RR IR T11"][i]), 
                          float(self.df["RR IR T12"][i]), 
                          float(self.df["RR IR T13"][i]), 
                          float(self.df["RR IR T14"][i]), 
                          float(self.df["RR IR T15"][i]), 
                          float(self.df["RR IR T16"][i])
                          ])
            
        with dpg.texture_registry(show=False):
                            dpg.add_dynamic_texture(
                                width=self.size,
                                height=self.size,
                                default_value=self.generate_disc_texture(temps[0]),
                                tag="disc_texture"
                            )

        self.dm.update_brake_temps(temps)
        self.dm.generate_disc_function(self.generate_disc_texture)
        with dpg.child_window(tag="Brake Temp Heatmap"):
            
            with dpg.group(horizontal=True):
                with dpg.child_window(width=360, height=380, border=True):
                    dpg.add_text(tag = "Brake Disc View", label="Brake Disc View (Paused)")
                    dpg.add_spacer(height=5)
                    dpg.add_image("disc_texture", width=300, height=300)
                    with dpg.group(horizontal = True):
                                    
                        dpg.add_button(label="Play", callback=lambda: self.dm.play_brake_temps(True))
                        dpg.add_button(label="Pause", callback=lambda: self.dm.play_brake_temps(False))
                        dpg.add_input_float(tag = "Play rate menu", 
                                            label="play rate", 
                                            width = 150,
                                            step = 0.25, 
                                            default_value = 1, 
                                            min_value= 0.25, min_clamped = True, 
                                            max_value = 3, max_clamped = True,
                                            callback = lambda: self.dm.set_brake_temp_step(dpg.get_value("Play rate menu"))
                                           )
                        
                with dpg.child_window(width=420, height=380, border=True):
                    dpg.add_text("Channel Temperatures")
                    dpg.add_separator()
                    dpg.add_text("", tag="temp_text")
            
                dpg.add_spacer(height=8)
            
               
                    
        

    def temp_to_color(self, temp):
        # not exact conversions
        blue_limit = 50   # 120  F
        yellow_point = 100 # 210 F
        red_point = 150    # 300 F

        # Below 300 F -> fully blue
        if temp <= blue_limit:
            return 0.0, 0.0, 1.0

        # Between 300 F and 350 F -> blue to yellow
        elif temp <= yellow_point:
            t = (temp - blue_limit) / (yellow_point - blue_limit)

            r = t
            g = t
            b = 1.0 - t

            return r, g, b

        # Between 350 F and 550 F -> yellow to red
        elif temp <= red_point:
            t = (temp - yellow_point) / (red_point - yellow_point)

            r = 1.0
            g = 1.0 - t
            b = 0.0

            return r, g, b

        # Above 550 F -> fully red
        else:
            return 1.0, 0.0, 0.0
    
    def generate_disc_texture(self,temps):
            """
            Create RGBA image with:
            - transparent center hole
            - transparent outside the disc
            - 16 concentric temperature bands
            """
            size = self.size
            cx = size / 2
            cy = size / 2
    
            image = np.zeros((size, size, 4), dtype=np.float32)
    
            band_thickness = (self.outer_radius - self.inner_radius) / self.bands
    
            y, x = np.indices((size, size))
            dx = x - cx
            dy = y - cy
            r = np.sqrt(dx**2 + dy**2)
    
            # Visible region = between inner and outer radius
            visible_mask = (r >= self.inner_radius) & (r <= self.outer_radius)
    
            # Compute band index for visible pixels
            band_index = ((r - self.inner_radius) / band_thickness).astype(int)
            band_index = np.clip(band_index, 0, self.bands - 1)
    
            for band in range(self.bands):
                mask = visible_mask & (band_index == band)
                temp = temps[band]
                red, green, blue = self.temp_to_color(temp)
    
                image[mask, 0] = red
                image[mask, 1] = green
                image[mask, 2] = blue
                image[mask, 3] = 1.0   # fully visible
    
            return image.flatten().tolist()