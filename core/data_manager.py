from core.dataset import DataSet 
from subprocess import check_output
from sys import executable
from pathlib import Path

class DataManager:
    """Gathers data from a motec csv file.
    
    Attributes:
        datasets (dictionary): Holds all the datasets with their dataset_id's.
        update_brake_temps (func): Holds a location to a function.
        play_brake_temps (func): Holds a location to a function.
        set_brake_temp_step (func): Holds a location to a function.
        generate_disc_function (func): Holds a location to a function.
        brake_temps (List): 2D List of all brake temps.
    """


    def __init__(self, update_brake_temps, play_brake_temps, set_brake_temp_step, generate_disc_function):
        """ 
        Initalizes the Oil Starvation View.
            
        Args:
            update_brake_temps (func): Holds a location to a function.
            play_brake_temps (func): Holds a location to a function.
            set_brake_temp_step (func): Holds a location to a function.
            generate_disc_function (func): Holds a location to a function.
        """
        self.datasets = {}
        self.update_brake_temps = update_brake_temps
        self.play_brake_temps = play_brake_temps
        self.set_brake_temp_step = set_brake_temp_step
        self.generate_disc_function = generate_disc_function

    def get_file(self):
        """
        Gets the file path by calling TK Inter file menu.

        Returns:
            str: File path.
        """
        file = check_output(
            [executable, "./ui/get_file.py"],
            text=True
        )
        return file
    
    def create_dataset(self):
        """
        creates datasets and gets the path to the file.

        Returns:
            list: Returns a 2D list with [dataset_id, dataset location] for each dataset created.
        """

        path = self.get_file().splitlines()
        new_datasets = []

        for file in path:
            dataset = DataSet()
            filename = Path(file).name
            dataset.import_and_validate(file, filename)
            dataset_id = len(self.datasets)

            self.datasets[dataset_id] = dataset
            new_datasets.append((dataset_id, dataset))

        return (new_datasets)

    def get_dataset(self, dataset_id):
        """
        Recives the dataset.

        Args:
            dataset_id (int): The id of the dataset.

        Returns:
            DataSet: the dataset associated with the id.
        """
        return(self.datasets[dataset_id])

    def set_brake_temps(self, temps):
        """
        Sets brake temps. (Incomplete)
        
        Args:
            temps (List): 2D list of all brake temps.
        """
        self.brake_temps = temps

