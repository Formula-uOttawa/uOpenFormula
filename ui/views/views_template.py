# Copy this file, DO NOT DELETE IT

# If you want to make a design for one of the analysis page's you will be doing that with this code.
# The code you write in this file will automatically be run when the menu's for the gui are created.
# Follow the instructions below and it should work, if you need more help, check power_oilstarv.py
# Don't modify this file, if you find something wrong with it or think it should be updated,
# let the team know and we will look at it together.
# A copy of the code without any of the comments can be found at the end of this file.
# Feel free to copy and paste it into your files to use.


# Name your file the same as what the second value of the node is called in home_page.py (lines 104-132)
# Example: self.nav.create_node("Oil starvation", "power_oilstarv", parent="power") 
# I would name my file ( power_oilstarv.py ) Don't include the brackets

import dearpygui.dearpygui as dpg

# Name your class as the first value of the node without the spaces and 
# add "View" to the end. Using the example from above we get OilStarvationView
class OilStarvationView: 
    
    def __init__(self, DataManager):

        # This imports all the data to self.df
        self.df = DataManager.df  

        # This gets the path for where the data is located on your pc.
        # You don't need to change this.
        self.path = DataManager.path

        # Next set any of the constants you need.
        MAX_OIL_TEMP = 48

    
    def build(self, parent_tag):
        """Called once to populate the window."""

        # The following code is just incase there is no data to load the graphs.
        # It will display a message to load a file. You only need to change the 
        # parts that say oil starvation to what you are working on.
        if self.path == "":
                     
            dpg.add_text("Oil Starvation Analysis", parent=parent_tag)
            dpg.add_separator(parent=parent_tag)
            dpg.add_text("Load a file to see data.", 
                        tag="oil_starvation_placeholder", parent=parent_tag) 
            
        else:
            self.refresh()


    # This is where you will write your actual code.
    def refresh(self):
        """Called after new data loads to update content."""

        
        # The following code deletes the text that says "load a file to see data".
        # Make sure to replace whats in side the quotes with that you names the placeholder above.
        # Example: if above I have tag = "oil_starvation_placeholder", 
        # I would change this to "oil_starvation_placeholder"
        if dpg.does_item_exist("coastdown_placeholder"):
            dpg.delete_item("coastdown_placeholder")

        # Now we need to get the data your need from self.df
        # If you want to read any of the data you will need to get the column name
        # Open one of the debugging files in excel (or where you like) 
        # and you will see it has column names such as Time or GPS Speed.
        # Use exactly that name in the code below. Debugging files can be found on the github.
        time = self.df["Time"]
        
        # This will import the time column as a pandas dataframe column but to use it for 
        # a dearpygui graph you will need to convert it to a list using .tolist()
        time = self.df["Time"].tolist()
        
        # Repeat those steps for all the data you need


        # Now we can build your analysis page. We will do this using a Child Window.
        # Tags are used to track objects that are created with dearpygui, 
        # so don't name two things the same thing. show=False is used to hide the window until somethings changes it,
        # like a button press. This is quite useful if you have multiple graphs that you want to display at diffrent times
        with dpg.child_window(tag="Rpm & Oil Pressure graph", show=False):

            # This command will allow you to start the graph, only change the label to update the graph's name
            with dpg.plot(label="Rpm & Oil Pressure", height=800, width=dpg.get_viewport_width() - 250, crosshairs=True):

                # This will allow you to create your x and Y axis, 
                # Update the tag and labels to repersent the units/data used
                dpg.add_plot_axis(dpg.mvXAxis, label="RPM")
                dpg.add_plot_axis(dpg.mvYAxis, label="Oil Pressure", tag="y_axis_rpm_vs_oil")

                # This command will allow you to actually map your data. 
                # replace the x and y with the variables holding your data lists.
                # The label should reflect what is being mapped
                # The parent must be the same as what the tag was when you created your axis above
                dpg.add_scatter_series(x=rpm, y=oil_pressure, label="Oil Pressure (Bar)", parent="y_axis_rpm_vs_oil")

                # THE END, if you need more help send a message on discord or check the DearPyGui documentation.
                # https://dearpygui.readthedocs.io/en/latest/index.html (or check the discord pinned messages)
        

# Absolute basic code needed
import dearpygui.dearpygui as dpg


class OilStarvationView: 
    
    def __init__(self, DataManager):
 
        self.df = DataManager.df  
        self.path = DataManager.path

    
    def build(self, parent_tag):
        """Called once to populate the window."""

        if self.path == "":
                     
            dpg.add_text("Oil Starvation Analysis", parent=parent_tag)
            dpg.add_separator(parent=parent_tag)
            dpg.add_text("Load a file to see data.", 
                        tag="oil_starvation_placeholder", parent=parent_tag) 
            
        else:
            self.refresh()


    def refresh(self):
        """Called after new data loads to update content."""

        if dpg.does_item_exist("coastdown_placeholder"):
            dpg.delete_item("coastdown_placeholder")


        with dpg.child_window(tag="Rpm & Oil Pressure graph", show=False):
            with dpg.plot(label="Rpm & Oil Pressure", height=800, width=dpg.get_viewport_width() - 250, crosshairs=True):

                dpg.add_plot_axis(dpg.mvXAxis, label="RPM")
                dpg.add_plot_axis(dpg.mvYAxis, label="Oil Pressure", tag="y_axis_rpm_vs_oil")
                dpg.add_scatter_series(x=rpm, y=oil_pressure, label="Oil Pressure (Bar)", parent="y_axis_rpm_vs_oil")
