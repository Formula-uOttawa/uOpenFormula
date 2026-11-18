import dearpygui.dearpygui as dpg


class DataFilesView:
    """
    View for Imported DataSets.

    Atributes:
        data_manager (DataManager): Location to DataManager.
    """
    
    def __init__(self, DataManager):
        """ 
        Initalizes the DataFiles View.
        
        Args:
            DataManager (DataManager): Location to DataManager.
        """
        self.data_manager = DataManager

    def build(self, parent_tag):
        """
        Called once to populate the window.

        Args:
            parent_tag (String): tag of the DataFiles view window.
        """
        
        if (self.data_manager.datasets == {}):
            
            dpg.add_text("Raw Data View", parent=parent_tag)
            dpg.add_separator(parent=parent_tag)
            dpg.add_text("Load a file to see data.", 
                     tag="raw_data_placeholder", parent=parent_tag)
        else:
             self.refresh()

    def refresh(self):
        """
        Called after new data loads to update content.
        """

        if dpg.does_item_exist("show_data"):
                    dpg.delete_item("show_data")
    
             
        for dataset_id, dataset in self.data_manager.datasets.items():
            self.add_file(dataset_id, dataset)

    def add_file(self, dataset_id , dataset):
        """
        Adds a file to the window.

        Args:
            dataset_id (String): The id of the dataset.
            dataset (DataSet): The dataset associated with the dataset_id.
        """
        with dpg.child_window(tag=f"{dataset_id}_showdata_window",
                              parent="datamanager_view", 
                              auto_resize_y=True, 
                              autosize_x = True, 
                              border=False,
                              always_use_window_padding=True
                              ):
            
            with dpg.collapsing_header(tag=f"{dataset_id}_showdata_text", label=dataset.name,parent=f"{dataset_id}_showdata_window"):
                dpg.add_separator()
                dpg.add_text("Dataset information")

    def table(self):
        """
        Builds the dataset table. incomplete.
        """
        data_array = self.df.to_numpy()
        with dpg.table(header_row=True,
                        policy=dpg.mvTable_SizingFixedFit,
                        resizable=True,
                        scrollX=True, scrollY=True,
                        borders_innerH=True, borders_outerH=True,
                        borders_innerV=True, borders_outerV=True,height = dpg.get_viewport_height() - 100
                       ): 
            
            for col in self.df.columns:
                dpg.add_table_column(label=str(col))
                            
                # Add Rows and Cells
                for i in range(self.df.shape[0]):
                    with dpg.table_row():
                        for j in range(self.df.shape[1]):
                            # Each cell is of type selectable, can also be text or input_text
                            dpg.add_selectable( label=str(data_array[i, j]),
                                                callback=lambda:None)