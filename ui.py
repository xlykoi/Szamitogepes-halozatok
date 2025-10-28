import tkinter as tk
from PIL import Image, ImageTk

def load_matrix_from_file(filename="default_config.txt"):
    with open(filename) as f:
        lines = [line.strip() for line in f if line.strip()]
    matrix = [[int(c) for c in line] for line in lines]
    return matrix

def draw_matrix(matrix):
    root = tk.Tk()
    root.title("Robot Mátrix")

    # Load and keep a reference to the image
    img = ImageTk.PhotoImage(Image.open("./robot.png").resize((40, 40)))

    labels = []  # to keep references to image labels

    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            if val == 1:
                label = tk.Label(root, image=img, width=50, height=50)
                label.image = img  # keep a reference!
            else:
                label = tk.Label(root, text="", bg="lightgray", width=5, height=3)
            label.grid(row=i, column=j, padx=2, pady=2)
            labels.append(label)  # store to prevent garbage collection

    root.mainloop()

if __name__ == "__main__":
    matrix = load_matrix_from_file()
    draw_matrix(matrix)
