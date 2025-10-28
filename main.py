import tkinter as tk
from ui import RobotUI

def load_matrix_from_file(filename="default_config.txt"):
    with open(filename) as f:
        lines = [line.strip() for line in f if line.strip()]
    matrix = [[int(c) for c in line] for line in lines]
    return matrix

if __name__ == "__main__":
    root = tk.Tk()
    matrix = load_matrix_from_file()
    app = RobotUI(root, matrix)

    root.mainloop()
