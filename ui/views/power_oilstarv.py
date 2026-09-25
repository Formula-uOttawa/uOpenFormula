import dearpygui.dearpygui as dpg


class OilStarvationView:

    def __init__(self, DataManager):
            
        self.df = DataManager.df
        self.path = DataManager.path
        self.current_graph = None
        self.oil_operating_upper = [0.00,5.00,5.0,5,5.5,5.5,6,6.2,6.2,6.2]
        self.oil_operating_lower = [0.00,2.1,2.1,2.1,2,2,2,2,2,2]
        self.oil_operating_RPM = [0,1000,2000,3000,4000,6000,8000,10000,12000,14000]
        

    def show_graph(self, showing_graph):
        if self.current_graph != None :
             dpg.hide_item(self.current_graph)

        self.current_graph = showing_graph

        dpg.show_item(showing_graph)
        


    def build(self, parent_tag):
        """Called once to populate the window."""

        if self.path == "":
             
            dpg.add_text("Oil Starvation Analysis", parent=parent_tag)
            dpg.add_separator(parent=parent_tag)
            dpg.add_text("Load a file to see data.", 
                     tag="oil_starvation_placeholder", parent=parent_tag) 
        else:
            self.refresh()

        
        #TODO update to follow pep8 guidelines
        #TODO update the ui look on the menu bar
        #TODO make it so that all the refresh functions run when a new file path is chosen
       
                       

    def refresh(self):
        """Called after new data loads to update content."""

        if dpg.does_item_exist("oil_starvation_placeholder"):
            dpg.delete_item("oil_starvation_placeholder")
        

        time = self.df["Time"].tolist()
        rpm = self.df["ECU RPM"].tolist()
        oil_pressure = self.df["ECU OIL P"].tolist()
        oil_p_scaled = (self.df["ECU OIL P"] * 1000).tolist()
        lat_g = self.df["GPS LatAcc"].tolist()
        long_g = self.df["GPS LonAcc"].tolist()
        lat_g_low = []
        lon_g_low = []
        lat_g_normal = []
        lon_g_normal = []
        lat_g_high = []
        lon_g_high = []
        
        for i in range(len(lat_g)):
        
            for j in range(len(self.oil_operating_RPM)):
                          
                if round(rpm[i],-3) <= self.oil_operating_RPM[j]:
        
                    if oil_pressure[i] < self.oil_operating_lower[j]:
                        lat_g_low.append(lat_g[i])
                        lon_g_low.append(long_g[i])
                    elif oil_pressure[i] > self.oil_operating_upper[j]:
                        lat_g_high.append(lat_g[i])
                        lon_g_high.append(long_g[i])
                    else:
                        lat_g_normal.append(lat_g[i])
                        lon_g_normal.append(long_g[i])
        
                    break
                                 
                                  
        
        with dpg.menu_bar(tag="Oil Starvation Menu Bar"):
            dpg.add_menu_item(label="Rpm & Oil Pressure", callback=lambda:self.show_graph("Rpm & Oil Pressure graph"))
            dpg.add_menu_item(label="G-forces & Oil Pressure", callback=lambda:self.show_graph("G-forces & Oil Pressure graph"))
            dpg.add_menu_item(label="G-forces & Low Oil Pressure Events", callback=lambda:self.show_graph("G-forces & Low Oil Pressure plot"))
            dpg.add_menu_item(label="Rpm vs Oil Pressure", callback=lambda:self.show_graph("Rpm vs Oil Pressure plot"))
        
        with dpg.child_window(tag="Rpm & Oil Pressure graph", show=False):
            with dpg.plot(label="Rpm & Oil Pressure", height=800, width=dpg.get_viewport_width() - 250, crosshairs=True):
                    
                dpg.add_plot_legend()
        
                        
                dpg.add_plot_axis(dpg.mvXAxis, label="Time")
                dpg.add_plot_axis(dpg.mvYAxis, label="", tag="y_axis_rpm_and_oil")
                dpg.add_line_series(x=time, y=oil_p_scaled, label="Oil Pressure (Bar) X 1000", parent="y_axis_rpm_and_oil")
                dpg.add_line_series(x=time, y=rpm, label="RPM", parent="y_axis_rpm_and_oil")
        
        with dpg.child_window(tag="G-forces & Oil Pressure graph", show=False):
                            
            with dpg.plot(label="G-forces & Oil Pressure", height=800, width=dpg.get_viewport_width() - 250, crosshairs=True):
                            
                dpg.add_plot_legend()
                
                                
                dpg.add_plot_axis(dpg.mvXAxis, label="Time")
                dpg.add_plot_axis(dpg.mvYAxis, label="", tag="y_axis_Gforce_and_oil")
                dpg.add_line_series(x=time, y=oil_pressure, label="Oil Pressure (Bar)", parent="y_axis_Gforce_and_oil")
                dpg.add_line_series(x=time, y=long_g, label="longitudinal G (Forward/Backward)", parent="y_axis_Gforce_and_oil")
                dpg.add_line_series(x=time, y=lat_g, label="lateral G (Left/Right)", parent="y_axis_Gforce_and_oil")
        
        with dpg.child_window(tag="G-forces & Low Oil Pressure plot", show=False):
            with dpg.plot(label="G-forces & Low Oil Pressure Events", height=800, width=dpg.get_viewport_width() - 250, crosshairs=True):
                            
                dpg.add_plot_legend()
                
                                
                dpg.add_plot_axis(dpg.mvXAxis, label="<-- Turning Left (maybe)  / Turning Right (maybe) -->")
                dpg.add_plot_axis(dpg.mvYAxis, label="<-- Breaking / Accelerating -->", tag="y_axis_Gforce_low_oil")
                dpg.add_scatter_series(x=lat_g_low, y=lon_g_low, tag = "Oil Pressure Low", label="Oil Pressure Low", parent="y_axis_Gforce_low_oil")
                dpg.add_scatter_series(x=lat_g_normal, y=lon_g_normal, tag = "Oil Pressure Normal", label="Oil Pressure Normal", parent="y_axis_Gforce_low_oil")
                dpg.add_scatter_series(x=lat_g_high, y=lon_g_high, tag = "Oil Pressure High", label="Oil Pressure High", parent="y_axis_Gforce_low_oil")                        
        
        with dpg.child_window(tag="Rpm vs Oil Pressure plot", show=False):
            with dpg.plot(label="Rpm vs Oil Pressure", height=800, width=dpg.get_viewport_width() - 250, crosshairs=True):
                            
                dpg.add_plot_legend()
                
                                
                dpg.add_plot_axis(dpg.mvXAxis, label="RPM")
                dpg.add_plot_axis(dpg.mvYAxis, label="Oil Pressure", tag="y_axis_rpm_vs_oil")
                dpg.add_scatter_series(x=rpm, y=oil_pressure, label="Oil Pressure (Bar)", parent="y_axis_rpm_vs_oil")
                dpg.add_line_series(x=self.oil_operating_RPM, y=self.oil_operating_upper, label="Oil Pressure Upper Limit (Bar)", parent="y_axis_rpm_vs_oil")
                dpg.add_line_series(x=self.oil_operating_RPM, y=self.oil_operating_lower, label="Oil Pressure Lower Limit (Bar)", parent="y_axis_rpm_vs_oil")
        
                # RED - Low pressure
        with dpg.theme() as red_theme:
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_color(
                    dpg.mvPlotCol_MarkerFill,
                    (255, 0, 0, 255),
                    category=dpg.mvThemeCat_Plots
                )
                dpg.add_theme_color(
                    dpg.mvPlotCol_MarkerOutline,
                    (255, 0, 0, 255),
                    category=dpg.mvThemeCat_Plots
                )
        
                # GREEN - Normal pressure
        with dpg.theme() as green_theme:
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_color(
                        dpg.mvPlotCol_MarkerFill,
                        (0, 255, 0, 255),
                        category=dpg.mvThemeCat_Plots
                )
                dpg.add_theme_color(
                    dpg.mvPlotCol_MarkerOutline,
                    (0, 255, 0, 255),
                    category=dpg.mvThemeCat_Plots
                )
        
        # YELLOW - High pressure
        with dpg.theme() as yellow_theme:
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_color(
                    dpg.mvPlotCol_MarkerFill,
                    (143, 0, 255, 255),
                    category=dpg.mvThemeCat_Plots
                )
                dpg.add_theme_color(
                    dpg.mvPlotCol_MarkerOutline,
                    (143, 0, 255, 255),
                    category=dpg.mvThemeCat_Plots
                )
        
        dpg.bind_item_theme("Oil Pressure Low", red_theme)
        dpg.bind_item_theme("Oil Pressure Normal", green_theme)
        dpg.bind_item_theme("Oil Pressure High", yellow_theme)

        
