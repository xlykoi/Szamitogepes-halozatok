from typing import Set, Tuple, List, Optional
from environment import Environment

Pos = Tuple[int, int]


def _calculate_bounding_box_with_alignment(occupied: Set[Pos]) -> Tuple[int, int, int, int]:
    """Calculate bounding box and align height to multiple of 3."""
    min_x = min(x for x, _ in occupied)
    max_x = max(x for x, _ in occupied)
    min_y = min(y for _, y in occupied)
    max_y = max(y for _, y in occupied)
    
    # Align height to multiple of 3 (required for scaffolding structure)
    height = max_y - min_y + 1
    if height % 3 != 0:
        max_y += 3 - (height % 3)
    
    return (min_x, max_x, min_y, max_y)


def _get_center_of_mass(occupied: Set[Pos]) -> Tuple[float, float]:
    """Calculate center of mass of occupied positions."""
    if not occupied:
        return (0.0, 0.0)
    total_mods = len(occupied)
    cx = sum(x for x, _ in occupied) / total_mods
    cy = sum(y for _, y in occupied) / total_mods
    return (cx, cy)


def _build_vertical_column(rightmost_x: int, min_y: int, max_y: int) -> Set[Pos]:
    """Build vertical column on the rightmost x coordinate."""
    return {(rightmost_x, y) for y in range(min_y, max_y + 1)}


def _trim_vertical_column(vertical_column: Set[Pos], total_mods: int, cy: float) -> Set[Pos]:
    """Trim vertical column to total_mods, keeping cells closest to center y."""
    if len(vertical_column) <= total_mods:
        return vertical_column
    
    vertical_sorted = sorted(
        vertical_column,
        key=lambda p: abs(p[1] - cy)
    )
    return set(vertical_sorted[:total_mods])


def _generate_horizontal_candidates(min_x: int, max_x: int, min_y: int, max_y: int,
                                    exclude: Set[Pos]) -> List[Pos]:
    """Generate candidate positions for horizontal base (excluding vertical column)."""
    return [
        (x, y)
        for x in range(min_x, max_x)
        for y in range(min_y, max_y + 1)
        if (x, y) not in exclude
    ]


def _generate_extended_candidates(min_x: int, max_x: int, min_y: int, max_y: int,
                                  exclude: Set[Pos], central_cell: Pos) -> List[Pos]:
    """Generate extended candidates outside the bounding box."""
    return [
        (x, y)
        for x in range(min_x - 1, max_x + 2)
        for y in range(min_y - 1, max_y + 2)
        if (x, y) not in exclude and (x, y) != central_cell
    ]


def _add_candidates_sorted(scaff: Set[Pos], candidates: List[Pos], 
                          total_mods: int, cx: float, cy: float) -> Set[Pos]:
    """Add candidates to scaffolding, sorted by distance to center of mass."""
    candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
    for c in candidates:
        if len(scaff) >= total_mods:
            break
        scaff.add(c)
    return scaff


def _fill_horizontal_base(scaff: Set[Pos], min_x: int, max_x: int, 
                          min_y: int, max_y: int, total_mods: int,
                          cx: float, cy: float) -> Set[Pos]:
    """Fill remaining modules to form horizontal base (L shape)."""
    if len(scaff) >= total_mods:
        return scaff
    
    candidates = _generate_horizontal_candidates(min_x, max_x, min_y, max_y, scaff)
    return _add_candidates_sorted(scaff, candidates, total_mods, cx, cy)


def _ensure_central_cell_empty(scaff: Set[Pos], central_cell: Pos,
                               min_x: int, max_x: int, min_y: int, max_y: int,
                               total_mods: int, cx: float, cy: float) -> Set[Pos]:
    """Ensure central cell is empty and add replacement if needed."""
    central_was_in_scaff = central_cell in scaff
    scaff.discard(central_cell)
    
    if central_was_in_scaff and len(scaff) < total_mods:
        extended_candidates = _generate_extended_candidates(
            min_x, max_x, min_y, max_y, scaff, central_cell
        )
        scaff = _add_candidates_sorted(scaff, extended_candidates, total_mods, cx, cy)
    
    return scaff


