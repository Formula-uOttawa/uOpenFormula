import dearpygui.dearpygui as dpg


class BrakeTempView: 
    
    def __init__(self, DataManager):
        self.dm = DataManager
        self.df = DataManager.df  
        self.path = DataManager.path

    
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

        self.dm.update_brake_temps(temps)
        
        with dpg.child_window(tag="Brake Temp Heatmap"):
            with dpg.plot(label="Temperature Heatmap", width=700, height=450):
                dpg.add_plot_axis(dpg.mvXAxis, label="Columns")
                dpg.add_plot_axis(dpg.mvYAxis, label="Rows", tag="heat_y")
                
                dpg.add_heat_series(
                            [0.0] * 16,
                            rows=4,
                            cols=4,
                            parent="heat_y",
                            scale_min=0,
                            scale_max=200,
                            bounds_min=(0, 0),
                            bounds_max=(4, 4),
                            format="%.1f",
                            tag="heatmap"
                        )
            with dpg.group(horizontal = True):

                dpg.add_button(label="Play", callback=lambda: self.dm.play_brake_temps(True))
                dpg.add_button(label="Pause", callback=lambda: self.dm.play_brake_temps(False))
                dpg.add_input_float(tag = "Play rate menu", 
                                    label="play rate", 
                                    width = 200,
                                    step = 0.25, 
                                    default_value = 1, 
                                    min_value= 0.25, min_clamped = True, 
                                    max_value = 3, max_clamped = True,
                                    callback = lambda: self.dm.set_brake_temp_step(dpg.get_value("Play rate menu"))
                                    )