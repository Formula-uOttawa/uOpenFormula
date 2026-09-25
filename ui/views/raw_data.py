import dearpygui.dearpygui as dpg

class RawDataView:
    
    def __init__(self, DataManager):
        self.df = DataManager.df
        

    def build(self, parent_tag):
        """Called once to populate the window."""

        if (self.df is None):
            
            dpg.add_text("Raw Data View", parent=parent_tag)
            dpg.add_separator(parent=parent_tag)
            dpg.add_text("Load a file to see data.", 
                     tag="raw_data_placeholder", parent=parent_tag)
        else:
             self.refresh()

    def refresh(self):
        """Called after new data loads to update content."""
        if dpg.does_item_exist("show_data"):
                    dpg.delete_item("show_data")
        
        with dpg.child_window(tag="show_data", label="Raw Data",):
            data_array = self.df.to_numpy()
            with dpg.table(header_row=True,
                policy=dpg.mvTable_SizingFixedFit,
                resizable=True,
                scrollX=True, scrollY=True,
                borders_innerH=True, borders_outerH=True,
                borders_innerV=True, borders_outerV=True):
                for col in self.df.columns:
                    dpg.add_table_column(label=str(col))
                            
                # Add Rows and Cells
                for i in range(self.df.shape[0]):
                    with dpg.table_row():
                        for j in range(self.df.shape[1]):
                            # Each cell is of type selectable, can also be text or input_text
                            dpg.add_selectable( label=str(data_array[i, j]),
                                                callback=lambda:None)