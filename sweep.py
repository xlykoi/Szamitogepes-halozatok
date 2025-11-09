from environment import Environment

def compute_histogram_from_environment(env: Environment) -> dict:
    """
    Phase 3: Build histogram structure on the west side of the extended bounding box.
    Updates env.grid.occupied.
    """
    occupied = set(env.grid.occupied.keys())
    if not occupied:
        return set()
    
    """Extended bounding box"""
    min_x = min(x for x, _ in occupied)
    max_x = max(x for x, _ in occupied)
    min_y = min(y for _, y in occupied)
    max_y = max(y for _, y in occupied)
    # Align (max_y - min_y) to multiple of 3
    if (max_y - min_y + 1) % 3 != 0:
        max_y += 3 - ((max_y - min_y + 1) % 3)
    total_mods = len(occupied)
    
    """Sweep line on the west side"""
    sweep_line_x = min_x + 1
    sweep_line_left = {(sweep_line_x - 1, y) for y in range(min_y, max_y + 1)}
    sweep_line_middle = {(sweep_line_x, y) for y in range(min_y, max_y + 1) if y % 3 != 1}
    sweep_line_right = {(sweep_line_x + 1, y) for y in range(min_y, max_y + 1)}

    sweep_line = sweep_line_left.union(sweep_line_middle).union(sweep_line_right)
    
    histogram = set(sweep_line)

    """Check for strips with missing modules"""
    strip_range = int((max_y - min_y + 1) / 3)
    missing_modules = dict()
    for eastern_strip in range(strip_range):
        """Count the modules in each strip"""
        module_count = 0
        for row in range(3):  
            for col in range(min_x, max_x + 1):
                pos = (col + min_x, min_y + eastern_strip * 3 + row)
                if pos in occupied:
                    module_count += 1
        
        """Subtract module cost of the meta module in the strip, and any missing modules from previous strip"""
        module_count -= 8

        """In case of missing modules, record them"""
        missing_modules[eastern_strip]= -module_count

    """If there are too few modules for the histogram, return with current histogram, and an error"""
    total_missing = sum(v for v in missing_modules.values())
    if total_missing > 0:
        print("Error: Not enough modules to build full histogram.")
        return
    print(missing_modules)
    """Adjust histogram to account for missing modules"""
    for eastern_strip in range(strip_range):
        if missing_modules[eastern_strip] > 0 and eastern_strip + 1 in missing_modules.keys():
            missing_modules[eastern_strip + 1] += missing_modules[eastern_strip]
            missing_modules[eastern_strip] = 0
                
    for eastern_strip in reversed(range(strip_range)):
        if missing_modules[eastern_strip] > 0 and eastern_strip - 1 in missing_modules.keys():
            missing_modules[eastern_strip - 1] += missing_modules[eastern_strip]
            missing_modules[eastern_strip] = 0

    """Fill histogram"""
    for eastern_strip in range(strip_range):
        modules_to_place = -missing_modules[eastern_strip]
        current_x = min_x + 3
        current_y = min_y + eastern_strip * 3
        while modules_to_place > 0:
            histogram.add((current_x, current_y))
            if current_y % 3 != 2:
                current_y += 1
            else:
                current_x += 1
                current_y -= 2
            modules_to_place -= 1
    return histogram