# importMotecCSV.py

import dearpygui.dearpygui as dpg
from data_manager import MoTeCImporter
from pathlib import Path

def on_file_selected(sender, app_data):
    """
    Called automatically when the user picks a file in the file dialog.
    """

    # Full path to the file the user selected
    file_path = app_data["file_path_name"]

    try:
        # Use the existing class you were given
        importer = MoTeCImporter(file_path)

        # This runs load() + validations and returns the DataFrame
        df = importer.import_and_validate()

        # If we got here, it worked
        dpg.set_value("status", "Import successful")
        dpg.show_item("status")

        meta_lines = [f"{k}: {v}" for k, v in importer.metadata.items() if v]
        dpg.set_value("metadata_box", "\n".join(meta_lines))

        preview_text = df.to_string()
        dpg.set_value("preview", preview_text)

    except Exception as e:
        # If anything failed, show the error and clear preview
        dpg.set_value("status", f"Error: {e}")
        dpg.show_item("status")
        dpg.set_value("preview", "")
        dpg.set_value("metadata_box", "")

def verify_loader_integrity():
    """Verifies that the MoTeCImporter can load all CSV files in the debugging_files folder."""
    
    # Reset status and display loading message
    dpg.set_value("status", "Verifying loader integrity...")
    dpg.show_item("status")
    dpg.set_value("metadata_box", "")
    dpg.set_value("preview", "")
    
    GLOBAL_FOLDER = Path(__file__).resolve().parent / "debugging_files"
    files = [str(p) for p in GLOBAL_FOLDER.rglob("*.csv")]
    
    for file in files[:-4]: # The last 4 are intentionally broken files (for testing)
        try:
            file_importer = MoTeCImporter(file)
            file_importer.import_and_validate()
        except Exception as e:
            print(f"[DEBUG] Loader integrity check failed for {file}: {e}")
            dpg.set_value("status", f"Loader integrity check failed for {file}: {e}")
            dpg.show_item("status")
            return
    
    print("[DEBUG] Loader integrity check passed for all files.")
    dpg.set_value("status", "Loader integrity check passed for all files.")

def main():
    """Main function to set up the DearPyGui interface."""
    
    # Required DearPyGui setup
    dpg.create_context()

    # Main window
    with dpg.window(label="MoTeC CSV Importer", tag="main_window"):

        with dpg.group(horizontal=True):
            # Button to open file dialog
            dpg.add_button(
                label="Select CSV file",
                callback=lambda: dpg.configure_item("file_dialog", show=True)
            )
            
            # Button to verify that the loader is working
            dpg.add_button(
                label="Verify loader integrity",
                callback=verify_loader_integrity
            )
            
        # Status line (empty at start)
        dpg.add_text("", tag="status", wrap=750, show=False)
        
        # Metadata
        dpg.add_text("Metadata")
        dpg.add_input_text(
            tag="metadata_box",
            multiline=True,
            readonly=True,
            width=750,
            height=100
        )
        
        # Data preview
        dpg.add_text("Data")
        dpg.add_input_text(
            tag="preview",
            multiline=True,
            readonly=True,
            width=750,
            height=400
        )

    # Hidden file dialog (pops up when button is pressed)
    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        callback=on_file_selected,
        tag="file_dialog",
        width=750,
        height=400
    ):
        dpg.add_file_extension(".csv", custom_text="[CSV]")
        dpg.add_file_extension(".*")  # allow all files just in case

    # Standard DearPyGui boilerplate to show the window
    dpg.create_viewport(title="MoTeC CSV Importer", width=800, height=550)
    dpg.set_exit_callback(dpg.stop_dearpygui)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("main_window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()



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