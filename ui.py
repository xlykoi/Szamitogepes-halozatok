import tkinter as tk
from PIL import Image, ImageTk
from phases import (phase_1, phase_2, phase_3, phase_4)
from phases.phase_3 import Phase_3
from phases.phase_1 import Phase1
from phases.phase_2 import Phase2


from structures.module import Module
from typing import List


phases_dict = {
    0: "Phase 1: Gathering squares",
    1: "Phase 2: Scaffolding",
    2: "Phase 3: Sweeping into a histogram",
    3: "Phase 4: Histograms of meta-modules",
    4: "Done"
}

class RobotUI:

    def __init__(self, root, matrix, stub_matrix, goal_matrix, phase_num=0):
        self.root = root
        self.root.title("Sliding Squares in Parallel Demonstrator Program")
        self.stub_matrix = stub_matrix

        self.phase_num = phase_num

        self.phase_3 = None
        self.phase_1 = None
        self.phase_2 = None
        self.sweep_done = False
        self.phase_4 = None

        print(f"Length of matrix: {len(matrix)} rows, {len(matrix[0])} columns ")

        self.matrix = matrix
        self.goal_matrix = goal_matrix
        self.labels = []

        if len(self.matrix) <= 7:
            self.robot_img = ImageTk.PhotoImage(
            Image.open("./robot.png").resize((40, 40)))
        else:
            self.robot_img = ImageTk.PhotoImage(
                Image.open("./robot.png").resize((40, 40)))

        self._setup_scrollable_frame()
        
        self.title_label = tk.Label(self.scrollable_frame, text="Sliding Squares in Parallel", font=("Arial", 16, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=5, sticky="w", padx=5, pady=(10,10))

        self.draw_matrix()
    
    def _setup_scrollable_frame(self):
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def configure_canvas_width(event):
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.canvas.bind('<Configure>', configure_canvas_width)

    def draw_matrix(self):
        for widget in self.labels:
            widget.destroy()
        self.labels = []

        for i, row in enumerate(self.matrix):
            for j, val in enumerate(row):
                frame = tk.Frame(self.scrollable_frame, width=44, height=44, padx=2, pady=2, highlightbackground="black", highlightthickness=1)
                frame.grid(row=i + 1, column=j, padx=1, pady=1)
                frame.grid_propagate(False)  # fix méret

                if val == 1:
                    label = tk.Label(frame, image=self.robot_img)
                    label.image = self.robot_img
                    label.pack(expand=True, fill="both")
                else:
                    frame.config(bg="lightgray")

                self.labels.append(frame)

        matrix_rows = len(self.matrix)
        matrix_cols = len(self.matrix[0]) if matrix_rows > 0 else 0

        phase_4_done = (self.phase_num == 4 or 
                       (self.phase_4 is not None and self.phase_4.is_done()))

        if phase_4_done:
            if hasattr(self, "next_step_button"):
                self.next_step_button.grid_remove()
            
            if not hasattr(self, "exit_button"):
                self.exit_button = tk.Button(
                    self.scrollable_frame, text="Exit", font=("Arial", 12, "bold"),
                    bg="lightcoral", command=self.root.quit
                )
            self.exit_button.grid(row=matrix_rows + 2, column=0, columnspan=1, pady=(5, 5), sticky="w")
        else:
            if hasattr(self, "exit_button"):
                self.exit_button.grid_remove()
            
            if not hasattr(self, "next_step_button"):
                self.next_step_button = tk.Button(
                    self.scrollable_frame, text="Next Step", font=("Arial", 12, "bold"),
                    bg="lightgreen", command=self.next_step
                )
            self.next_step_button.grid(row=matrix_rows + 2, column=0, columnspan=1, pady=(5, 5), sticky="w")
        
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def update_matrix(self, new_matrix):
        self.matrix = new_matrix
        self.draw_matrix()

    def update_phase_label(self, text):
        self.title_label.config(text=text)

    def next_step(self):
        match self.phase_num:
            case 0:
                if not self.phase_1:
                    self.phase_1 = Phase1(self)
                    self.update_phase_label(phases_dict[0])
                if self.phase_1.execute_step():
                    self.phase_num += 1
                    if self.phase_num in phases_dict:
                        self.update_phase_label(phases_dict[self.phase_num])
            case 1:
                if not self.phase_2:
                    self.phase_2 = Phase2(self)
                if self.phase_2.execute_step():
                    self.phase_num += 1
                    if self.phase_num in phases_dict:
                        self.update_phase_label(phases_dict[self.phase_num])
            case 2:
                if not self.phase_3:
                    self.phase_3 = Phase_3(self)
                if not self.sweep_done:
                    self.sweep_done = self.phase_3.execute_step()
                elif self.phase_3.execute_histogram_step() == True:
                    self.phase_num += 1
                    if self.phase_num in phases_dict:
                        self.update_phase_label(phases_dict[self.phase_num])
            case 3:
                if not self.phase_4:
                    self.phase_4 = phase_4.Phase4(self, "configurations/001-goal.txt")
                self.phase_4.execute_step()
                if self.phase_4.is_done():
                    self.phase_num += 1
                    if self.phase_num in phases_dict:
                        self.update_phase_label(phases_dict[self.phase_num])
                    self.draw_matrix()
