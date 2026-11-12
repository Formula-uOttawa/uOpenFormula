import dearpygui.dearpygui as dpg
from ui.render_manager import RenderManager as rm
from core.data_manager import DataManager
from ui.home_page import HomePage
from ui.themes import neon_blue

class Runtime:


    def __init__(self):
        self.importer = DataManager(self.update_break_temp, self.play_brake_temps, self.set_brake_temp_step, self.set_brake_texture)
        self.home_page = HomePage(self.importer)
        self.render_manager = rm()
        self.boot()


    def boot(self):
                """Initializes the homepage and loads all necessary elements."""
                
                dpg.create_context()

                with dpg.font_registry():
                    normal_font = dpg.add_font(
                        "Assets/Fonts/Oxanium-Regular.ttf",
                        14
                    )

                    heading_font = dpg.add_font(
                        "Assets/Fonts/Oxanium-SemiBold.ttf",
                        28,
                        tag = "Heading_font",
                    )

                    menu_font = dpg.add_font(
                        "Assets/Fonts/Oxanium_Regular_viewport_menubar.ttf",
                        13
                    )
                
                dpg.bind_font(normal_font)

                neon_blue_theme = neon_blue.neon_blue()
                image_button_theme = neon_blue.create_image_button_theme()
                dpg.bind_theme(neon_blue_theme)

                self.home_page.nav_themes()
                
                # Create and populate main viewport
                dpg.create_viewport(title='uOpenFormula', width=800, height=600)
                
                self.init_menu_bar()
                dpg.bind_item_font("file_menu", menu_font)
                dpg.bind_item_font("debugging_tools_menu", menu_font)
                dpg.bind_item_font("help_button", menu_font)
    
                self.home_page.show_landing()
                dpg.bind_item_theme("new_project_button", image_button_theme)
                dpg.bind_item_theme("load_project_button", image_button_theme)
                
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
                with dpg.menu(tag="file_menu", label="File"):
                    dpg.add_menu_item(label="Save Project", callback=lambda: None)
                    dpg.add_menu_item(label="Load Project", callback=lambda: self.home_page.load_file())

                
                with dpg.menu(tag="debugging_tools_menu", label="Debugging Tools"):
                    dpg.add_menu_item(label="Metrics", callback=lambda: dpg.show_metrics())
                    dpg.add_menu_item(label="Debugging Menu", callback=lambda: dpg.show_debug())
                    dpg.add_menu_item(label="Item  Registry", callback=lambda: dpg.show_item_registry())

                dpg.add_menu_item(tag="help_button", label="Help", callback=lambda: None)
            


    def update_break_temp(self, temps):
        self.render_manager.brake_temps = temps


    def play_brake_temps(self, flag):
        self.render_manager.play_brake_temps = flag
        if flag:
            dpg.set_value("Brake Disc View", "Brake Disc View (Playing)")
        else:
             dpg.set_value("Brake Disc View", "Brake Disc View (Paused)")


    def set_brake_temp_step(self, playrate):

        self.render_manager.update_interval = (1/(20 * playrate))


    def set_brake_texture(self, texture):
        self.render_manager.generate_brake_texture = texture