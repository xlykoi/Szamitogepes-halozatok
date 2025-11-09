from environment import Environment
from structures.module import Module
from structures.scaffolding import compute_scaffolding_from_env  # a Phase 2 logikája

def execute_phase(ui=None):
    print("Executing Phase 2: Building Scaffolding")

    if ui is None:
        print("No UI reference provided. Phase 2 cannot update GUI.")
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

    # --- 3) Calculate center cell
    min_x = 0
    max_x = cols - 1
    min_y = 0
    max_y = rows - 1
    center_x = (min_x + max_x) // 2
    center_y = (min_y + max_y) // 2
    center_cell = (center_x, center_y)

    # --- 4) Compute scaffolding
    scaff_cells = compute_scaffolding_from_env(env, center_cell)
    print(f"Scaffolding generated with {len(scaff_cells)} cells.")

    # --- 5) Update GUI matrix
    all_positions = scaff_cells
    min_x_pos = min(x for x, _ in all_positions)
    max_x_pos = max(x for x, _ in all_positions)
    min_y_pos = min(y for _, y in all_positions)
    max_y_pos = max(y for _, y in all_positions)

    new_rows = max_y_pos - min_y_pos + 1
    new_cols = max_x_pos - min_x_pos + 1
    new_matrix = [[0 for _ in range(new_cols)] for _ in range(new_rows)]

    for pos in scaff_cells:
        x, y = pos
        gui_x = x - min_x_pos
        gui_y = max_y_pos - y
        new_matrix[gui_y][gui_x] = 1

    # --- 6) Update GUI
    ui.update_matrix(new_matrix)
    ui.update_phase_label("Phase 2: Scaffolding Constructed")
    print("Phase 2 completed successfully.")
