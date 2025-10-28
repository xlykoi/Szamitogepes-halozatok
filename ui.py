import tkinter as tk
from PIL import Image, ImageTk

class RobotUI:

    def __init__(self, root, matrix):
        self.root = root
        self.root.title("Robot Matrix")

        # Keep a reference to the robot image
        self.robot_img = ImageTk.PhotoImage(
            Image.open("./robot.png").resize((40, 40))
        )

        self.matrix = matrix
        self.labels = []

        self.draw_matrix()

    def draw_matrix(self):
        # clear previous labels
        for widget in self.labels:
            widget.destroy()
        self.labels = []

        for i, row in enumerate(self.matrix):
            for j, val in enumerate(row):
                if val == 1:
                    label = tk.Label(self.root, image=self.robot_img, width=50, height=50)
                    label.image = self.robot_img  # keep reference
                else:
                    label = tk.Label(self.root, bg="lightgray", width=5, height=3)
                label.grid(row=i, column=j, padx=2, pady=2)
                self.labels.append(label)

    def update_matrix(self, new_matrix):
        self.matrix = new_matrix
        self.draw_matrix()

