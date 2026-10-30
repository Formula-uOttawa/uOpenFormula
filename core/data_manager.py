import os
import pandas as pd
from pathlib import Path
import dearpygui.dearpygui as dpg
import tkinter as tk
from tkinter import filedialog
from core.log_data_manager import data_manager_log,selected_files

class DataManager:
    """Gathers data from a motec csv file.
    
    Args:
        file_path (string): file path of csv containing data.

    Returns:
        Tuple: List containing x data, followed by list containing y data.
    """

    def __init__(self):
        self.path = ""              # Path to the CSV file
        self.df = None              # DataFrame to hold the loaded data
        self.df_excl_time = None    # DataFrame excluding 'Time' column
        self.metadata = {}          # Metadata that is located at the top of the csv files
        self.channels = {}          # Channel items with their units
        self.header_index = None    # Index of the header row
    
    def import_and_validate(self, path):
        """Global method to import and validate the MoTeC CSV file."""
        
        self.path = path
        
        #TODO: error handling
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"File not found: {self.path}")
        
        self._find_header_index_and_metadata()
        self._load()
        self._validate_not_all_zero()
        self._validate_variation()

        return self.df

    def _load(self):
        """
        Loads the file, checks for errors, ignores certain 
        info (such as comments in MoTeC), saves the file
        """

        df = pd.read_csv(
            self.path, 
            skiprows=self.header_index,
            )
        #TODO: error handling
        if df.empty:
            raise ValueError("CSV loaded, no data found.")
        
        # First row after header is the units row
        units_row = df.iloc[0]
        self.channels = units_row.to_dict()

        # Drop units row from data and convert to numeric where possible
        df = df.iloc[1:].reset_index(drop=True)
        try:
            df = df.apply(pd.to_numeric)
        #TODO: error handling
        except Exception as e:
            raise ValueError(f"Error converting data to numeric: {e}")
        
        self.df = df
        self.df_excl_time = df.drop(columns=['Time'])
        print("[DEBUG] Data loaded successfully with shape:", self.df.shape)
        
    def _find_header_index_and_metadata(self):
        """Finds the index of the header row starting with 'Time'."""
                
        target = '"Time"'
        encountered = False
        metadata = {}
        
        with open(self.path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                s = line.strip()
                
                # Skip empty lines
                if not s:
                    continue
                
                while s.count('"') % 2 != 0:
                    s += '\n' + next(f).strip()
                    
                if s.startswith(target):
                    if encountered:
                        self.header_index = i
                        print(f"[DEBUG] Header row found at index: {self.header_index}")
                        break
                    encountered = True

                key, value = s.split(',', 1)
                metadata[key.strip().strip('"')] = value.strip().strip('"')
        
        if self.header_index is None:
            raise ValueError("Header row starting with 'Time' not found.")
        
        self.metadata = metadata
        print("[DEBUG] Metadata extracted:", self.metadata)

    def _validate_not_all_zero(self):
        """Validates to make sure not all numeric data is zero."""

        if self.df.empty:
            raise ValueError("No Numeric Data Found")
        print("[DEBUG] Numeric data check passed.")
        
        if self.df_excl_time.empty:
            raise ValueError("No Numeric Data Found (excluding 'Time' column)")
        print("[DEBUG] Numeric data check (excluding 'Time') passed.")

        if (self.df == 0).all().all():
            raise ValueError("All numeric values are 0.")
        print("[DEBUG] Non-zero data check passed.")
        
        if (self.df_excl_time == 0).all().all():
            raise ValueError("All numeric values are 0 (excluding 'Time' column).")
        print("[DEBUG] Non-zero data check (excluding 'Time') passed.")

    def _validate_variation(self):
        """Validates to make sure sensors aren't frozen or logs are corrupted."""

        if all(self.df[col].nunique() <= 1 for col in self.df.columns):
            raise ValueError("All sensors show no variation.")
        print("[DEBUG] Data variation check passed.")
        
        if all(self.df_excl_time[col].nunique() <= 1 for col in self.df_excl_time.columns):
            raise ValueError("All sensors show no variation (excluding 'Time' column).")
        print("[DEBUG] Data variation check (excluding 'Time') passed.")
    def select_file_tk(show_home,get_max_files,refresh_view):
        """
        Select a file using native operating system UI.
        """
        
        root = tk.Tk()
        root.withdraw()
        window_height = 100
        file_paths = filedialog.askopenfilenames()
        root.destroy()
        if not file_paths:
            return
        
                  
        dpg.delete_item("Landing Page", children_only=True)
            
        
        if not dpg.does_item_exist("import_selector"):
            dpg.delete_item("Landing Page", children_only=True)
            show_home()
        #     with dpg.window(label="Import Selector",tag="import", width=400, height=window_height):
                        
        #                 pass
            

        dpg.add_text("Import Selector", parent="import_selector")
        dpg.add_separator(parent="import_selector")
        for file_path in file_paths:
                    
                    data_manager_for_files = DataManager()
                    
                    try:
                        data_manager_for_files.import_and_validate(file_path) 
                        
                    except(FileNotFoundError,ValueError)as e:
                        
                        dpg.add_text(f"    {Path(file_path).name} ❌ ",color=(255, 100, 100),parent="import_selector")
                        continue
                    data_manager_log[file_path] = data_manager_for_files
                    dpg.add_checkbox(label=f"{Path(file_path).name} ✅",callback=DataManager.show_selected_window, user_data = (file_path, get_max_files,refresh_view), parent="import_selector")
                   
                                                
                                        
                
    def show_selected_window(checkbox, check_status,user_data):
            
            file,get_max_files,refresh_view  =user_data
            window_tag = f"window : {file}"
            if check_status:
                if not dpg.does_item_exist(window_tag):
                    if(len(selected_files)>=get_max_files()):
                        if not dpg.does_item_exist("max_error"):
                         dpg.add_text("The maximum number of files was selected",color=(255, 100, 100),parent="import_selector",tag="max_error")
                    else : 
                         if dpg.does_item_exist("max_error"):
                              dpg.delete_item("max_error")
                         
                         manager= data_manager_log[file]
                         selected_files[file] = data_manager_log[file]
                         df= manager.df
                         with dpg.window(label=Path(file).name, tag=window_tag,  width=800,height=500, no_close=True):
                                                
                                                data_array = df.to_numpy()
                                                with dpg.table(header_row=True,
                                                               policy=dpg.mvTable_SizingFixedFit,
                                                               resizable=True,
                                                               scrollX=True, scrollY=True,
                                                               borders_innerH=True, borders_outerH=True,
                                                               borders_innerV=True, borders_outerV=True):
                                                    for col in df.columns:
                                                        dpg.add_table_column(label=str(col))
                                                        
                                                    # Add Rows and Cells
                                                    for i in range(df.shape[0]):
                                                        with dpg.table_row():
                                                            for j in range(df.shape[1]):
                                                                # Each cell is of type selectable, can also be text or input_text
                                                                dpg.add_selectable(label=str(data_array[i, j]),
                                                                                   callback=lambda:None)
                else:
                  dpg.show_item(window_tag)
            else:
                 
                 selected_files.pop(file,None)
                 if dpg.does_item_exist(window_tag):
                      dpg.hide_item(window_tag)
                 if dpg.does_item_exist("max_error"):
                      dpg.delete_item("max_error")
            refresh_view()
        

def _project_root() -> Path:
    "Walks up the directory tree until it finds .git"
    cur = Path(__file__).resolve()
    # Walk upward until we find a marker that signals the project root.
    # Common markers: pyproject.toml, setup.cfg, .git
    for parent in cur.parents:
        if (parent / ".git").exists():
            return parent
    # Fallback: just use the directory that contains this file
    return cur.parent

def _test_data_manager():
    """Verifies that the class can load all CSV files in the debugging_files folder."""
    
    GLOBAL_FOLDER = _project_root() / "_debugging_files"
    files = [str(p) for p in GLOBAL_FOLDER.rglob("*.csv")]
    # TODO add check that files isnt empty
    if len(files)==0:
        raise ImportError("Debugging files not found")
    
    for file in files[:-4]: # The last 4 are intentionally broken files (for testing)
        try:
            file_importer = DataManager()
            file_importer.import_and_validate(file)
        except Exception as e:
            print(f"[DEBUG] Loader integrity check failed for {file}: {e}")
            return
    
    print("[DEBUG] Loader integrity check passed for all files.")
    

if __name__ == "__main__":
    _test_data_manager()
    

        
        
        