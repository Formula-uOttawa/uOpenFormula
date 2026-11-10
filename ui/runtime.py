import dearpygui.dearpygui as dpg
from ui.render_manager import RenderManager as rm
from core.data_manager import DataManager
from ui.home_page import HomePage

class Runtime:


    def __init__(self):
        self.importer = DataManager(self.update_break_temp, self.play_brake_temps, self.set_brake_temp_step)
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
            with dpg.viewport_menu_bar(tag="Main Menu Bar"):  
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="Save Project", callback=lambda: None)
                    dpg.add_menu_item(label="Load Project", callback=lambda: self.home_page.load_file())

                
                with dpg.menu(label="Debugging Tools"):
                    dpg.add_menu_item(label="Metrics", callback=lambda: dpg.show_metrics())
                    dpg.add_menu_item(label="Debugging Menu", callback=lambda: dpg.show_debug())
                    dpg.add_menu_item(label="Item  Registry", callback=lambda: dpg.show_item_registry())

                dpg.add_menu_item(label="Help", callback=lambda: None)


    def update_break_temp(self, temps):
        self.render_manager.brake_temps = temps


    def play_brake_temps(self, flag):
        self.render_manager.play_brake_temps = flag


    def set_brake_temp_step(self, playrate):

        self.render_manager.update_interval = (1/(20 * playrate))

