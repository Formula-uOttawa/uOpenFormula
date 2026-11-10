import dearpygui.dearpygui as dpg
from ui.render_manager import RenderManager as rm
from core.data_manager import DataManager
from ui.home_page import HomePage

class Runtime:

    def __init__(self):
        self.importer = DataManager(self.update_break_temp, self.show_brake_temps)
        self.home_page = HomePage(self.importer)
        self.render_manager = rm()
        self.boot()


    def boot(self):
                """Initializes the homepage and loads all necessary elements."""
                
                dpg.create_context()
                
                # Set theme for button rounding.
                with dpg.theme() as global_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10.0)
                dpg.bind_theme(global_theme)

                self.home_page.nav_themes()
                
                # Create and populate main viewport
                dpg.create_viewport(title='uOpenFormula',
                                    width=800, height=600)
                
                self.init_menu_bar()
                self.home_page.show_landing()
                
                dpg.set_primary_window("Landing Page", True)
                dpg.set_viewport_large_icon("assets/Formula_uottawa.ico")
                dpg.setup_dearpygui()
                dpg.set_viewport_pos([0, 0])
                dpg.show_viewport(maximized=True)  # prevents window sizing and positioning from failing on initial creation
                self.render_manager.start()
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
                    dpg.add_menu_item(label="Linear", callback=lambda: dpg.show_metrics())

    def update_break_temp(self, temps):
        self.render_manager.brake_temps = temps


    def show_brake_temps(self, flag):
        self.render_manager.show_brake_temps = flag

    