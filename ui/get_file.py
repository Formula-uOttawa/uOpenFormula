# get_file.py
from tkinter import filedialog

file = filedialog.askopenfilename()
print(file, end="")