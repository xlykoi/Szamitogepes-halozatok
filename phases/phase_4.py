
from environment import Environment
from structures.module import Module
from xy_monotonous_histogram import compute_xy_monotonous_histogram_from_environment

def execute_phase(ui=None):
    print("Executing Phase 4: Histograms of Metamodules")

    if ui is None:
        print("No UI reference provided. Phase 4 cannot update GUI.")
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

    # --- 3) Compute xy monotonous histogram
    histogram = compute_xy_monotonous_histogram_from_environment(env)
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
    ui.update_phase_label("Phase 4: Histograms of Metamodules constructed")
    print("Phase 4 completed successfully.")