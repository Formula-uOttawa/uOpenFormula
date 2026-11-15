from core.dataset import DataSet 
from subprocess import check_output
from sys import executable

class DataManager:
    """Gathers data from a motec csv file.
    
    Args:
        file_path (string): file path of csv containing data.

    Returns:
        Tuple: List containing x data, followed by list containing y data.
    """


    def __init__(self, update_brake_temps, play_brake_temps, set_brake_temp_step, generate_disc_function):
        self.datasets = {}
        self.update_brake_temps = update_brake_temps
        self.play_brake_temps = play_brake_temps
        self.set_brake_temp_step = set_brake_temp_step
        self.generate_disc_function = generate_disc_function


    def get_file(self):
        file = check_output(
            [executable, "./ui/get_file.py"],
            text=True
        )
        return file


    def create_dataset(self):
        dataset = DataSet()
        path = self.get_file()
        dataset.import_and_validate(path)
        dataset_id = len(self.datasets)

        self.datasets[dataset_id] = dataset


    def get_dataset(self, dataset_id):
        return(self.datasets[dataset_id])


    def set_brake_temps(self, temps):
        self.brake_temps = temps

