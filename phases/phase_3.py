from environment import Environment
from structures.module import Module
from structures.sweepline import SweepLine
from structures.metamodule import MetaModule
from sweep import compute_histogram_from_environment
from typing import Tuple, List

def execute_step(ui=None):
    print("Executing Step in Phase 3")
    
    env, mid = build_env_from_ui(ui)

    # --- 1) Find Sweep Line
    occupied = set(env.grid.occupied.keys())
    if not occupied:
        return set()
    
    """Extended bounding box"""
    min_x = min(x for x, _ in occupied)
    max_x = max(x for x, _ in occupied)
    min_y = min(y for _, y in occupied)
    max_y = max(y for _, y in occupied)
    sweep_line_x = max_x - 1

    metamodules: List[MetaModule] = []
    for y in range(min_y, max_y):
        if (y - min_y) % 3 == 1:
            metamodules.append(MetaModule(sweep_line_x, y, env))
            
    sweep_line = SweepLine(sweep_line_x, metamodules)

    #weep_line.full_diagnostic(env)

    sweep_line.clean(env, ui)
    sweep_line.advance(env, ui)

def execute_phase(ui=None):
    print("Executing Phase 3")
    
    env, mid = build_env_from_ui(ui)

    # --- 3) Compute histogram
    histogram = compute_histogram_from_environment(env)
    print(f"Histogram generated with {len(histogram)} cells.")

    # --- 4) Update GUI matrix
    all_positions = histogram
    min_x_pos = min(x for x, _ in all_positions)
    max_x_pos = max(x for x, _ in all_positions)
    min_y_pos = min(y for _, y in all_positions)
    max_y_pos = max(y for _, y in all_positions)

    new_rows = max_y_pos - min_y_pos + 1
    new_cols = max_x_pos - min_x_pos + 1
    new_matrix = [[0 for _ in range(new_cols)] for _ in range(new_rows)]

    for pos in histogram:
        x, y = pos
        gui_x = x - min_x_pos
        gui_y = max_y_pos - y
        new_matrix[gui_y][gui_x] = 1

    # --- 5) Update GUI
    ui.update_matrix(new_matrix)
    ui.update_phase_label("Phase 3: Histogram constructed")
    print("Phase 3 completed successfully.")

def build_env_from_ui(ui=None):
    if ui is None:
        print("No UI reference provided. Phase 3 cannot update GUI.")
        return

    # --- 1) Read matrix from UI
    matrix = ui.matrix
    rows, cols = len(matrix), len(matrix[0])

    # --- 2) Build environment
    env = Environment()
    mid = 1
    for y in range(rows):
        for x in range(cols):
            if matrix[y][x] == 1:
                grid_pos = (x, rows - 1 - y)  # convert GUI->grid
                env.add_module(Module(mid, grid_pos))
                mid += 1

    return env, mid