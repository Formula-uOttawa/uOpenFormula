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
        self.setup_disc_geometry() # assigns pixels to bands for heatmap

    
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

        # generates a list containing lists of all 16 bands for each time stamp
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

        # generates the texture for the heatmap  
        with dpg.texture_registry(show=False):
                            dpg.add_dynamic_texture(
                                width=self.size,
                                height=self.size,
                                default_value=self.generate_disc_texture(temps[0]),
                                tag="disc_texture"
                            )

        # sends the temps list, and the heatmap update function to data manager
        self.dm.update_brake_temps(temps)
        self.dm.generate_disc_function(self.generate_disc_texture)

        with dpg.child_window(tag="Brake Temp Heatmap"):
            
            with dpg.group(horizontal=True):
                with dpg.child_window(tag = "brake_disc_window", width=((dpg.get_viewport_width()-265)/2), height=430, no_scroll_with_mouse=True):
                    dpg.add_text(tag = "Brake Disc View", label="Brake Disc View (Paused)")
                    dpg.add_image("disc_texture", width=300, height=300)
                    dpg.add_spacer(height=50)

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
                        
                with dpg.child_window(tag = "channel_temp_window",width=((dpg.get_viewport_width()-265)/2), height=430, border=True):
                    dpg.add_text("Channel Temperatures")
                    dpg.add_separator()
                    dpg.add_text("", tag="temp_text")
            
                dpg.add_spacer(height=8)
        dpg.bind_item_theme("brake_disc_window", "cyan_border_theme")
        dpg.bind_item_theme("channel_temp_window", "cyan_border_theme")

    def temp_to_color(self, temp):
        """
        Converts Brake Temps to RGB values

        """

        # not exact conversions
        blue_temp = 50   # 120  F
        yellow_temp = 100 # 210 F
        red_temp = 150    # 300 F

        # below blue_temp is fully blue
        if temp <= blue_temp:
            return 0.0, 0.0, 1.0

        # between blue_temp and yellow_temp 
        elif temp <= yellow_temp:
            colour_ratio = (temp - blue_temp) / (yellow_temp - blue_temp)

            red = colour_ratio
            green = colour_ratio
            blue = 1.0 - colour_ratio

            return red, green, blue

        # between yellow_temp and red_temp
        elif temp <= red_temp:
            colour_ratio = (temp - yellow_temp) / (red_temp - yellow_temp)

            red = 1.0
            green = 1.0 - colour_ratio
            blue = 0.0

            return red, green, blue

        # fully red
        else:
            return 1.0, 0.0, 0.0

        
    def setup_disc_geometry(self):

        # center point of the disc
        x_centre = self.size / 2
        y_centre = self.size / 2

        band_thickness = (
            self.outer_radius - self.inner_radius
        ) / self.bands

        # position of a pixel
        y_value, x_value = np.indices((self.size, self.size))

        # distance of a pixel from the centre
        x_distance = x_value - x_centre
        y_distance = y_value - y_centre

        # distance in a straight line
        hyp = np.sqrt(x_distance**2 + y_distance**2)

        # makes only the pixels inside the wanted area visable
        # think about the hole in the centre not showing and the outside being round
        self.visible_mask = (
            (hyp >= self.inner_radius) &
            (hyp <= self.outer_radius)
        )

        band_index = ( (hyp - self.inner_radius) / band_thickness ).astype(int)

        band_index = np.clip( band_index, 0, self.bands - 1)

        # band 1 on the outside (flips the bands)
        self.band_index = self.bands - 1 - band_index

        # assigns and calculates which band each pixel belongs to
        self.band_masks = [
            self.visible_mask & (self.band_index == band)
            for band in range(self.bands)
        ]


    def generate_disc_texture(self, temperatures):
        """
        updates the heatmaps
        """
        # the actual image that is shown (initally all pixels have a 0 value)
        image = np.zeros(
            (self.size, self.size, 4),
            dtype=np.float32
        )

        # the temps are converted to RGB values for each band then converted to python list
        for band in range(self.bands):

            mask = self.band_masks[band]

            red, green, blue = self.temp_to_color(
                temperatures[band]
            )

            image[mask, 0] = red
            image[mask, 1] = green
            image[mask, 2] = blue
            image[mask, 3] = 1.0

        return image.flatten().tolist()