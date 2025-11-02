import tkinter as tk
from PIL import Image, ImageTk

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

    def __init__(self, root, matrix, example_window=False, phase_num=0):
        self.root = root
        self.root.title("Sliding Squares in Parallel Demonstrator Program")

        self.phase_num = phase_num
        self.example_window = example_window

        # Title label
        self.title_label = tk.Label(root, text="Sliding Squares in Parallel", font=("Arial", 16, "bold"))
        self.title_label.grid(row=0, column=0,columnspan = 5, sticky="w", padx=5, pady=(10,10))

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
                    frame.config(bg="lightgray")

                self.labels.append(frame)

        if not self.example_window:
            # Next Phase gomb csak egyszer
            if not hasattr(self, "next_button"):
                self.next_button = tk.Button(
                    self.root, text="Next Phase", font=("Arial", 12, "bold"),
                    bg="lightgreen", command=self.next_phase
                )
                self.next_button.grid(row=len(self.matrix) + 2, column=4, columnspan=int(len(self.matrix[0])/2), pady=(5, 5))

            # Basic Moves button
            if not hasattr(self, "basic_moves_button"):
                self.basic_moves_button = tk.Button(
                    self.root, text="Basic Moves", font=("Arial", 12, "bold"),
                    bg="lightpink", command=self.show_basic_moves_window
                )
                self.basic_moves_button.grid(row=len(self.matrix) + 2, column=0, columnspan=int(len(self.matrix[0])/2), pady=(5, 5))
        else:
            if not hasattr(self, "slide_button"):
                self.slide_button = tk.Button(
                    self.root, text="Slide", font=("Arial", 12, "bold"),
                    bg="lightblue"
                )
                self.next_button.grid(row=len(self.matrix) + 2, column=4, columnspan=int(len(self.matrix[0])/3), pady=(5, 5))

            # Basic Moves button
            if not hasattr(self, "convex_transition_button"):
                self.convex_transition_button = tk.Button(
                    self.root, text="Convex Transition", font=("Arial", 12, "bold"),
                    bg="lightpink"
                )
                self.basic_moves_button.grid(row=len(self.matrix) + 2, column=0, columnspan=int(len(self.matrix[0])/3), pady=(5, 5))
            
            if not hasattr(self, "convex_transition_button"):
                self.convex_transition_button = tk.Button(
                    self.root, text="Convex Transition", font=("Arial", 12, "bold"),
                    bg="lightpink", command=self.basic_window.destroy
                )
                self.basic_moves_button.grid(row=len(self.matrix) + 2, column=0, columnspan=int(len(self.matrix[0])/3), pady=(5, 5))

        # button for calling the next phase
        next_button = tk.Button(self.root, text="Next Phase", font=("Arial", 12, "bold"), bg="lightgreen", command=self.next_phase)
        next_button.grid(row=len(self.matrix)+1, column=5, columnspan=2, pady=(5,5))

    def update_matrix(self, new_matrix):
        self.matrix = new_matrix
        self.draw_matrix()

    def update_phase_label(self, text):
        self.title_label.config(text=text)

    def next_phase(self):
        global phases_dict

        self.phase_num += 1

        match self.phase_num:
            case 1: phase_1.execute_phase(self),
            case 2: phase_2.execute_phase(self),
            case 3: phase_3.execute_phase(),
            case 4: phase_4.execute_phase(self),

        if self.phase_num in phases_dict and self.phase_num < 5:
            self.update_phase_label(phases_dict[self.phase_num])

        if self.phase_num == 5:
            self.root.quit()

        print("phase_num: " + str(self.phase_num))
        

    def show_basic_moves_window(self):
        example_matrix = load_matrix_from_file("example_config.txt")

        self.basic_window = tk.Toplevel(self.root)
        self.basic_window.title("Basic Moves")

        example_window = RobotUI(self.basic_window, example_matrix, example_window=True)

def load_matrix_from_file(filename):
    with open(filename) as f:
        lines = [line.strip() for line in f if line.strip()]
    matrix = [[int(c) for c in line] for line in lines]
    return matrix

