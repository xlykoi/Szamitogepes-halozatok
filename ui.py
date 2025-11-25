import tkinter as tk
from PIL import Image, ImageTk
from phases import (phase_1, phase_2, phase_3, phase_4)
from phases.phase_3 import Phase_3
from phases.phase_1 import Phase1


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
        self.phase_1 = None

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

        # Create scrollable frame
        self._setup_scrollable_frame()
        
        # Title label (in scrollable frame)
        self.title_label = tk.Label(self.scrollable_frame, text="Sliding Squares in Parallel", font=("Arial", 16, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=5, sticky="w", padx=5, pady=(10,10))

        self.draw_matrix()
    
    def _setup_scrollable_frame(self):
        """Set up a scrollable canvas with frame for the UI."""
        # Create main container
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas with scrollbar
        self.canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        # Configure scrollbar
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas for the scrollable frame
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure canvas scrolling
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Update canvas width when window is resized
        def configure_canvas_width(event):
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.canvas.bind('<Configure>', configure_canvas_width)

    def draw_matrix(self):
        # clear previous labels
        for widget in self.labels:
            widget.destroy()
        self.labels = []

        # --- MÁTRIX ÚJRA ÉPÍTÉSE ---
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

        # Next Phase gomb
        if not hasattr(self, "next_button"):
            self.next_button = tk.Button(
                self.scrollable_frame, text="Next Phase", font=("Arial", 12, "bold"),
                bg="lightgreen", command=self.next_phase
            )
        # EZ A SOR MOZGATJA A GOMBOT az új mátrix alá
        self.next_button.grid(row=matrix_rows + 2, column=matrix_cols - 1, columnspan=1, pady=(5, 5), sticky="e")
        
        # Nxt Step gomb
        if not hasattr(self, "next_step_button"):
            self.next_step_button = tk.Button(
                self.scrollable_frame, text="Next Step", font=("Arial", 12, "bold"),
                bg="lightgreen", command=self.next_step
            )
        # EZ A SOR MOZGATJA A GOMBOT az új mátrix alá
        self.next_step_button.grid(row=matrix_rows + 2, column=0, columnspan=1, pady=(5, 5), sticky="w")
        
        # Update scroll region after drawing
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
                self.phase_1.execute_step()

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
                if not self.phase_1:
                    self.phase_1 = Phase1(self)
                self.phase_1.execute_phase()
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
