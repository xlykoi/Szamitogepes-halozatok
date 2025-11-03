from typing import Set, Tuple
from environment import Environment

Pos = Tuple[int, int]

def compute_scaffolding_from_env(env: Environment, central_cell: Pos) -> Set[Pos]:
    """
    Phase 2: Build scaffolding from exoskeleton.
    Moves modules into an 'L' shape, preserving module count.
    Central cell remains empty for movement.
    Updates env.grid.occupied.
    
    Based on "Sliding Squares in Parallel" - creates an L-shaped scaffolding
    structure to facilitate parallel reconfiguration.
    """
    occupied = set(env.grid.occupied.keys())
    if not occupied:
        return set()

    # Bounding box
    min_x = min(x for x, _ in occupied)
    max_x = max(x for x, _ in occupied)
    min_y = min(y for _, y in occupied)
    max_y = max(y for _, y in occupied)
    # Align height to multiple of 3 (required for scaffolding structure)
    height = max_y - min_y + 1
    if height % 3 != 0:
        max_y += 3 - (height % 3)
    total_mods = len(occupied)

    # Build L-shaped scaffolding:
    # 1. Vertical column on the rightmost x coordinate
    # 2. Horizontal base filling remaining modules
    
    rightmost_x = max_x
    
    # Start with vertical column (rightmost column)
    vertical_column = {(rightmost_x, y) for y in range(min_y, max_y + 1)}
    
    # Calculate center of mass for candidate selection
    cx = sum(x for x, _ in occupied) / total_mods
    cy = sum(y for _, y in occupied) / total_mods
    
    # If vertical column alone is larger than total_mods, use only a subset
    if len(vertical_column) > total_mods:
        # Use vertical cells closest to center y
        vertical_sorted = sorted(
            vertical_column,
            key=lambda p: abs(p[1] - cy)
        )
        vertical_column = set(vertical_sorted[:total_mods])
    
    scaff = set(vertical_column)

    # Fill remaining modules to form horizontal base (L shape) if needed
    if len(scaff) < total_mods:
        # Candidates: everything inside bounding box except vertical column
        candidates = [
            (x, y)
            for x in range(min_x, max_x)
            for y in range(min_y, max_y + 1)
            if (x, y) not in scaff
        ]
        # Sort by distance to center of mass (prefer cells closer to original position)
        candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))

        # Add candidates until we have total_mods cells
        for c in candidates:
            if len(scaff) >= total_mods:
                break
            scaff.add(c)

    # Ensure central cell is empty (must remain free for movement)
    central_was_in_scaff = central_cell in scaff
    scaff.discard(central_cell)
    
    # If we removed the central cell, we need to add one more cell to maintain module count
    if central_was_in_scaff and len(scaff) < total_mods:
        # Find additional candidates outside the bounding box if needed
        extended_candidates = [
            (x, y)
            for x in range(min_x - 1, max_x + 2)
            for y in range(min_y - 1, max_y + 2)
            if (x, y) not in scaff and (x, y) != central_cell
        ]
        extended_candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
        for c in extended_candidates:
            if len(scaff) >= total_mods:
                break
            scaff.add(c)
    
    # Final check: if we have too many cells, trim from candidates that were added last
    if len(scaff) > total_mods:
        # Keep vertical column and trim excess from horizontal base
        horizontal_cells = scaff - vertical_column
        if len(horizontal_cells) > (total_mods - len(vertical_column)):
            # Sort horizontal cells by distance to center, keep closest ones
            horizontal_sorted = sorted(
                horizontal_cells,
                key=lambda p: abs(p[0] - cx) + abs(p[1] - cy)
            )
            needed_horizontal = total_mods - len(vertical_column)
            scaff = vertical_column | set(horizontal_sorted[:needed_horizontal])
        else:
            # Need to trim from vertical column if it's too large
            vertical_sorted = sorted(
                vertical_column,
                key=lambda p: abs(p[1] - cy)  # Keep vertical cells closest to center y
            )
            needed_vertical = total_mods - len(horizontal_cells)
            scaff = set(vertical_sorted[:needed_vertical]) | horizontal_cells
    
    # Recalculate center of scaffolding and ensure it's empty
    if scaff:
        scaff_min_x = min(x for x, _ in scaff)
        scaff_max_x = max(x for x, _ in scaff)
        scaff_min_y = min(y for _, y in scaff)
        scaff_max_y = max(y for _, y in scaff)
        scaff_center_x = (scaff_min_x + scaff_max_x) // 2
        scaff_center_y = (scaff_min_y + scaff_max_y) // 2
        scaff_center = (scaff_center_x, scaff_center_y)
        
        # Ensure scaffolding center is empty
        if scaff_center in scaff:
            scaff.discard(scaff_center)
            # Add replacement cell if needed
            if len(scaff) < total_mods:
                replacement_candidates = [
                    (x, y)
                    for x in range(scaff_min_x - 1, scaff_max_x + 2)
                    for y in range(scaff_min_y - 1, scaff_max_y + 2)
                    if (x, y) not in scaff and (x, y) != scaff_center
                ]
                replacement_candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
                for c in replacement_candidates:
                    if len(scaff) >= total_mods:
                        break
                    scaff.add(c)
    
    # Final verification: exact module count
    if len(scaff) != total_mods:
        # Emergency adjustment: trim or add to reach exact count
        if len(scaff) > total_mods:
            scaff_list = sorted(scaff, key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
            scaff = set(scaff_list[:total_mods])
        elif len(scaff) < total_mods:
            # This shouldn't happen, but add cells if needed
            all_candidates = [
                (x, y)
                for x in range(min_x - 2, max_x + 3)
                for y in range(min_y - 2, max_y + 3)
                if (x, y) not in scaff and (x, y) != central_cell
            ]
            all_candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
            for c in all_candidates:
                if len(scaff) >= total_mods:
                    break
                scaff.add(c)

    # Update environment
    env.grid.occupied.clear()
    for pos in scaff:
        env.grid.occupied[pos] = True

    return scaff
