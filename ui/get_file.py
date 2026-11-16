# get_file.py
from tkinter import filedialog

files = filedialog.askopenfilenames()
for file in files:
    print(file)



