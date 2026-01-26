# Harsh Patel

import dearpygui.dearpygui as dpg
import tkinter as tk
from tkinter import filedialog



def import_static_image(file_path):
    w, h, channels, data = dpg.load_image(file_path)

    with dpg.texture_registry():
        texture = dpg.add_static_texture(w, h, data)
    return (texture)


def load_project():
    pass


def save_project():
    pass


def print_me():
    pass  # Will be removed when homepage menu bar is complete


def Choose_file(text_box):
    """Creates a pop up menu to choose a file.


    Args:
        text_box (Dpg widget): The widget where current chosen file path is shown.


    Returns:
        text_box (Dpg widget): The widget does not get returned but rather its value is set to the file path.
    """

    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(title="Select a file")

    root.destroy()
    dpg.set_value(text_box, file_path)


def import_data(file_path):
    """Gathers data from the csv file.


    Args:
        file_path (string): file path of csv containing data.


    Returns:
        Tuple: List containing x data, followed by list containing y data.
    """
    pass


def filter_data(unfiltered_x_data, unfiltered_y_data, filter_type):
    """filters data based on filter type selected.


    Args:
        unfiltered_x_data (list): Raw x values imported directly from file.
        unfiltered_y_data (list): Raw y values imported directly from file.


    Returns:
        tuple: Expected Values:
            - "filtered_x_data" (list): List of filtered x values.
            - "filtered_y_data" (list): List of filtered y values.
    """

    if filter_type == "None":

        filtered_x_data = unfiltered_x_data
        filtered_y_data = unfiltered_y_data

    elif filter_type == "High-Pass":  # filter processing needs to be added

        pass

    elif filter_type == "Low-Pass":

        pass

    elif filter_type == "Band-Pass":

        pass

    return (filtered_x_data, filtered_y_data)


def make_graph(name, file_path, graph_type, filter_type):
    """Makes graph widget inside of new window.


    Args:
        name (string): name/label of the new window.
        file_path (string): file path of csv containing data.
        graph_type (string): type of graph wanted.
        filter_type (string): type of filter to be applied to the data.


    Returns:
        None, Makes a new window and widget.
    """

    unfiltered_x_data, unfiltered_y_data = import_data(file_path)
    filtered_x_data, filtered_y_data = filter_data(unfiltered_x_data, unfiltered_y_data, filter_type)

    if graph_type == "Line Graph":  # Graph creation coming soon

        pass

    elif graph_type == "Bar Chart":

        pass

    elif graph_type == "Histogram":

        pass

    elif graph_type == "Scatter Plot":

        pass

    elif graph_type == "Pie Chart":

        pass

    elif graph_type == "Heat Map":

        pass


def graph_type_check(user_data):
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
                                "Heat Map": ["High-Pass", "Low-Pass", "Band-Pass", "None"]
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
                graph_type = dpg.add_combo(["Line Graph", "Bar Chart", "Histogram", "Scatter Plot", "Pie Chart", "Heat Map"],
                                           default_value="Choose Type of Graph")

                filter_type = dpg.add_combo(["High-Pass", "Low-Pass", "Band-Pass", "None"],
                                            default_value="Choose Type of Filter")

                dpg.add_spacer(height=5)
                dpg.add_button(label="OK", width=75, callback=lambda: graph_type_check((name, file_path, graph_type, filter_type)))

    else:

        dpg.delete_item("ask_graph")
        dpg.split_frame()  # force Dpg to generate a frame and load new widget states, close modal before making graph
        make_graph(name, file_path, graph_type, filter_type)


def file_path_check(user_data):
    """Verifiy the user chose a file path.


    Args:
        user_data (tuple): Expected Values:
            - "name" (str): name of the graph.
            - "file_path" (input text widget): widget containing current chosen file path.
            - "graph_type" (combo widget): the menu widget for types of graphs.
            - "filter_type" (combo widget): the menu widget for types of filters.


    Returns:
        None, Calls graph_type_check function.
    """

    name, file_path, graph_type, filter_type = user_data
    file_path = dpg.get_value(file_path)

    if (file_path == ""):

        if not dpg.does_item_exist("ask_file"):

            with dpg.window(label="File Path", modal=True, tag="ask_file", no_title_bar=True, pos=[200, 200]):

                dpg.add_text("Please Choose A File For the Graph Data!")
                dpg.add_separator()
                dpg.add_spacer(height=5)
                path_display = dpg.add_input_text(hint="Selected File Path", readonly=True, width=300)
                file_path_button = dpg.add_button(label="Choose File", callback=lambda: Choose_file(path_display))
                dpg.add_spacer(height=5)
                dpg.add_button(label="OK", width=75, callback=lambda: file_path_check((name, path_display, graph_type, filter_type)))

    else:

        user_data = (name, file_path, graph_type, filter_type)
        dpg.delete_item("ask_file")
        dpg.split_frame()  # force Dpg to generate a frame and load new widget states, prevents multiple modals
        graph_type_check(user_data)


