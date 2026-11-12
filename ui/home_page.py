import importlib
import pkgutil
import platform
import tkinter as tk
import dearpygui.dearpygui as dpg
import ui.views as views_package
from random import randint
from subprocess import check_output
from sys import executable  # To run subprocess
from tkinter import filedialog
from treelib import Tree
from ui.utils.load_texture import load_texture


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

    SWAPPABLE_WINDOWS = []  # populated dynamically from tree

    def __init__(self, importer):
        self.importer = importer

    def nav_themes(self):
        # Active nav button highlighted
        with dpg.theme() as self.theme_nav_active:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (16, 91, 136))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (22, 110, 160))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (12, 75, 115))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6.0)


        # Inactive nav button default
        with dpg.theme() as self.theme_nav_inactive:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (18, 22, 45))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (25, 30, 60))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (20, 25, 55))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6.0)

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
        self.nav.create_node("Brake Temps", "susp_brake", parent="susp")
        self.nav.create_node("Frequency analysis", "susp_freq", parent="susp")
        self.nav.create_node("Slip angle", "susp_slip", parent="susp")

        self.nav.create_node("Raw Data", "raw_data", parent="home")

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

        dpg.configure_item("home_view", show=(view_key == "home"))

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
                tag=f"nav_btn_{child.identifier}",  # <-- needed for highlight lookup
                user_data=child.identifier,
                callback=lambda s, a, u: self.push_nav(u),
                width=-1,
                parent="navbar",
            )

    def show_landing(self):
        # Create the main window.

        viewport_width = dpg.get_viewport_width()
        viewport_height = dpg.get_viewport_height()
        vertical_padding = (viewport_height - 360) / 2

        with dpg.window(tag="Landing Page", no_move=True, no_resize=True, pos=(0, 0)):
            # This table houses the logo, new project, and load project buttons at the start of the program.
            with dpg.table(
                header_row=False,
                policy=dpg.mvTable_SizingFixedFit,
                no_host_extendX=True,
                borders_innerV=False,
                borders_innerH=False,
                borders_outerV=False,
                borders_outerH=False,
            ):
                dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=0.0)
                dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)

                with dpg.table_row():
                    dpg.add_spacer(height=vertical_padding)

                with dpg.table_row():
                    dpg.add_spacer()
                    dpg.add_image(
                        load_texture("assets/formula_logo.png"), height=233, width=699
                    )

                with dpg.table_row():
                    dpg.add_spacer(height=150)

                with dpg.table_row():
                    dpg.add_spacer()
                    with dpg.group(horizontal=True, horizontal_spacing=4):
                        dpg.add_spacer(width=63)

                        with dpg.group():
                            with dpg.group(horizontal=True):
                                dpg.add_spacer(width=80)
                                dpg.add_text("Load Project")

                            dpg.add_image_button(
                                load_texture("assets/file_icon.png"),
                                tag="load_project_button",
                                background_color=(0, 0, 0, 0),
                                frame_padding=0,
                                width=250,
                                height=250,
                                callback=lambda: self.load_project(),
                            )

                        dpg.add_spacer(width=60)

                        with dpg.group():
                            with dpg.group(horizontal=True):
                                dpg.add_spacer(width=82)
                                dpg.add_text("New Project")

                            dpg.add_image_button(
                                load_texture("assets/plus.png"),
                                tag="new_project_button",
                                background_color=(0, 0, 0, 0),
                                frame_padding=0,
                                width=250,
                                height=250,
                                callback=lambda: self.new_project(),
                            )

                        dpg.add_spacer(width=63)

                with dpg.table_row():
                    dpg.add_spacer(height=(dpg.get_viewport_height() - 560))

                with dpg.table_row():
                    dpg.add_text(
                        default_value="Version: Pre-Beta", color=[255, 255, 255, 200]
                    )

    def new_project(self):
        # meant for future use

        self.load_project()

    def load_project(self):
        # meant for future use
        self.load_file()

        if dpg.does_item_exist("Landing Page"):
            dpg.delete_item("Landing Page", children_only=True)

        self.show_home()

    def load_file(self):
        self.select_file_tk()

    def select_file_tk(self):
        """
        Select a file using native operating system UI.
        """

        if platform.system() == "Windows":
            self.file_path = self.windows_open_file()

        elif platform.system() == "Darwin":
            self.file_path = self.mac_open_file()

        elif platform.system() == "Linux":
            print("Running on Linux")

        self.df = self.importer.import_and_validate(self.file_path)

    def windows_open_file(self):
        # TODO: move this to the new data manager view
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename()
        root.destroy()  # DO NOT DELETE EVER

        return file_path

    def mac_open_file(self):
        file = check_output([executable, "./ui/get_file.py"])
        return(f"{file=}")

    def show_home(self):
        self._build_nav_tree()

        self.views = {}

        with dpg.window(
            label="Navigation",
            tag="navbar",
            pos=[0, 27],
            width=200,
            height=(dpg.get_viewport_height() - 67),
            no_close=True,
            no_move=True,
            no_collapse=True,
            no_resize=True,
        ):
            self._build_sidebar_for("home")

        
        self.make_home_view()

        dpg.bind_item_theme("navbar", "cyan_border_theme")
        dpg.bind_item_theme("home_view", "cyan_border_theme")

        # Create all view windows (hidden by default except first)
        for node in self.nav.all_nodes():
            if node.identifier == "home":
                continue
            
            with dpg.window(
                label=node.tag,
                tag=node.identifier,
                pos=[201, 27],
                width=dpg.get_viewport_width() - 219,
                height=dpg.get_viewport_height() - 67,
                no_close=True,
                no_move=True,
                no_resize=True,
                no_collapse=True,
                show=False,
            ):
                dpg.bind_item_theme(node.identifier, "cyan_border_theme")
                if node.identifier in VIEW_MAP:
                    view = VIEW_MAP[node.identifier](self.importer)
                    view.build(node.identifier)  # parent_tag = window tag
                    self.views[node.identifier] = view
                else:
                    # Parent node with no dedicated view — just a placeholder
                    dpg.add_text(f"{node.tag}: select a sub-view from the sidebar.")

        dpg.set_viewport_resize_callback(lambda: self.resize_windows())

    def get_motm(self):
        """
        generates random message of the month

        """        
        
        messages = [
            "Wagwan Famalam - Alex",
            "It Fits In CAD!",
            "Shirley It'll Work!",
            "If You Find Something Wrong,\n It's Not A Bug, It's A Feature",
            "Powered By Caffeine and Deadlines",
            "Designed By Sleep Deprived Students",
            "Now With 20% Fewer Crashes!",
            "Run With Hopes And Dreams",
            "Built Different. Runs Slower",
            "Optimized For Developer Happiness",
            "Endurance? Never Heard Of Her",
            "Downforce? Never Heard Of Her",
            "Ayham Approved This... Hopefully",
            "Made Possible By Sleep Deprivation",
            "Our CAD Model Is Faster",
            "Manufacturing tolerances\n are suggestions - Someone",
            "The Car Is Almost Finished... Hopefully",
            "Trust The Data. Question The Sensor.",
            "We Don't Know How This Is Working",
            "It's Not Noise, It's Character",
            "Built By Students. Lower Your Expectations",
            "Our Sleep Schedules Are Theoretical",
            "The Car Has Better Attendance Than Us",
            "Please Return The 10 mm Socket",
            "Someone Stole The Torque Wrench Again",
            "Our Most Reliable Component Is the Group Chat",
            "The Car Isn't Late. The Calendar Is Wrong",
            "Hello, Future Engineer!",
            "Not Suitable For Underwater Use",
            "We Know What You Did In SolidWorks",
            "Plot Twist: It's Another Plot",
            "Speed And Powwerrrrrr!",
            "CLARKSOOOON!",
            "Ambitious, But Rubbish",
            "GP2 engine! GP2!",
            "Fernando is faster than you",
            "The Seat is Full Of Water",
            "Loading at Ferrari strategy speed",
            "Try a Kalman Filter - PhD Knowledge",
            'We Made "Various Changes" - Josh',
        ]
        
        return(messages[randint(0, len(messages)-1)])

    def make_home_view(self):
        with dpg.window(
                    label="Welcome to uOpenFormula",
                    tag="home_view",
                    pos=[201, 27],
                    width=dpg.get_viewport_width() - 219,
                    height=dpg.get_viewport_height() - 67,
                    no_close=True,
                    no_move=True,
                    no_resize=True,
                    no_collapse=True,
                ):  
                    self.message = self.get_motm()

                    dpg.add_image( load_texture("assets/formula_logo.png"), width=450, height=150, tag="home_logo")

                    dpg.add_text(self.message, tag="home_message")
                    dpg.bind_item_font("home_message", "Heading_font")
                    self.positon_motm()
    
    def positon_motm(self):
        window_width, window_height = dpg.get_item_rect_size("home_view")
        
        
        # Get the actual sizes
                            
        text_width, text_height = dpg.get_text_size(self.message)
        text_width *= 2
        text_height *= 2
        
        # Space between logo and text
        gap = 50
        
        # Total height of both elements
        total_height = 150 + gap + text_height
        
        # Center the entire layout vertically
        start_y = (window_height - total_height - 400) / 2
        
        # Center logo horizontally
        logo_x = (window_width - 470) / 2
        
        # Center text horizontally
        text_x = (window_width - text_width - 20) / 2
        
        # Position both elements
        dpg.set_item_pos("home_logo", [logo_x, start_y])
        dpg.set_item_pos("home_message", [text_x, start_y + 150 + gap])

    def resize_windows(self):
        viewport_width = dpg.get_viewport_width()
        viewport_height = dpg.get_viewport_height()

        # Resize navigation window
        dpg.configure_item(
            "navbar",
            height=viewport_height - 67
        )
        

        # Resize all analysis windows
        for window in self.SWAPPABLE_WINDOWS:
            if dpg.does_item_exist(window):
                dpg.configure_item(
                    window,
                    width=viewport_width - 219,
                    height=viewport_height - 67
                )


        
        # Resize Home window
        if dpg.does_item_exist("home_view"):
            dpg.configure_item(
            "home_view",
            width=viewport_width - 219,
            height=viewport_height - 67
            )
            dpg.set_frame_callback(
                dpg.get_frame_count() +2,
                lambda *args: self.positon_motm()
            )
            


