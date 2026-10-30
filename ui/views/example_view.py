import dearpygui.dearpygui as dpg
from core.log_data_manager import selected_files
from pathlib import Path

class ExampleView:
    max_files =2
    
    def __init__(self, DataManager):
        self.df = DataManager.df

    def build(self, parent_tag):
        """Called once to populate the window."""
        self.file_group = dpg.add_group(parent=parent_tag)
        self.refresh()

    def refresh(self):
        """Called after new data loads to update content."""
        dpg.delete_item(self.file_group, children_only=True)
        # build your plots here using self.dm.df
        if(selected_files):
                    for path, manager in selected_files.items():
                        
                        dpg.add_text(f"{Path(path).name}: {len(manager.df)} rows",parent=self.file_group)
                        
                    
        else:
                    dpg.add_text("Load a file to see data.", 
                             tag="example_placeholder", parent=self.file_group)