import dearpygui.dearpygui as dpg


class OilStarvationView:

    def __init__(self, DataManager):
            
        self.df = DataManager.df
        self.path = DataManager.path
        self.current_graph = None
        #TODO Change to dictionary
        self.oil_default_upper = [0,29,45,60,70,85,95,100,110,115]
        self.oil_default_lower = [0,10,14,14,30,60,70,75,75,75]
        self.oil_operating_upper = [0,29,45,60,70,85,95,100,110,115]
        self.oil_operating_lower = [0,10,14,14,30,60,70,75,75,75]
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

    def reset_oil_graphs(self):
        
        self.classify_oil_values()
        dpg.set_value("rpm vs oil upper", [self.oil_operating_RPM, self.oil_operating_upper])
        dpg.set_value("rpm vs oil lower", [self.oil_operating_RPM, self.oil_operating_lower])
        dpg.set_value("Oil Pressure Low", [self.lat_g_low, self.lon_g_low])
        dpg.set_value("Oil Pressure Normal", [self.lat_g_normal, self.lon_g_normal])
        dpg.set_value("Oil Pressure High", [self.lat_g_high, self.lon_g_high])
        dpg.set_value("Oil Upper Limit Timed", [self.time, self.oil_upper_timed])
        dpg.set_value("Oil Lower Limit Timed", [self.time, self.oil_lower_timed])
        dpg.set_value("Excess Oil Pressure", [self.time, self.pressure_excess])
        dpg.configure_item("Excess Oil Pressure", label=f"Excess Oil Pressure ({self.avg_excess:.1f})")
        dpg.configure_item("Oil Pressure Low", label=f"Oil Pressure Low ({self.low_percent:.1f}%)")
        dpg.configure_item("Oil Pressure Normal", label=f"Oil Pressure Normal ({self.normal_percent:.1f}%)")
        dpg.configure_item("Oil Pressure High", label=f"Oil Pressure High ({self.high_percent:.1f}%)")



    def reset_oil_ranges(self):
        self.oil_operating_lower = self.oil_default_lower.copy()
        self.oil_operating_upper = self.oil_default_upper.copy()
        for i in range(len(self.oil_default_lower)):

            dpg.set_value(
                f"lower_{i}",
                self.oil_default_lower[i]
            )

            dpg.set_value(
                f"upper_{i}",
                self.oil_default_upper[i]
            )
        self.reset_oil_graphs()
       
    def update_graphs(self):

        for i in range(len(self.oil_operating_RPM)):
            self.oil_operating_lower[i] = dpg.get_value(f'lower_{i}')
            self.oil_operating_upper[i] = dpg.get_value(f'upper_{i}')
        self.reset_oil_graphs()
        
    def classify_oil_values(self):
        self.oil_upper_timed = []
        self.oil_lower_timed = []
        self.lat_g_low = []
        self.lon_g_low = []
        self.lat_g_normal = []
        self.lon_g_normal = []
        self.lat_g_high = []
        self.lon_g_high = []
        self.pressure_excess = []

        for i in range(len(self.time)):
            for j in range(len(self.oil_operating_RPM)):
                if self.rpm[i] >= self.oil_operating_RPM[j]:
                    rpm_index = j
                else:
                    break
            self.oil_upper_timed.append(self.oil_operating_upper[rpm_index] * 100)
            self.oil_lower_timed.append(self.oil_operating_lower[rpm_index] * 100)
        
        for i in range(len(self.lat_g)):
        
            for j in range(len(self.oil_operating_RPM)):
                          
                if round(self.rpm[i],-3) <= self.oil_operating_RPM[j]:
        
                    if self.oil_pressure[i] < self.oil_operating_lower[j]:
                        self.lat_g_low.append(self.lat_g[i])
                        self.lon_g_low.append(self.long_g[i])
                    elif self.oil_pressure[i] > self.oil_operating_upper[j]:
                        self.lat_g_high.append(self.lat_g[i])
                        self.lon_g_high.append(self.long_g[i])
                    else:
                        self.lat_g_normal.append(self.lat_g[i])
                        self.lon_g_normal.append(self.long_g[i])
        
                    break
        self.low_percent = len(self.lat_g_low)/len(self.lat_g)*100
        self.normal_percent = len(self.lat_g_normal)/len(self.lat_g)*100
        self.high_percent = len(self.lat_g_high)/len(self.lat_g)*100

        for i in range(len(self.time)):
            self.pressure_excess.append(self.oil_p_scaled[i] - (self.oil_lower_timed[i] + self.oil_upper_timed[i]) / 2 )

        self.avg_excess = (sum(self.pressure_excess) / len(self.pressure_excess) / 100 )

    def refresh(self):
        """Called after new data loads to update content."""

        if dpg.does_item_exist("oil_starvation_placeholder"):
            dpg.delete_item("oil_starvation_placeholder")
        

        self.time = self.df["Time"].tolist()
        self.rpm = self.df["ECU RPM"].tolist()
        self.oil_pressure = (self.df["ECU OIL P"] * 14.504).tolist()
        self.oil_p_scaled = (self.df["ECU OIL P"] * 14.504 * 100).tolist()
        self.lat_g = self.df["GPS LatAcc"].tolist()
        self.lat_g_scaled = (self.df["GPS LatAcc"] * 10).tolist()
        self.long_g_scaled = (self.df["GPS LonAcc"] * 10).tolist()
        self.long_g = self.df["GPS LonAcc"].tolist()
        self.rad_temp = (self.df["ECU ECT"] * 100).tolist()
        self.classify_oil_values()
                                 
                                  
        
        with dpg.menu_bar(tag="Oil Starvation Menu Bar"):
            dpg.add_menu_item(label="Rpm & Oil Pressure", callback=lambda:self.show_graph("Rpm & Oil Pressure graph"))
            dpg.add_menu_item(label="G-forces & Oil Pressure", callback=lambda:self.show_graph("G-forces & Oil Pressure graph"))
            dpg.add_menu_item(label="G-forces & Low Oil Pressure Events", callback=lambda:self.show_graph("G-forces & Low Oil Pressure plot"))
            dpg.add_menu_item(label="Rpm vs Oil Pressure", callback=lambda:self.show_graph("Rpm vs Oil Pressure plot"))

            with dpg.menu(tag="Change Safe Pressure Range", label="Change Safe Pressure Range"):  
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Update", callback=lambda: self.update_graphs(), width = 250)
                    dpg.add_button(label="Reset", callback=lambda: self.reset_oil_ranges(), width = 250)

                for i in range(len(self.oil_operating_RPM)):

                    dpg.add_text(f"{self.oil_operating_RPM[i]} RPM")

                    with dpg.group(horizontal=True):
                        dpg.add_input_float(
                            tag = f"lower_{i}",
                            label = "Lower",
                            default_value = self.oil_operating_lower[i],
                            step = 1.0
                        )

                        dpg.add_input_float(
                            tag = f"upper_{i}",
                            label = "Upper",
                            default_value = self.oil_operating_upper[i],
                            step = 1.0
                        )

                    dpg.add_separator()

                
        
        with dpg.child_window(tag="Rpm & Oil Pressure graph", show=False):
            with dpg.plot(label="Rpm & Oil Pressure", height=800, width=dpg.get_viewport_width() - 250, crosshairs=True):
                    
                dpg.add_plot_legend()
        
                        
                dpg.add_plot_axis(dpg.mvXAxis, label="Time")
                dpg.add_plot_axis(dpg.mvYAxis, label="", tag="y_axis_rpm_and_oil")
                dpg.add_line_series(x=self.time, y=self.oil_p_scaled, label="Oil Pressure (PSI) X 100", parent="y_axis_rpm_and_oil")
                dpg.add_line_series(x=self.time, y=self.rpm, label="RPM", parent="y_axis_rpm_and_oil")
                dpg.add_line_series(x=self.time, y=self.oil_upper_timed, tag = "Oil Upper Limit Timed", label="Oil Pressure Upper Limit", parent="y_axis_rpm_and_oil")
                dpg.add_line_series(x=self.time, y=self.oil_lower_timed, tag = "Oil Lower Limit Timed", label="Oil Pressure Lower Limit", parent="y_axis_rpm_and_oil")
                dpg.add_line_series(x=self.time, y=self.pressure_excess, tag = "Excess Oil Pressure", label=f"Excess Oil Pressure ({self.avg_excess:.1f})", parent="y_axis_rpm_and_oil")
                dpg.add_line_series(x=self.time, y=self.rad_temp, label="Temp (C) X 100", parent="y_axis_rpm_and_oil")
                
        with dpg.child_window(tag="G-forces & Oil Pressure graph", show=False):
                            
            with dpg.plot(label="G-forces & Oil Pressure", height=800, width=dpg.get_viewport_width() - 250, crosshairs=True):
                            
                dpg.add_plot_legend()
                
                                
                dpg.add_plot_axis(dpg.mvXAxis, label="Time")
                dpg.add_plot_axis(dpg.mvYAxis, label="", tag="y_axis_Gforce_and_oil")
                dpg.add_line_series(x=self.time, y=self.oil_pressure, label="Oil Pressure (PSI)", parent="y_axis_Gforce_and_oil")
                dpg.add_line_series(x=self.time, y=self.long_g_scaled, label="longitudinal G (Forward/Backward) X 10", parent="y_axis_Gforce_and_oil")
                dpg.add_line_series(x=self.time, y=self.lat_g_scaled, label="lateral G (Left/Right) X 10", parent="y_axis_Gforce_and_oil")
        
        with dpg.child_window(tag="G-forces & Low Oil Pressure plot", show=False):
            with dpg.plot(label="G-forces & Low Oil Pressure Events", height=800, width=dpg.get_viewport_width() - 250, crosshairs=True):
                            
                dpg.add_plot_legend()
                
                                
                dpg.add_plot_axis(dpg.mvXAxis, label="<-- Turning Right  / Turning Left -->")
                dpg.add_plot_axis(dpg.mvYAxis, label="<-- Breaking / Accelerating -->", tag="y_axis_Gforce_low_oil")

                dpg.add_scatter_series(x=self.lat_g_low,
                                       y=self.lon_g_low, 
                                       tag = "Oil Pressure Low", 
                                       label=f"Oil Pressure Low ({self.low_percent:.1f}%)", 
                                       parent="y_axis_Gforce_low_oil"
                                       )
                
                dpg.add_scatter_series(x=self.lat_g_normal, 
                                       y=self.lon_g_normal, 
                                       tag = "Oil Pressure Normal", 
                                       label=f"Oil Pressure Normal ({self.normal_percent:.1f}%)", 
                                       parent="y_axis_Gforce_low_oil"
                                       )
                
                dpg.add_scatter_series(x=self.lat_g_high, 
                                       y=self.lon_g_high, 
                                       tag = "Oil Pressure High", 
                                       label=f"Oil Pressure High ({self.high_percent:.1f}%)", 
                                       parent="y_axis_Gforce_low_oil"
                                       )             
                   
        
        with dpg.child_window(tag="Rpm vs Oil Pressure plot", show=False):
            with dpg.plot(label="Rpm vs Oil Pressure", height=800, width=dpg.get_viewport_width() - 250, crosshairs=True):
                            
                dpg.add_plot_legend()
                
                                
                dpg.add_plot_axis(dpg.mvXAxis, label="RPM")
                dpg.add_plot_axis(dpg.mvYAxis, label="Oil Pressure", tag="y_axis_rpm_vs_oil")
                dpg.add_scatter_series(x=self.rpm, y=self.oil_pressure, label="Oil Pressure (PSI)", parent="y_axis_rpm_vs_oil")

                dpg.add_line_series(x=self.oil_operating_RPM,
                                    y=self.oil_operating_upper, 
                                    tag="rpm vs oil upper",
                                    label="Oil Pressure Upper Limit (PSI)", 
                                    parent="y_axis_rpm_vs_oil"
                                    )
                
                dpg.add_line_series(x=self.oil_operating_RPM, 
                                    y=self.oil_operating_lower, 
                                    tag="rpm vs oil lower",
                                    label="Oil Pressure Lower Limit (PSI)", 
                                    parent="y_axis_rpm_vs_oil"
                                    )
        
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

        
