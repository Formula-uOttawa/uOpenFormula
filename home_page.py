# GUI and backend code for the homepage.

import dearpygui.dearpygui as dpg
import tkinter as tk
from data_manager import DataManager

class HomePage:
    
    file_path = ""
    df = None
    metadata = None
    importer = DataManager()
    
    def __init__(self):
        self.show_home_page()
    
    def show_error_modal(self, tag, message):
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
        with dpg.window(label="Error", modal=True, tag=tag, no_title_bar=True, pos=[200, 200]):
            dpg.add_text(message)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            dpg.add_button(label="OK", width=75, callback=lambda: dpg.delete_item(tag))
    
    def render_gg_diagram(self, graph_name):
        if self.df is None:
            self.show_error_modal("gg_error_modal", "Please load a project before generating a GG Diagram.")
            return
        
        column_options = [
            ("GPS LonAcc", "GPS LatAcc"),
            ("LateralAcc", "VerticalAcc"),
        ]
        selected_pair = None
        for x_col, y_col in column_options:
            if x_col in self.df.columns and y_col in self.df.columns:
                selected_pair = (x_col, y_col)
                break
        
        if selected_pair is None:
            self.show_error_modal(
                "gg_error_modal",
                "Missing GG columns. Expected either GPS LonAcc/GPS LatAcc or LateralAcc/VerticalAcc.",
            )
            return
        
        x_col, y_col = selected_pair
        gg_df = self.df[[x_col, y_col]].dropna()
        if gg_df.empty:
            self.show_error_modal("gg_error_modal", "No valid GPS acceleration points found for GG Diagram.")
            return
        
        x_vals = gg_df[x_col].tolist()
        y_vals = gg_df[y_col].tolist()
        limit = 3.5
        
        window_tag = f"gg_diagram_{graph_name}".replace(" ", "_")
        if dpg.does_item_exist(window_tag):
            dpg.delete_item(window_tag)
        
        with dpg.window(label=f"GG Diagram - {graph_name}", tag=window_tag, width=800, height=700):
            with dpg.plot(label="GG Diagram", height=-1, width=-1):
                dpg.add_plot_legend()
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label=x_col)
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label=y_col)
                dpg.add_scatter_series(x_vals, y_vals, label="Acceleration Points", parent=y_axis)
                dpg.add_line_series([-limit, limit], [0, 0], label="LatAcc = 0", parent=y_axis)
                dpg.add_line_series([0, 0], [-limit, limit], label="LonAcc = 0", parent=y_axis)
                dpg.set_axis_limits(x_axis, -limit, limit)
                dpg.set_axis_limits(y_axis, -limit, limit)
    
    def select_file(self):
        """
        Called automatically when the user picks a file in the file dialog.
        """
        
        self.importer.select_file()
        
        # This runs load() + validations and returns the DataFrame
        self.df = self.importer.import_and_validate()
        
        self.metadata = [f"{k}: {v}" for k, v in self.importer.metadata.items() if v]
        
        dpg.delete_item("Home Window", children_only=True)
        
        self.show_windows()
        
        # The data preview window
        with dpg.window(label="Raw Data",width=800,height=500,no_close=True):
            data_array = self.df.to_numpy()
            with dpg.table(header_row=True,
                           policy=dpg.mvTable_SizingFixedFit,
                           resizable=True,
                           scrollX=True, scrollY=True,
                           borders_innerH=True, borders_outerH=True,
                           borders_innerV=True, borders_outerV=True):
                for col in self.df.columns:
                    dpg.add_table_column(label=str(col))
                    
                # Add Rows and Cells
                for i in range(self.df.shape[0]):
                    with dpg.table_row():
                        for j in range(self.df.shape[1]):
                            # Each cell is of type selectable, can also be text or input_text
                            dpg.add_selectable(label=str(data_array[i, j]),
                                               callback=lambda:None)
        
        #     dpg.set_value("metadata_box", "\n".join(meta_lines))
        #     preview_text = df.to_string()
        #     dpg.set_value("preview", preview_text)

        # except Exception as e:
            # If anything failed, show the error and clear preview
            # TODO: create metadata and data preview box
            # dpg.set_value("preview", "")
            # dpg.set_value("metadata_box", "")
            # pass
    
    def show_windows(self):
        # List of windows that should be swappable
        SWAPPABLE_WINDOWS = ["aero_window", "electronics_window"]

        def switch_view(sender, app_data, user_data):
            """Hides all windows, then shows the one passed in user_data."""
            for win in SWAPPABLE_WINDOWS:
                if win == user_data:
                    dpg.configure_item(win, show=True)
                else:
                    dpg.configure_item(win, show=False)

        # --- Navigation Menu ---
        with dpg.window(label="Menu",
                        pos=[0, 0],
                        width=200,
                        height=dpg.get_viewport_height(),
                        no_close=True,
                        no_move=True,
                        no_collapse=True):
            dpg.add_text("Dashboard Navigation")
            dpg.add_separator()
            # Pass the target window tag as user_data
            dpg.add_button(label="Aero Data",
                           user_data="aero_window",
                           callback=switch_view,
                           width=-1)
            dpg.add_button(label="Electronics",
                           user_data="electronics_window",
                           callback=switch_view,
                           width=-1)

        # --- View 1: Aerodynamics (Shown by default) ---
        with dpg.window(label="Aero Data View",
                        tag="aero_window", pos=[200, 0],
                        width=dpg.get_viewport_width(),
                        height=dpg.get_viewport_height(),
                        no_close=True,
                        no_move=True,
                        no_resize=True,
                        no_collapse=True,
                        show=True):
            dpg.add_text("Real-time aerodynamic load data would go here.")
            # Add your plots and readouts here

        # --- View 2: Electronics (Hidden by default) ---
        with dpg.window(label="Electronics View",
                        tag="electronics_window",
                        pos=[200, 0],
                        width=dpg.get_viewport_width(),
                        height=dpg.get_viewport_height(),
                        no_close=True,
                        no_move=True,
                        no_resize=True,
                        no_collapse=True,
                        show=False):
            dpg.add_text("Battery voltage and wiring harness diagnostics would go here.")
            # Add your electrical gauges here
    
    def load_texture(self, file_path):
        w, h, channels, data = dpg.load_image(file_path)
        with dpg.texture_registry():
            texture = dpg.add_static_texture(w, h, data)
        return (texture)
    
    def show_home_page(self):
        
        dpg.create_context()
        
        # Load font
        with dpg.font_registry():
            try:
                font_path = ("C:/Windows/Fonts/segoeui.ttf")  # will fail on non-Windows
                segoe = dpg.add_font(font_path, 18)
                dpg.bind_font(segoe)  # only runs if add_font worked
            except Exception:
                pass

        # Set theme
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10.0)
        dpg.bind_theme(global_theme)
        
        # Create main viewport
        dpg.create_viewport(title='Formula uOttawa Telemetry Software', width=800, height=600)
        
        # Add and populate menu bar at the top
        with dpg.viewport_menu_bar(tag="Main Menu Bar"):  # TODO: revisions to menu bar
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Save Project", callback=lambda: None)
                dpg.add_menu_item(label="Load Project", callback=lambda: self.select_file())
                
            with dpg.menu(label="Graph"):
                dpg.add_menu_item(label="Make New Graph", callback=lambda: self.make_graph_window(400, 150, 450, 770))
            
            with dpg.menu(label="Filter"):
                dpg.add_menu_item(label="Low-pass", callback=lambda: None)
                dpg.add_menu_item(label="High-pass", callback=lambda: None)
                dpg.add_menu_item(label="Band-pass", callback=lambda: None)
            
            with dpg.menu(label="Trim"):
                pass
            
            with dpg.menu(label="Correlation"):
                dpg.add_menu_item(label="Linear", callback=lambda: None)
            
        # Create the main window.
        with dpg.window(tag="Home Window", no_move=True, no_resize=True, pos=(0, 0)):
            
            # This table houses the logo, new project, and load project buttons at the start of the program.
            with dpg.table(header_row=False,
                            policy=dpg.mvTable_SizingFixedFit,
                            no_host_extendX=True,                
                            borders_innerV=False,
                            borders_innerH=False,
                            borders_outerV=False,
                            borders_outerH=False):
                dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=0.0)
                dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)
                
                with dpg.table_row():
                    dpg.add_spacer(height=150)
                
                with dpg.table_row():
                    dpg.add_spacer()
                    dpg.add_image(self.load_texture("Assets/formula_logo.png"), height=150, width=699)
                
                with dpg.table_row():
                    dpg.add_spacer(height=150)
                
                with dpg.table_row():
                    dpg.add_spacer()
                    with dpg.group(horizontal=True, horizontal_spacing=4):
                        dpg.add_spacer(width=63) # TODO: ask Harsh about this
                        
                        with dpg.group():
                            with dpg.group(horizontal=True):
                                dpg.add_spacer(width=80)
                                dpg.add_text("New Project")

                            dpg.add_image_button(self.load_texture("Assets/plus.png"),
                                                 background_color=(0,0,0,70),
                                                 frame_padding=0,
                                                 width=250,
                                                 height=250,
                                                 callback=lambda:None)

                        dpg.add_spacer(width=60)

                        with dpg.group():

                            with dpg.group(horizontal=True):
                                dpg.add_spacer(width=82)
                                dpg.add_text("Load Project")
                            dpg.add_image_button(self.load_texture("Assets/file_icon.png"),
                                                 background_color=(0,0,0,70),
                                                 frame_padding=0,
                                                 width=250,
                                                 height=250,
                                                 callback=lambda: self.select_file())
                        dpg.add_spacer(width=63)

                with dpg.table_row():
                    dpg.add_spacer(height=97)

                with dpg.table_row():
                    dpg.add_text(default_value="Version: Pre-alpha", color=[255, 255, 255, 120])

            dpg.set_primary_window("Home Window", True)
            dpg.set_viewport_large_icon("Assets/Formula_uottawa.ico")
            dpg.setup_dearpygui()
            dpg.set_viewport_pos([0, 0])
            dpg.show_viewport(maximized=True)  # prevents window sizing and positioning from failing on initial creation
            dpg.start_dearpygui()
            dpg.destroy_context()

    # TODO: This should be private 
    def graph_type_check(self, user_data):
        """Checks if graph type and filter type are choosen and compatiable.


        Args:
            user_date (tuple): Expected Values:
                - "name" (str): name of the graph.
                - "file_path" (str): file path of csv containing data.
                - "graph_type" (combo widget): the menu widget for types of graphs.
                - "filter_type" (combo widget): the menu widget for types of filters.


        Returns:
            None, Calls make_graph function.
        """

        valid_graph_filter_pairs = {"Line Graph": ["High-Pass", "Low-Pass", "Band-Pass", "None"],
                                    "Bar Chart": ["None"],
                                    "Histogram": ["None"],
                                    "Scatter Plot": ["High-Pass", "Low-Pass", "Band-Pass", "None"],
                                    "Pie Chart": ["None"],
                                    "Heat Map": ["High-Pass", "Low-Pass", "Band-Pass", "None"],
                                    "GG Diagram": ["None"]
                                    }

        name, file_path, graph_type, filter_type = user_data
        graph_type = dpg.get_value(graph_type)
        filter_type = dpg.get_value(filter_type)

        if (graph_type not in list(valid_graph_filter_pairs.keys()) or filter_type not in valid_graph_filter_pairs[graph_type]):

            if not dpg.does_item_exist("ask_graph"):

                with dpg.window(label="Type of Graph", modal=True, tag="ask_graph", no_title_bar=True, pos=[200, 200]):

                    dpg.add_text("Please Reselect The Type of Graph!")
                    dpg.add_separator()
                    dpg.add_spacer(height=5)
                    graph_type = dpg.add_combo(["Line Graph", "Bar Chart", "Histogram", "Scatter Plot", "Pie Chart", "Heat Map", "GG Diagram"],
                                            default_value="Choose Type of Graph")

                    filter_type = dpg.add_combo(["High-Pass", "Low-Pass", "Band-Pass", "None"],
                                                default_value="Choose Type of Filter")

                    dpg.add_spacer(height=5)
                    dpg.add_button(label="OK", width=75, callback=lambda: self.graph_type_check((name, file_path, graph_type, filter_type)))

        else:

            if dpg.does_item_exist("ask_graph"):
                dpg.delete_item("ask_graph")
            dpg.split_frame()  # force Dpg to generate a frame and load new widget states, close modal before making graph
            if graph_type == "GG Diagram":
                self.render_gg_diagram(name)
            else:
                self.show_error_modal("graph_not_implemented_modal", f"{graph_type} is not implemented yet.")


    def name_check(self, sender, app_data, user_data):
        """Verifiy the user entered a name.


        Args:
            sender (Not Used):
            app_data (Not Used):
            user_data (tuple): Expected Values:
                - "name" (input text widget): widget containing current name user entered.
                - "file_path" (input text widget): widget containing current chosen file path.
                - "graph_type" (combo widget): the menu widget for types of graphs.
                - "filter_type" (combo widget): the menu widget for types of filters.


        Returns:
            None, Calls file_path_check function.
        """

        name, file_path, graph_type, filter_type = user_data
        name = dpg.get_value(name)

        if (name == ""):

            if not dpg.does_item_exist("ask_name"):

                with dpg.window(label="Name", modal=True, tag="ask_name", no_title_bar=True, pos=[200, 200]):

                    dpg.add_text("Please Enter A Name For The Graph!")
                    dpg.add_separator()
                    dpg.add_spacer(height=5)
                    name_input = dpg.add_input_text(hint="Enter Graph Name", width=300)
                    dpg.add_spacer(height=5)
                    dpg.add_button(label="OK", width=75, callback=lambda: self.name_check(None, None, (name_input, file_path, graph_type, filter_type)))

        else:

            if dpg.does_item_exist("ask_name"):
                dpg.delete_item("ask_name")
            dpg.split_frame()  # force Dpg to generate a frame and load new widget states, prevents multiple modals
            self.graph_type_check((name, file_path, graph_type, filter_type))


    def make_graph_window(self, x_pos, y_pos, ht, wd):
        """Create a window for graph selection menu.


        Args:
            x_pos (int): x position wanted for the window.
            y_pos (int): y position wanted for the window.
            ht (int): height wanted for the window.
            wd (int): width wanted for the window.


        Returns:
            None, Creates a new window.
        """

        with dpg.window(pos=(x_pos, y_pos), height=ht, width=wd):

            with dpg.table(header_row=False,
                        policy=dpg.mvTable_SizingFixedFit,
                        no_host_extendX=True,                
                        borders_innerV=False,                   # set everything below to True to see table lines
                        borders_innerH=False,
                        borders_outerV=False,
                        borders_outerH=False,
                        ):

                dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=0.0)
                dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)
                # middle column width is fixed, side columns are variable and will fill remaning space, keeping middle column centered

                for r in range(9):

                    with dpg.table_row():
                        dpg.add_spacer()

                        if r == 3:

                            with dpg.group():  # allows vertical stacking of widgets within one cell

                                path_display = dpg.add_input_text(hint="Selected File Path", readonly=True, width=300)
                                file_path = dpg.add_button(label="Choose File", callback=lambda: None)

                        elif r == 1:

                            graph_name = dpg.add_input_text(hint="Enter Graph Name", width=300)

                        elif r == 5:

                            graph_type = dpg.add_combo(
                                ["Line Graph", "Bar Chart", "Histogram", "Scatter Plot", "Pie Chart", "Heat Map", "GG Diagram"],
                                default_value="Choose Type of Graph",
                            )

                        elif (r == 7):

                            filter_type = dpg.add_combo(
                                ["High-Pass", "Low-Pass", "Band-Pass", "None"],
                                default_value="Choose Type of Filter",
                            )
                            dpg.add_button(label="Submit", callback=self.name_check, user_data=(graph_name, path_display, graph_type, filter_type))

                        else:

                            dpg.add_spacer(height=(ht - 150) / 6)  # vertical spacing between the rows that include widgets
