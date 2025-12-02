import tkinter as tk
from dumb_ui import DumbUI
import random

# reading config file into a list
def load_matrix_from_file(filename="default_config_copy.txt"):
    with open(filename) as f:
        lines = [line.strip() for line in f if line.strip()]
    matrix = [[int(c) for c in line] for line in lines]
    return matrix

if __name__ == "__main__":
    root = tk.Tk()
    successful_runs = 0
    step_counts = []
    failed_runs = 0
    for i in range(10):
        try:
            # matrix contains the default_config as a list
            matrix_1 = random.randrange(100)
            matrix_2 = random.randrange(100)
            matrix = load_matrix_from_file('configurations/input-' + str(matrix_1) + '.txt')
            goal_matrix = load_matrix_from_file('configurations/input-' + str(matrix_2) + '.txt')

            stub_matrix = load_matrix_from_file("stub_phase3_matrix.txt")
            app = DumbUI(matrix, goal_matrix)

            step_count = 0
            while app.phase_num < 4:
                app.next_step()
                step_count+=1
            
            successful_runs += 1
            step_counts.append([i, step_count])
            print('step_count:', step_count)
        except:
            failed_runs += 1

    print('========================================================')
    print('successful runs:', successful_runs)
    print('step counts', step_counts)
    print('failed runs', failed_runs)
