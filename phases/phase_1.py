from environment import Environment
from module import Module
from skeleton import compute_exoskeleton_from_env

def execute_phase(ui=None):
    print("Executing Phase 1: Building Exoskeleton")

    if ui is None:
        print("No UI reference provided. Phase 1 cannot update GUI.")
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

    # --- 3) Compute exoskeleton
    exo_cells = compute_exoskeleton_from_env(env)
    print(f"Exoskeleton generated with {len(exo_cells)} cells.")

    # --- 4) Update GUI matrix
    all_positions = exo_cells
    min_x = min(x for x, _ in all_positions)
    max_x = max(x for x, _ in all_positions)
    min_y = min(y for _, y in all_positions)
    max_y = max(y for _, y in all_positions)

    new_rows = max_y - min_y + 1
    new_cols = max_x - min_x + 1
    new_matrix = [[0 for _ in range(new_cols)] for _ in range(new_rows)]

    for pos in exo_cells:
        x, y = pos
        gui_x = x - min_x
        gui_y = max_y - y
        new_matrix[gui_y][gui_x] = 1

    # --- 5) Update GUI
    ui.update_matrix(new_matrix)
    ui.update_phase_label("Phase 1: Exoskeleton Constructed")
    print("Phase 1 completed successfully.")
