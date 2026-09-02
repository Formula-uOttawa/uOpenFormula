import dearpygui.dearpygui as dpg

class AeroCoastdownView:
    
    def __init__(self, DataManager):
        self.df = DataManager.df

    def build(self, parent_tag):
        """Called once to populate the window."""
        dpg.add_text("Coastdown Analysis", parent=parent_tag)
        dpg.add_separator(parent=parent_tag)
        dpg.add_text("Load a file to see data.", 
                     tag="coastdown_placeholder", parent=parent_tag)
        

    def refresh(self):
        """Called after new data loads to update content."""
        if dpg.does_item_exist("coastdown_placeholder"):
            dpg.delete_item("coastdown_placeholder")
        # build your plots here using self.dm.df