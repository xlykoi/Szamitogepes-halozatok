def execute_phase(ui=None):
    print("Executing Phase 4: Histograms of Exoskeletons")

    if ui is None:
        print("No UI reference provided. Phase 4 cannot update GUI.")
        return

    # --- 1) Read matrix from UI
    matrix = ui.matrix
    rows, cols = len(matrix), len(matrix[0])