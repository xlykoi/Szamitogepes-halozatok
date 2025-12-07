import tkinter as tk
from PIL import Image, ImageTk
from phases import (phase_1, phase_2, phase_3, phase_4)
from phases.phase_3 import Phase_3
from phases.phase_1 import Phase1
from phases.phase_2 import Phase2


from structures.module import Module
from typing import List

# one of the attributes of the RobotUI class is the phase_num, 
# which contains the current phase the ui (and the algorithm) is in
# and always gets incremented when the "Next Phase" button is clicked

phases_dict = {
    0: "Phase 1: Gathering squares",
    1: "Phase 2: Scaffolding",
    2: "Phase 3: Sweeping into a histogram",
    3: "Phase 4: Histograms of meta-modules",
    4: "Done"
}

class DumbUI:

    def __init__(self, matrix, goal_matrix, phase_num=0):
        self.phase_num = phase_num

        self.phase_3 = None
        self.phase_1 = None
        self.phase_2 = None
        self.sweep_done = False
        self.phase_4 = None
        self.step_num = 0

        self.matrix = matrix
        self.goal_matrix = goal_matrix
        self.labels = []

    def update_matrix(self, new_matrix):
        self.matrix = new_matrix

    def next_step(self):
        match self.phase_num:
            case 0:
                if not self.phase_1:
                    self.phase_1 = Phase1(self)
                if self.phase_1.execute_step():
                    self.phase_num += 1
            case 1:
                if not self.phase_2:
                    self.phase_2 = Phase2(self)
                if self.phase_2.execute_step():
                    self.phase_num += 1
            case 2:
                if not self.phase_3:
                    self.phase_3 = Phase_3(self)
                if not self.sweep_done:
                    self.sweep_done = self.phase_3.execute_step()
                elif self.phase_3.execute_histogram_step() == True:
                    self.phase_num += 1
            case 3:
                if not self.phase_4:
                    self.phase_4 = phase_4.Phase4(self, "configurations/001-goal.txt")
                self.phase_4.execute_step()
                if self.phase_4.is_done():
                    self.phase_num += 1
                    
    def update_phase_label(self, text):
        pass