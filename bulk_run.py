import tkinter as tk
from dumb_ui import DumbUI
import random
from generate_inputs import generate_input

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
    for node_num in range(350, 500):
        generate_input(node_num)
        for i in range(10):
            try:
                # matrix contains the default_config as a list
                matrix_1 = random.randrange(100)
                matrix_2 = random.randrange(100)
                matrix = load_matrix_from_file('configurations/input-' + str(matrix_1) + '.txt')
                y1 = len(matrix)
                x1 = len(matrix[0])
                goal_matrix = load_matrix_from_file('configurations/input-' + str(matrix_2) + '.txt')
                y2 = len(goal_matrix)
                x2 = len(goal_matrix[0])

                perimeter = 2 * (max(x1, x2) + max(y1, y2))

                stub_matrix = load_matrix_from_file("stub_phase3_matrix.txt")
                app = DumbUI(matrix, goal_matrix)

                step_count = 0
                while app.phase_num < 4:
                    app.next_step()
                    step_count+=1
                
                successful_runs += 1
                step_counts.append([i, perimeter, step_count])
                print('step_count:', step_count)
            except:
                failed_runs += 1

        print('========================================================')
        print('successful runs:', successful_runs)
        print('failed runs', failed_runs)
        print('step counts:')


        filename = 'stats/success_rate.txt'

        saved_successful_runs += successful_runs
        saved_failed_runs += failed_runs

        with open(filename, 'a') as f:
            f.write((str(node_num) + '\t' +str(successful_runs) + '\t' + str(failed_runs) + '\n'))

        filename = 'stats/step_counts.txt'
        
        with open(filename, 'a') as f:
            for step_count in step_counts:
                f.write((str(node_num) + '\t' + str(step_count[1]) + '\t' + str(step_count[2]) + '\n'))