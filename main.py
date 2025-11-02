import tkinter as tk
from ui import RobotUI

# reading config file into a list
def load_matrix_from_file(filename="default_config_copy.txt"):
    with open(filename) as f:
        lines = [line.strip() for line in f if line.strip()]
    matrix = [[int(c) for c in line] for line in lines]
    return matrix

if __name__ == "__main__":
    root = tk.Tk()

    # matrix contains the default_config as a list
    matrix = load_matrix_from_file()
    app = RobotUI(root, matrix)

    root.mainloop()
