import dearpygui.dearpygui as dpg

class RawDataView:
    
    def __init__(self, DataManager):
        self.df = DataManager.df
        

    def build(self, parent_tag):
        """Called once to populate the window."""

        if (self.df is None):
            
            dpg.add_text("Raw Data View", parent=parent_tag)
            dpg.add_separator(parent=parent_tag)
            self.refresh()
        else:
             self.refresh()

    def refresh(self):
        """Called after new data loads to update content."""
        if dpg.does_item_exist("show_data"):
                    dpg.delete_item("show_data")
        
        with dpg.child_window(tag="show_data", label="Raw Data", parent="raw_data"):
            if not self.selected_files:
                 dpg.add_text("Select a CSV file to see its raw data.")
                 return
            manager = next(iter(self.selected_files.values()))
            df = manager.df
            data_array = df.to_numpy()
            with dpg.table(header_row=True,
                policy=dpg.mvTable_SizingFixedFit,
                resizable=True,
                scrollX=True, scrollY=True,
                borders_innerH=True, borders_outerH=True,
                borders_innerV=True, borders_outerV=True,height = dpg.get_viewport_height() - 100):
                for col in df.columns:
                    dpg.add_table_column(label=str(col))
                            
                # Add Rows and Cells
                for row in data_array:
                    with dpg.table_row():
                        for value in row:
                            dpg.add_selectable(label=str(value))