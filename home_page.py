import dearpygui.dearpygui as dpg
from data_manager import DataManager
from data_visualization import DataVisualization

class HomePage:
    
    def __init__(self):
        self.importer = DataManager()
        self.df = None
        self.metadata = None
        self.visualizer = None
        self.show_home_page()
    
    def select_file(self):
        """Open file dialog, load and validate CSV, then refresh the UI."""
        self.importer.select_file()
        self.df = self.importer.import_and_validate()
        self.metadata = [f"{k}: {v}" for k, v in self.importer.metadata.items() if v]
        self.visualizer = DataVisualization(self.importer)

        dpg.delete_item("Home Window", children_only=True)
        self.show_windows()

        # Raw data preview window
        with dpg.window(label="Raw Data", width=800, height=500, no_close=True):
            data_array = self.df.to_numpy()
            with dpg.table(
                header_row=True,
                policy=dpg.mvTable_SizingFixedFit,
                resizable=True,
                scrollX=True, scrollY=True,
                borders_innerH=True, borders_outerH=True,
                borders_innerV=True, borders_outerV=True,
            ):
                for col in self.df.columns:
                    dpg.add_table_column(label=str(col))
                for i in range(self.df.shape[0]):
                    with dpg.table_row():
                        for j in range(self.df.shape[1]):
                            dpg.add_selectable(
                                label=str(data_array[i, j]),
                                callback=lambda: None,
                            )
    
    def save_graph_screenshot(self):
        """Save the current plot to disk via Matplotlib (high-quality offscreen render)."""
        if self.visualizer is None:
            if not dpg.does_item_exist("no_data_modal"):
                with dpg.window(label="No Data", modal=True,
                                tag="no_data_modal", no_title_bar=True, pos=[200, 200]):
                    dpg.add_text("Please load a file before saving a graph.")
                    dpg.add_spacer(height=5)
                    dpg.add_button(
                        label="OK", width=75,
                        callback=lambda: dpg.delete_item("no_data_modal"),
                    )
            return
        self.visualizer.save_matplotlib()
    
    def show_windows(self):
        """Build the navigation sidebar and the main view windows after data is loaded."""
        SWAPPABLE_WINDOWS = ["aero_window", "electronics_window"]

        def switch_view(sender, app_data, user_data):
            for win in SWAPPABLE_WINDOWS:
                dpg.configure_item(win, show=(win == user_data))

        # Sidebar navigation
        with dpg.window(
            label="Menu", pos=[0, 0],
            width=200, height=dpg.get_viewport_height(),
            no_close=True, no_move=True, no_collapse=True,
        ):
            dpg.add_text("Dashboard Navigation")
            dpg.add_separator()
            dpg.add_button(label="Aero Data",
                           user_data="aero_window", callback=switch_view, width=-1)
            dpg.add_button(label="Electronics",
                           user_data="electronics_window", callback=switch_view, width=-1)

        # Aero view
        with dpg.window(
            label="Aero Data View", tag="aero_window",
            pos=[200, 0],
            width=dpg.get_viewport_width() - 200,
            height=dpg.get_viewport_height(),
            no_close=True, no_move=True, no_resize=True, no_collapse=True,
            show=True,
        ):
            aero_group = dpg.add_group(tag="aero_plot_group")
            if self.visualizer is not None:
                # Render all channels except Time by default
                y_cols = list(self.importer.df_excl_time.columns)
                self.visualizer.render_dpg_plot(
                    parent_tag="aero_plot_group",
                    x_col="Time",
                    y_cols=y_cols,
                )
            else:
                dpg.add_text("Load a file to view data.", parent=aero_group)

        # Electronics view
        with dpg.window(
            label="Electronics View", tag="electronics_window",
            pos=[200, 0],
            width=dpg.get_viewport_width() - 200,
            height=dpg.get_viewport_height(),
            no_close=True, no_move=True, no_resize=True, no_collapse=True,
            show=False,
        ):
            elec_group = dpg.add_group(tag="electronics_plot_group")
            dpg.add_text("Select specific channels to display here.", parent=elec_group)
    
    def graph_type_check(self, user_data):
        """Validate graph/filter combination, then trigger plot creation."""
        valid_graph_filter_pairs = {
            "Line Graph":   ["High-Pass", "Low-Pass", "Band-Pass", "None"],
            "Bar Chart":    ["None"],
            "Histogram":    ["None"],
            "Scatter Plot": ["High-Pass", "Low-Pass", "Band-Pass", "None"],
            "Pie Chart":    ["None"],
            "Heat Map":     ["High-Pass", "Low-Pass", "Band-Pass", "None"],
        }

        name, file_path, graph_type_widget, filter_type_widget = user_data
        graph_type = dpg.get_value(graph_type_widget)
        filter_type = dpg.get_value(filter_type_widget)

        valid = (
            graph_type in valid_graph_filter_pairs
            and filter_type in valid_graph_filter_pairs[graph_type]
        )

        if not valid:
            if not dpg.does_item_exist("ask_graph"):
                with dpg.window(label="Type of Graph", modal=True,
                                tag="ask_graph", no_title_bar=True, pos=[200, 200]):
                    dpg.add_text("Please reselect the type of graph.")
                    dpg.add_separator()
                    dpg.add_spacer(height=5)
                    graph_type_widget = dpg.add_combo(
                        list(valid_graph_filter_pairs.keys()),
                        default_value="Choose Type of Graph",
                    )
                    filter_type_widget = dpg.add_combo(
                        ["High-Pass", "Low-Pass", "Band-Pass", "None"],
                        default_value="Choose Type of Filter",
                    )
                    dpg.add_spacer(height=5)
                    dpg.add_button(
                        label="OK", width=75,
                        callback=lambda: self.graph_type_check(
                            (name, file_path, graph_type_widget, filter_type_widget)
                        ),
                    )
        else:
            dpg.delete_item("ask_graph")
            dpg.split_frame()
            self._create_graph(name, filter_type)
    
    def _create_graph(self, name, filter_type):
        """Create a new floating graph window using DataVisualization.
        
        Args:
            name (str): Title for the graph window.
            filter_type (str): Selected filter to apply.
        """
        if self.visualizer is None or self.df is None:
            return
        
        win_tag = f"graph_window_{name}"
        if dpg.does_item_exist(win_tag):
            dpg.delete_item(win_tag)

        with dpg.window(label=name, tag=win_tag, width=700, height=450):
            group_tag = f"graph_group_{name}"
            dpg.add_group(tag=group_tag)
            y_cols = list(self.importer.df_excl_time.columns)
            self.visualizer.render_dpg_plot(
                parent_tag=group_tag,
                x_col="Time",
                y_cols=y_cols,
                filter_type=filter_type,
            )
    
    def name_check(self, sender, app_data, user_data):
        """Verify a graph name was entered before proceeding."""
        name_widget, file_path, graph_type, filter_type = user_data
        name = dpg.get_value(name_widget)

        if name == "":
            if not dpg.does_item_exist("ask_name"):
                with dpg.window(label="Name", modal=True,
                                tag="ask_name", no_title_bar=True, pos=[200, 200]):
                    dpg.add_text("Please enter a name for the graph.")
                    dpg.add_separator()
                    dpg.add_spacer(height=5)
                    name_input = dpg.add_input_text(hint="Enter Graph Name", width=300)
                    dpg.add_spacer(height=5)
                    dpg.add_button(
                        label="OK", width=75,
                        callback=lambda: self.name_check(
                            None, None,
                            (name_input, file_path, graph_type, filter_type),
                        ),
                    )
        else:
            dpg.delete_item("ask_name")
            dpg.split_frame()
            self.graph_type_check((name_widget, file_path, graph_type, filter_type))
    
    def make_graph_window(self, x_pos, y_pos, ht, wd):
        """Open the graph configuration panel."""
        with dpg.window(pos=(x_pos, y_pos), height=ht, width=wd):
            with dpg.table(
                header_row=False,
                policy=dpg.mvTable_SizingFixedFit,
                no_host_extendX=True,
                borders_innerV=False, borders_innerH=False,
                borders_outerV=False, borders_outerH=False,
            ):
                dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=0.0)
                dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)

                for r in range(9):
                    with dpg.table_row():
                        dpg.add_spacer()

                        if r == 1:
                            graph_name = dpg.add_input_text(
                                hint="Enter Graph Name", width=300)
                        elif r == 3:
                            with dpg.group():
                                path_display = dpg.add_input_text(
                                    hint="Selected File Path", readonly=True, width=300)
                                # File path is now managed by HomePage.select_file()
                                dpg.add_button(
                                    label="Load File",
                                    callback=lambda: self.select_file(),
                                )
                                
                        elif r == 5:
                            graph_type = dpg.add_combo(
                                ["Line Graph", "Bar Chart", "Histogram",
                                 "Scatter Plot", "Pie Chart", "Heat Map"],
                                default_value="Choose Type of Graph",
                            )
                        elif r == 7:
                            filter_type = dpg.add_combo(
                                ["High-Pass", "Low-Pass", "Band-Pass", "None"],
                                default_value="Choose Type of Filter",
                            )
                            dpg.add_button(
                                label="Submit",
                                callback=self.name_check,
                                user_data=(graph_name, path_display,
                                           graph_type, filter_type),
                            )
                        else:
                            dpg.add_spacer(height=(ht - 150) / 6)
    
    def load_texture(self, file_path):
        w, h, channels, data = dpg.load_image(file_path)
        with dpg.texture_registry():
            texture = dpg.add_static_texture(w, h, data)
        return (texture)
    
    def show_home_page(self):
        dpg.create_context()
        
        # with dpg.font_registry():
        #     try:
        #         segoe = dpg.add_font("C:/Windows/Fonts/segoeui.ttf", 18)
        #         dpg.bind_font(segoe)
        #     except Exception:
        #         pass
        
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10.0)
        dpg.bind_theme(global_theme)
        
        dpg.create_viewport(
            title='Formula uOttawa Telemetry Software', width=800, height=600)
        
        with dpg.viewport_menu_bar(tag="Main Menu Bar"):  # TODO: revisions to menu bar
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Save Project", callback=lambda: None)
                dpg.add_menu_item(label="Load Project",
                                  callback=lambda: self.select_file())
                
            with dpg.menu(label="Graph"):
                dpg.add_menu_item(
                    label="Make New Graph",
                    callback=lambda: self.make_graph_window(400, 150, 450, 770))
                dpg.add_menu_item(
                    label="Save Graph",
                    callback=lambda: self.save_graph_screenshot(),
                )
            
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
                            borders_innerV=False, borders_innerH=False,
                            borders_outerV=False, borders_outerH=False,):
                dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=0.0)
                dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)
                
                with dpg.table_row():
                    dpg.add_spacer(height=150)
                
                with dpg.table_row():
                    dpg.add_spacer()
                    dpg.add_image(self.load_texture("Assets/formula_logo.png"),
                                  height=150, width=699)
                
                with dpg.table_row():
                    dpg.add_spacer(height=150)
                
                with dpg.table_row():
                    dpg.add_spacer()
                    with dpg.group(horizontal=True, horizontal_spacing=4):
                        dpg.add_spacer(width=63)
                        
                        with dpg.group():
                            with dpg.group(horizontal=True):
                                dpg.add_spacer(width=80)
                                dpg.add_text("New Project")

                            dpg.add_image_button(
                                self.load_texture("Assets/plus.png"),
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
                    dpg.add_text(default_value="Version: Pre-alpha",
                                 color=[255, 255, 255, 120])

            dpg.set_primary_window("Home Window", True)
            dpg.set_viewport_large_icon("Assets/Formula_uottawa.ico")
            dpg.setup_dearpygui()
            dpg.set_viewport_pos([0, 0])
            dpg.show_viewport(maximized=True)
            dpg.start_dearpygui()
            dpg.destroy_context()
