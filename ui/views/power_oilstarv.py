import dearpygui.dearpygui as dpg


class OilStarvationView:

    def __init__(self, DataManager):
            self.df = DataManager.df


    def build(self, parent_tag):
        """Called once to populate the window."""
        dpg.add_text("Oil Starvation Analysis", parent=parent_tag)
        dpg.add_separator(parent=parent_tag)
        dpg.add_text("Load a file to see data.", 
                     tag="oil_starvation_placeholder", parent=parent_tag)

        #TODO move to refresh after tk file selection todo in home_page is done
        #TODO update to follow guidelines
        time = self.df["Time"].tolist()
        rpm = self.df["ECU RPM"].tolist()
        oil_pressure = self.df["ECU OIL P"].tolist()
        print (rpm)
        
        with dpg.plot(label="Line Series", height=800, width=800):
            
            dpg.add_plot_legend()

            
            dpg.add_plot_axis(dpg.mvXAxis, label="x")
            dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis")
            dpg.add_line_series(x=time, y=oil_pressure, label="Oil Presure", parent="y_axis")
            dpg.add_line_series(x=time, y=rpm, label="RPM", parent="y_axis")
        

    def refresh(self):
        """Called after new data loads to update content."""

        if dpg.does_item_exist("oil_starvation_placeholder"):
            dpg.delete_item("oil_starvation_placeholder")

        
