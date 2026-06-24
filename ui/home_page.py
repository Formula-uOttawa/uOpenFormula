import dearpygui.dearpygui as dpg
from core.data_manager import DataManager
import tkinter as tk
from tkinter import filedialog
from ui.utils.load_texture import load_texture
from treelib import Tree
import pkgutil
import ui.views as views_package
import importlib

def _load_view_map():
    """Auto-discover all view classes from ui/views/.
    
    Convention: file 'ui/views/foo.py' must contain a class ending in 'View'.
    The filename (without .py) must match the nav tree node identifier.
    """
    view_map = {}
    for finder, name, ispkg in pkgutil.iter_modules(views_package.__path__):
        module = importlib.import_module(f"ui.views.{name}")
        # Find the first class in the module whose name ends in "View"
        for attr_name in dir(module):
            if attr_name.endswith("View"):
                view_map[name] = getattr(module, attr_name)
                break
    return view_map

VIEW_MAP = _load_view_map()

class HomePage:
    """Stores the logic of the home and landing page gui. TODO do this docstring"""
    
    file_path = ""
    df = None
    importer = DataManager()
    
    SWAPPABLE_WINDOWS = []  # populated dynamically from tree
    
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
        
        # Active nav button highlighted
        with dpg.theme() as self.theme_nav_active:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button,        (80, 130, 160, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (90, 145, 175, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  (70, 115, 145, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10.0)

        # Inactive nav button default
        with dpg.theme() as self.theme_nav_inactive:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button,        (50, 50, 50, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (70, 70, 70, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  (90, 90, 90, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10.0)
        
        # Create and populate main viewport
        dpg.create_viewport(title='uOpenFormula',
                            width=800, height=600)
        
        self.init_menu_bar()
        self.show_landing()
        
        dpg.set_primary_window("Landing Page", True)
        dpg.set_viewport_large_icon("assets/Formula_uottawa.ico")
        dpg.setup_dearpygui()
        dpg.set_viewport_pos([0, 0])
        dpg.show_viewport(maximized=True)  # prevents window sizing and positioning from failing on initial creation
        dpg.start_dearpygui()
        dpg.destroy_context()
    
    def init_menu_bar(self):
        # Add and populate menu bar at the top.
        with dpg.viewport_menu_bar(tag="Main Menu Bar"):  # TODO: revisions to menu bar
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Save Project", callback=lambda: None)
                dpg.add_menu_item(label="Load Project", callback=lambda: self.select_file_tk())
                
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
    
    def _build_nav_tree(self):
        self.nav = Tree()
        self.nav.create_node("Home", "home")
        self.nav.create_node("Aerodynamics", "aero", parent="home")
        self.nav.create_node("Coastdown", "aero_coastdown", parent="aero")
        self.nav.create_node("Yaw Rate", "aero_yawrate", parent="aero")
        self.nav.create_node("Lap time", "aero_laptime", parent="aero")
        
        self.nav.create_node("Electrical", "elec", parent="home")
        self.nav.create_node("Monitor", "elec_monitor", parent="elec")
        
        self.nav.create_node("Drivetrain", "drive", parent="home")
        self.nav.create_node("Acceleration comparison", "drive_accel", parent="drive")
        self.nav.create_node("Shifting comparison", "drive_shift", parent="drive")
        
        self.nav.create_node("Powertrain", "power", parent="home")
        self.nav.create_node("Oil starvation", "power_oilstarv", parent="power")
        self.nav.create_node("Intake tests", "power_intake", parent="power")
        self.nav.create_node("Radiator cooling", "power_radtemp", parent="power")
        
        self.nav.create_node("Frame", "frame", parent="home")
        self.nav.create_node("Torsion test", "frame_torsion", parent="frame")
        
        self.nav.create_node("Suspension", "susp", parent="home")
        self.nav.create_node("Frequency analysis", "susp_freq", parent="susp")
        self.nav.create_node("Slip angle", "susp_slip", parent="susp")
        
        

        # How we track the current state of the navbar. List gets appended with
        # entries as we go through the tree.
        self.nav_stack = ["home"]

        # Build the swappable window list from all non-root nodes
        self.SWAPPABLE_WINDOWS = [
            node.identifier
            for node in self.nav.all_nodes()
            if node.identifier != "home"
        ]
        
    def push_nav(self, view_key):
        """Drill into a child view, or select a leaf without redrawing sidebar."""
        children = self.nav.children(view_key)
        is_leaf = len(children) == 0

        if is_leaf:
            # Don't push to stack or redraw — just switch view and highlight
            self._switch_main_view(view_key)
            self._update_highlights(view_key)
        else:
            self.nav_stack.append(view_key)
            self._refresh_sidebar()
            self._switch_main_view(view_key)

    def pop_nav(self):
        """Go up one level."""
        if len(self.nav_stack) > 1:
            self.nav_stack.pop()
            self._refresh_sidebar()
            self._switch_main_view(self.nav_stack[-1])
    
    def _update_highlights(self, active_key):
        """Highlight the active button among its siblings in the current sidebar."""
        parent_key = self.nav_stack[-1]
        siblings = self.nav.children(parent_key)

        for sibling in siblings:
            btn_tag = f"nav_btn_{sibling.identifier}"
            if dpg.does_item_exist(btn_tag):
                theme = (
                    self.theme_nav_active
                    if sibling.identifier == active_key
                    else self.theme_nav_inactive
                )
                dpg.bind_item_theme(btn_tag, theme)
    
    def _switch_main_view(self, view_key):
        """Show only the window matching view_key, hide all others."""
        for win in self.SWAPPABLE_WINDOWS:
            if dpg.does_item_exist(win):
                dpg.configure_item(win, show=(win == view_key))

    def _refresh_sidebar(self):
        """Wipe and redraw sidebar contents for the current nav stack top."""
        dpg.delete_item("navbar", children_only=True)
        self._build_sidebar_for(self.nav_stack[-1])
    
    def _build_sidebar_for(self, view_key):
        node = self.nav.get_node(view_key)
        children = self.nav.children(view_key)

        dpg.add_text(node.tag, parent="navbar")
        dpg.add_separator(parent="navbar")

        if len(self.nav_stack) > 1:
            dpg.add_button(
                label="<- Back",
                callback=lambda: self.pop_nav(),
                width=-1,
                parent="navbar",
            )
            dpg.add_separator(parent="navbar")

        for child in children:
            dpg.add_button(
                label=child.tag,
                tag=f"nav_btn_{child.identifier}",   # <-- needed for highlight lookup
                user_data=child.identifier,
                callback=lambda s, a, u: self.push_nav(u),
                width=-1,
                parent="navbar",
            )
    
    def show_landing(self):
        # Create the main window.
        with dpg.window(tag="Landing Page", no_move=True, no_resize=True, pos=(0, 0)):
            
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
                                                 callback=lambda: self.select_file_tk())
                        dpg.add_spacer(width=63)

                with dpg.table_row():
                    dpg.add_spacer(height=97)

                with dpg.table_row():
                    dpg.add_text(default_value="Version: Pre-alpha", color=[255, 255, 255, 120])
    
    def select_file_tk(self):
        """
        Select a file using native operating system UI.
        """
        
        root = tk.Tk()
        root.withdraw()
        self.file_path = filedialog.askopenfilename()
        
        # This runs load() + validations and returns the DataFrame
        # TODO: this makes two copies of df? If so investigate making this not a hard copy.
        self.df = self.importer.import_and_validate(self.file_path)
        
        
        dpg.delete_item("Landing Page", children_only=True)
        
        self.show_home()
        
        # The data preview window
        # TODO: move this
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
        
    
    def show_home(self):
        self._build_nav_tree()
        
        self.views = {}
        
        with dpg.window(
            label="Navigation", tag="navbar",
            pos=[0, 0], width=200,
            height=dpg.get_viewport_height(),
            no_close=True, no_move=True, no_collapse=True,
        ):
            self._build_sidebar_for("home")

        # Create all view windows (hidden by default except first)
        for node in self.nav.all_nodes():
            if node.identifier == "home":
                continue
            # First child of home is the default
            default_view = self.nav.children("home")[0].identifier
            is_first = (node.identifier == default_view)
            with dpg.window(
                label=node.tag,
                tag=node.identifier,
                pos=[200, 0],
                width=dpg.get_viewport_width() - 200,
                height=dpg.get_viewport_height(),
                no_close=True, no_move=True,
                no_resize=True, no_collapse=True,
                show=is_first,
            ):
                if node.identifier in VIEW_MAP:
                    view = VIEW_MAP[node.identifier](self.importer)
                    view.build(node.identifier)       # parent_tag = window tag
                    self.views[node.identifier] = view
                else:
                    # Parent node with no dedicated view — just a placeholder
                    dpg.add_text(f"{node.tag}: select a sub-view from the sidebar.")