def name_check(sender, app_data, user_data):
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
                dpg.add_button(label="OK", width=75, callback=lambda: name_check(None, None, (name_input, file_path, graph_type, filter_type)))

    else:

        user_data = (name, file_path, graph_type, filter_type)
        dpg.delete_item("ask_name")
        dpg.split_frame()  # force Dpg to generate a frame and load new widget states, prevents multiple modals
        file_path_check(user_data)


def make_graph_window(x_pos, y_pos, ht, wd):
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
                            file_path = dpg.add_button(label="Choose File", callback=lambda: Choose_file(path_display))

                    elif r == 1:

                        graph_name = dpg.add_input_text(hint="Enter Graph Name", width=300)

                    elif r == 5:

                        graph_type = dpg.add_combo(
                            ["Line Graph", "Bar Chart", "Histogram", "Scatter Plot", "Pie Chart", "Heat Map"],
                            default_value="Choose Type of Graph",
                        )

                    elif (r == 7):

                        filter_type = dpg.add_combo(
                            ["High-Pass", "Low-Pass", "Band-Pass", "None"],
                            default_value="Choose Type of Filter",
                        )
                        dpg.add_button(label="Submit", callback=name_check, user_data=(graph_name, path_display, graph_type, filter_type))

                    else:

                        dpg.add_spacer(height=(ht - 150) / 6)  # vertical spacing between the rows that include widgets


dpg.create_context()


with dpg.font_registry():
    try:
        font_path = ("C:/Windows/Fonts/segoeui.ttf")  # will fail on non-Windows
        segoe = dpg.add_font(font_path, 18)
        dpg.bind_font(segoe)  # only runs if add_font worked
    except Exception:
        pass


with dpg.theme() as global_theme:

    with dpg.theme_component(dpg.mvButton):

        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10.0)

dpg.bind_theme(global_theme)


dpg.create_viewport(title='Formula uOttawa Telemetry Software', width=800, height=600)


with dpg.viewport_menu_bar(tag="Main Menu Bar"):  # Menu Bar will be revised and corrected soon

    with dpg.menu(label="File"):
        dpg.add_menu_item(label="Save Project", callback=lambda: save_project())
        dpg.add_menu_item(label="Load Project", callback=lambda: load_project())
        
            
    with dpg.menu(label="Graph"):
        dpg.add_menu_item(label="Make New Graph", callback=lambda: make_graph_window(400, 150, 450, 770))
            
            

    with dpg.menu(label="Filter"):
        pass
        
    with dpg.menu(label="Trim"):
        pass

    with dpg.menu(label="Correlation"):
        pass


with dpg.window(tag="Home Window", no_move=True, no_resize=True, pos=(0, 0)):
    
    with dpg.table(header_row=False,
                    policy=dpg.mvTable_SizingFixedFit,
                    no_host_extendX=True,                
                    borders_innerV=False,                # Set the following all to True to see the table lines
                    borders_innerH=False,
                    borders_outerV=False,
                    borders_outerH=False,
                    ):

        dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)
        dpg.add_table_column(width_fixed=True, init_width_or_weight=0.0)
        dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)
    

        with dpg.table_row():
            dpg.add_spacer(height=150)
        

        with dpg.table_row():

            dpg.add_spacer()
            dpg.add_image(import_static_image("Assets/formula_logo.png"), height=150, width=699)


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

                    dpg.add_image_button(import_static_image("Assets/plus.png"), background_color=(0,0,0,70), frame_padding=0, width=250, height=250)


                dpg.add_spacer(width=60)


                with dpg.group():

                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=82)
                        dpg.add_text("Load Project")

                    dpg.add_image_button(import_static_image("Assets/file_icon.png"), background_color=(0,0,0,70), frame_padding=0, width=250, height=250)
                dpg.add_spacer(width=63)


        with dpg.table_row():
            dpg.add_spacer(height=97)


        with dpg.table_row():
            dpg.add_text(default_value="Version: Pre-alpha", color=[255, 255, 255, 120])
            





        

        


dpg.set_primary_window("Home Window", True)
dpg.set_viewport_large_icon("Assets/Formula_uottawa.ico")
dpg.setup_dearpygui()
dpg.set_viewport_pos([0, 0])
dpg.show_viewport(maximized=True)  # prevents window sizing and positioning from failing on intital creation
dpg.start_dearpygui()
dpg.destroy_context()

