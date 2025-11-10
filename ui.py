import tkinter as tk
from PIL import Image, ImageTk
from phases import (phase_1, phase_2, phase_3, phase_4)
from phases.phase_3 import Phase_3
from structures.module import Module
from typing import List

# one of the attributes of the RobotUI class is the phase_num, 
# which contains the current phase the ui (and the algorithm) is in
# and always gets incremented when the "Next Phase" button is clicked

phases_dict = {
    0: "Inicialization",
    1: "Phase 1: Gathering squares",
    2: "Phase 2: Scaffolding",
    3: "Phase 3: Sweeping into a histogram",
    4: "Phase 4: Histograms of meta-modules",
}

class RobotUI:

    def __init__(self, root, matrix, stub_matrix, phase_num=0):
        self.root = root
        self.root.title("Sliding Squares in Parallel Demonstrator Program")
        self.stub_matrix = stub_matrix

        self.phase_num = phase_num

        self.phase_3 = None

        # Title label
        self.title_label = tk.Label(root, text="Sliding Squares in Parallel", font=("Arial", 16, "bold"))
        self.title_label.grid(row=0, column=0,columnspan = 5, sticky="w", padx=5, pady=(10,10))

        print(f"Length of matrix: {len(matrix)} rows, {len(matrix[0])} columns ")

        self.matrix = matrix
        self.labels = []

        # Keep a reference to the robot image
        if len(self.matrix) <= 7:
            self.robot_img = ImageTk.PhotoImage(
            Image.open("./robot.png").resize((40, 40)))
        else:
            self.robot_img = ImageTk.PhotoImage(
                Image.open("./robot.png").resize((40, 40)))

        self.draw_matrix()

    def draw_matrix(self):
        # clear previous labels
        for widget in self.labels:
            widget.destroy()
        self.labels = []

        for i, row in enumerate(self.matrix):
            for j, val in enumerate(row):
                frame = tk.Frame(self.root, width=44, height=44, padx=2, pady=2, highlightbackground="black", highlightthickness=1)
                frame.grid(row=i + 1, column=j, padx=1, pady=1)
                frame.grid_propagate(False)  # fix méret

                if val == 1:
                    label = tk.Label(frame, image=self.robot_img)
                    label.image = self.robot_img
                    label.pack(expand=True, fill="both")
                else:
                    frame.config(bg="lightgray")

                self.labels.append(frame)

        # Next Phase gomb csak egyszer
        if not hasattr(self, "next_button"):
            self.next_button = tk.Button(
                self.root, text="Next Phase", font=("Arial", 12, "bold"),
                bg="lightgreen", command=self.next_phase
            )
            self.next_button.grid(row=len(self.matrix) + 2, column=4, columnspan=int(len(self.matrix[0])/2), pady=(5, 5))
        
        # Nxt Step gomb csak egyszer
        if not hasattr(self, "next_step_button"):
            self.next_step_button = tk.Button(
                self.root, text="Next Step", font=("Arial", 12, "bold"),
                bg="lightgreen", command=self.next_step
            )
            self.next_step_button.grid(row=len(self.matrix) + 2, column=1, columnspan=int(len(self.matrix[0])/2), pady=(5, 5))


    def update_matrix(self, new_matrix):
        self.matrix = new_matrix
        self.draw_matrix()

    def update_phase_label(self, text):
        self.title_label.config(text=text)

    def next_step(self):
        match self.phase_num:
            case 0:
                print('No step implemented for phase 1')
            case 1:
                print('No step implemented for phase 2')
            case 2:
                if not self.phase_3:
                    self.phase_3 = Phase_3(self)
                self.phase_3.execute_step()
            case 3:
                print('No step implemented for phase 4')
                

    def next_phase(self):
        global phases_dict

        self.phase_num += 1

        match self.phase_num:
            case 1:
                phase_1.execute_phase(self)
            case 2:
                # phase_2.execute_phase(self)
                self.update_matrix(self.stub_matrix)
                self.update_phase_label("Phase 2: Scaffolding Constructed")
                print("Phase 2 completed successfully.")
            case 3:
                if not self.phase_3:
                    self.phase_3 = Phase_3(self)
                self.phase_3.execute_phase()
            case 4:
                phase_4.execute_phase(self)

        if self.phase_num == 4:
            self.next_button.destroy()

        if self.phase_num in phases_dict and self.phase_num < 5:
            self.update_phase_label(phases_dict[self.phase_num])

        if self.phase_num == 5:
            self.root.quit()

        print("phase_num: " + str(self.phase_num))
