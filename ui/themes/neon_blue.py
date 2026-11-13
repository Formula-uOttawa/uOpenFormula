import dearpygui.dearpygui as dpg

def neon_blue():

    with dpg.theme() as neon_blue:
        with dpg.theme_component(dpg.mvAll):

            # backgrounds
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (12, 15, 30))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (18, 22, 45))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (25, 30, 60))
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg,(32, 35, 70))
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (32, 35, 70))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (20, 90, 140))


            # neon accents
            dpg.add_theme_color(dpg.mvThemeCol_Button, (18, 22, 45))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (25, 30, 60))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (20, 25, 55))
            dpg.add_theme_color(dpg.mvThemeCol_Separator, (0, 200, 255))

            # text
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255))

            
            # Remove borders
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 0)
            dpg.add_theme_style(dpg.mvStyleVar_PopupBorderSize, 0)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0)

            # rounding for modern look
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6)
    
    with dpg.theme(tag="cyan_border_theme"):
        with dpg.theme_component(dpg.mvAll):

            dpg.add_theme_color(
                dpg.mvThemeCol_Border,
                (0, 200, 255)
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_WindowBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1)
            

    return(neon_blue)

def create_image_button_theme():

    with dpg.theme() as image_theme:
        with dpg.theme_component(dpg.mvImageButton):

            # Normal background
            dpg.add_theme_color(
                dpg.mvThemeCol_Button,
                (0, 0, 0, 0)
            )

            # Hover background
            dpg.add_theme_color(
                dpg.mvThemeCol_ButtonHovered,
                (0, 200, 255, 60)
            )

            # Click background
            dpg.add_theme_color(
                dpg.mvThemeCol_ButtonActive,
                (0, 200, 255, 100)
            )

    return image_theme


