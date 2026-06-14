import dearpygui.dearpygui as dpg
from core.data_manager import DataManager
import tkinter as tk
from tkinter import filedialog
from ui.utils.load_texture import load_texture

class HomePage:
    """Stores the logic of the home and landing page gui. TODO do this docstring"""
    
    file_path = ""
    df = None
    metadata = None
    importer = DataManager()
    
    def __init__(self):
        self.show_home_page()
    
    def show_home_page(self):
        """Initializes the homepage and loads all necessary elements."""
        
        dpg.create_context()

        # Set theme for button rounding.
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10.0)
        dpg.bind_theme(global_theme)
        
        # Create main viewport
        dpg.create_viewport(title='Formula uOttawa Telemetry Software', width=800, height=600)
        
        self.init_menu_bar()
            
        self.show_landing()
    
    def init_menu_bar(self):
        # Add and populate menu bar at the top.
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
    
    def show_landing(self):
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
                    dpg.add_image(load_texture("assets/formula_logo.png"), height=150, width=699)
                
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

                            dpg.add_image_button(load_texture("assets/plus.png"),
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
                            dpg.add_image_button(load_texture("assets/file_icon.png"),
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
            dpg.set_viewport_large_icon("assets/Formula_uottawa.ico")
            dpg.setup_dearpygui()
            dpg.set_viewport_pos([0, 0])
            dpg.show_viewport(maximized=True)  # prevents window sizing and positioning from failing on initial creation
            dpg.start_dearpygui()
            dpg.destroy_context()
    
    def select_file(self):
        """
        Select a file using a ui.
        """
        
        root = tk.Tk()
        root.withdraw()
        self.file_path = filedialog.askopenfilename()
        
        # This runs load() + validations and returns the DataFrame
        self.df = self.importer.import_and_validate(self.file_path)
        
        self.metadata = [f"{k}: {v}" for k, v in self.importer.metadata.items() if v]
        
        dpg.delete_item("Home Window", children_only=True)
        
        self.show_home()
        
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
    
    def show_home(self):
        # List of windows that should be swappable
        SWAPPABLE_WINDOWS = ["preview_window", "aerodynamics_window","electrical_window"]

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
            dpg.add_text("Sub-team Analysis")
            dpg.add_separator()
            # Pass the target window tag as user_data
            dpg.add_button(label="Preview",
                           user_data="preview_window",
                           callback=switch_view,
                           width=-1)
            dpg.add_button(label="Aerodynamics",
                           user_data="aerodynamics_window",
                           callback=switch_view,
                           width=-1)
            dpg.add_button(label="Electrical",
                           user_data="electrical_window",
                           callback=switch_view,
                           width=-1)
        
        # Data preview
        with dpg.window(label="Preview",
                        tag="preview_window", pos=[200, 0],
                        width=dpg.get_viewport_width(),
                        height=dpg.get_viewport_height(),
                        no_close=True,
                        no_move=True,
                        no_resize=True,
                        no_collapse=True,
                        show=True):
            dpg.add_text("Overall data preview + metadata goes here")
        
        # Aerodynamics
        with dpg.window(label="Aerodynamics",
                        tag="aerodynamics_window", pos=[200, 0],
                        width=dpg.get_viewport_width(),
                        height=dpg.get_viewport_height(),
                        no_close=True,
                        no_move=True,
                        no_resize=True,
                        no_collapse=True,
                        show=False):
            dpg.add_text("Real-time aerodynamic load data would go here.")
            # Add your plots and readouts here
        
        # Electrical
        with dpg.window(label="Electrical",
                        tag="electrical_window",
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
    
    