def _trim_scaffolding_if_needed(scaff: Set[Pos], vertical_column: Set[Pos],
                                total_mods: int, cx: float, cy: float) -> Set[Pos]:
    """Trim scaffolding if too many cells, keeping vertical column when possible."""
    if len(scaff) <= total_mods:
        return scaff
    
    horizontal_cells = scaff - vertical_column
    
    if len(horizontal_cells) > (total_mods - len(vertical_column)):
        # Trim from horizontal base
        horizontal_sorted = sorted(
            horizontal_cells,
            key=lambda p: abs(p[0] - cx) + abs(p[1] - cy)
        )
        needed_horizontal = total_mods - len(vertical_column)
        return vertical_column | set(horizontal_sorted[:needed_horizontal])
    else:
        # Trim from vertical column
        vertical_sorted = sorted(
            vertical_column,
            key=lambda p: abs(p[1] - cy)
        )
        needed_vertical = total_mods - len(horizontal_cells)
        return set(vertical_sorted[:needed_vertical]) | horizontal_cells


def _calculate_scaffolding_center(scaff: Set[Pos]) -> Optional[Pos]:
    """Calculate center cell of scaffolding."""
    if not scaff:
        return None
    scaff_min_x = min(x for x, _ in scaff)
    scaff_max_x = max(x for x, _ in scaff)
    scaff_min_y = min(y for _, y in scaff)
    scaff_max_y = max(y for _, y in scaff)
    scaff_center_x = (scaff_min_x + scaff_max_x) // 2
    scaff_center_y = (scaff_min_y + scaff_max_y) // 2
    return (scaff_center_x, scaff_center_y)


def _ensure_scaffolding_center_empty(scaff: Set[Pos], total_mods: int,
                                    cx: float, cy: float) -> Set[Pos]:
    """Ensure scaffolding center is empty and add replacement if needed."""
    scaff_center = _calculate_scaffolding_center(scaff)
    if not scaff_center or scaff_center not in scaff:
        return scaff
    
    scaff.discard(scaff_center)
    
    if len(scaff) < total_mods:
        scaff_min_x = min(x for x, _ in scaff)
        scaff_max_x = max(x for x, _ in scaff)
        scaff_min_y = min(y for _, y in scaff)
        scaff_max_y = max(y for _, y in scaff)
        
        replacement_candidates = [
            (x, y)
            for x in range(scaff_min_x - 1, scaff_max_x + 2)
            for y in range(scaff_min_y - 1, scaff_max_y + 2)
            if (x, y) not in scaff and (x, y) != scaff_center
        ]
        scaff = _add_candidates_sorted(scaff, replacement_candidates, total_mods, cx, cy)
    
    return scaff


def _finalize_scaffolding_count(scaff: Set[Pos], min_x: int, max_x: int,
                               min_y: int, max_y: int, total_mods: int,
                               central_cell: Pos, cx: float, cy: float) -> Set[Pos]:
    """Final verification: ensure exact module count."""
    if len(scaff) == total_mods:
        return scaff
    
    if len(scaff) > total_mods:
        # Trim excess
        scaff_list = sorted(scaff, key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
        return set(scaff_list[:total_mods])
    else:
        # Add missing cells
        all_candidates = [
            (x, y)
            for x in range(min_x - 2, max_x + 3)
            for y in range(min_y - 2, max_y + 3)
            if (x, y) not in scaff and (x, y) != central_cell
        ]
        return _add_candidates_sorted(scaff, all_candidates, total_mods, cx, cy)


def _update_environment(env: Environment, scaff: Set[Pos]) -> None:
    """Update environment grid with scaffolding positions."""
    env.grid.occupied.clear()
    for pos in scaff:
        env.grid.occupied[pos] = True


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

    # Calculate bounding box with alignment
    min_x, max_x, min_y, max_y = _calculate_bounding_box_with_alignment(occupied)
    total_mods = len(occupied)
    
    # Calculate center of mass
    cx, cy = _get_center_of_mass(occupied)
    
    # Build vertical column
    rightmost_x = max_x
    vertical_column = _build_vertical_column(rightmost_x, min_y, max_y)
    vertical_column = _trim_vertical_column(vertical_column, total_mods, cy)
    
    # Start with vertical column
    scaff = set(vertical_column)
    
    # Fill horizontal base to form L-shape
    scaff = _fill_horizontal_base(scaff, min_x, max_x, min_y, max_y, total_mods, cx, cy)
    
    # Ensure central cell is empty
    scaff = _ensure_central_cell_empty(scaff, central_cell, min_x, max_x, min_y, max_y,
                                       total_mods, cx, cy)
    
    # Trim if too many cells
    scaff = _trim_scaffolding_if_needed(scaff, vertical_column, total_mods, cx, cy)
    
    # Ensure scaffolding center is empty
    scaff = _ensure_scaffolding_center_empty(scaff, total_mods, cx, cy)
    
    # Final verification
    scaff = _finalize_scaffolding_count(scaff, min_x, max_x, min_y, max_y, total_mods,
                                       central_cell, cx, cy)
    
    # Update environment
    _update_environment(env, scaff)
    
    return scaff

