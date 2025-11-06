from typing import Set, Tuple, List, Optional
from collections import deque
from environment import Environment

Pos = Tuple[int, int]


def neighbors4_unbounded(p: Pos):
    """Return 4-connected neighbors without bounds checking."""
    x, y = p
    return [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]


def is_connected(positions: Set[Pos]) -> bool:
    """
    Check if a set of positions forms a connected component via 4-connectivity.
    Returns True if all positions are reachable from each other.
    """
    if not positions:
        return True
    if len(positions) == 1:
        return True
    
    # BFS from first position
    start = next(iter(positions))
    visited = {start}
    q = deque([start])
    
    while q:
        current = q.popleft()
        for neighbor in neighbors4_unbounded(current):
            if neighbor in positions and neighbor not in visited:
                visited.add(neighbor)
                q.append(neighbor)
    
    # If we visited all positions, it's connected
    return len(visited) == len(positions)


def _find_connected_components(positions: Set[Pos]) -> List[Set[Pos]]:
    """Find all connected components in a set of positions."""
    components = []
    remaining = positions.copy()
    
    while remaining:
        start = next(iter(remaining))
        component = set()
        q = deque([start])
        visited = {start}
        
        while q:
            current = q.popleft()
            component.add(current)
            remaining.discard(current)
            for neighbor in neighbors4_unbounded(current):
                if neighbor in remaining and neighbor not in visited:
                    visited.add(neighbor)
                    q.append(neighbor)
        
        components.append(component)
    
    return components


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


def _generate_sweep_line_on_east(min_x: int, max_x: int, min_y: int, max_y: int) -> Set[Pos]:
    """
    Generate sweep line structure on the east (right) side, inspired by sweep.py.
    Creates a three-column structure:
    - Right column: full height at max_x
    - Middle column: at max_x - 1 with pattern (excluding y % 3 == 1)
    - Left column: full height at max_x - 2
    """
    sweep_line_x = max_x - 1
    
    # Right column (easternmost)
    sweep_line_right = {(sweep_line_x + 1, y) for y in range(min_y, max_y + 1)}
    
    # Middle column with pattern (exclude cells where y % 3 == 1)
    sweep_line_middle = {(sweep_line_x, y) for y in range(min_y, max_y + 1) if y % 3 != 1}
    
    # Left column (westernmost of the sweep line)
    sweep_line_left = {(sweep_line_x - 1, y) for y in range(min_y, max_y + 1)}
    
    # Combine all three columns
    sweep_line = sweep_line_left.union(sweep_line_middle).union(sweep_line_right)
    
    return sweep_line


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
    """Add candidates to scaffolding, sorted by distance to center of mass, maintaining connectivity."""
    candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
    for c in candidates:
        if len(scaff) >= total_mods:
            break
        # Only add if it maintains connectivity (must be adjacent to existing scaffold)
        test_set = scaff | {c}
        if is_connected(test_set):
            scaff.add(c)
    return scaff


def _trim_scaffold_while_connected(scaff: Set[Pos], target_count: int, 
                                   cx: float, cy: float) -> Set[Pos]:
    """Trim scaffolding to target count while maintaining connectivity."""
    if len(scaff) <= target_count:
        return scaff
    
    scaff_list = sorted(scaff, key=lambda p: abs(p[0] - cx) + abs(p[1] - cy), reverse=True)
    result = set(scaff_list)
    for pos in scaff_list:
        if len(result) <= target_count:
            break
        test_set = result - {pos}
        if is_connected(test_set):
            result = test_set
    return result


def _extend_scaffold_with_columns(scaff: Set[Pos], min_x: int, max_x: int, 
                                   min_y: int, max_y: int, total_mods: int) -> Set[Pos]:
    """Extend scaffold by adding adjacent columns to left or right."""
    if len(scaff) >= total_mods:
        return scaff
    
    # Add additional columns to the left if needed (must be adjacent to connect)
    sweep_min_x = min(x for x, _ in scaff)
    additional_cols_x = sweep_min_x - 1  # Adjacent to existing scaffold
    
    while len(scaff) < total_mods and additional_cols_x >= min_x - 5:
        additional_col = _build_vertical_column(additional_cols_x, min_y, max_y)
        # Add entire column since it's adjacent (will be connected)
        for pos in additional_col:
            if len(scaff) >= total_mods:
                break
            scaff.add(pos)
        additional_cols_x -= 1  # Move left, adjacent columns
    
    # If still not enough, add to the right (adjacent to existing scaffold)
    if len(scaff) < total_mods:
        sweep_max_x = max(x for x, _ in scaff)
        additional_cols_x = sweep_max_x + 1  # Adjacent to existing scaffold
        while len(scaff) < total_mods:
            additional_col = _build_vertical_column(additional_cols_x, min_y, max_y)
            for pos in additional_col:
                if len(scaff) >= total_mods:
                    break
                scaff.add(pos)
            additional_cols_x += 1  # Move right, adjacent columns
    
    return scaff


def _trim_scaffold_preserving_sweep_line(scaff: Set[Pos], min_x: int, max_x: int,
                                         min_y: int, max_y: int, total_mods: int,
                                         cx: float, cy: float) -> Set[Pos]:
    """Trim scaffold while trying to preserve sweep line structure."""
    if len(scaff) <= total_mods:
        return scaff
    
    # Try to keep the sweep line structure intact, trim from additional columns
    sweep_line = _generate_sweep_line_on_east(min_x, max_x, min_y, max_y)
    additional_cells = scaff - sweep_line
    
    if len(sweep_line) <= total_mods:
        # Keep entire sweep line, trim from additional cells while maintaining connectivity
        additional_sorted = sorted(additional_cells, key=lambda p: abs(p[0] - cx) + abs(p[1] - cy), reverse=True)
        result = sweep_line.copy()
        for pos in additional_sorted:
            if len(result) <= total_mods:
                break
            test_set = result - {pos}
            if is_connected(test_set):
                result = test_set
        return result
    else:
        # Need to trim from sweep line itself, maintaining connectivity
        return _trim_scaffold_while_connected(scaff, total_mods, cx, cy)


def _generate_manhattan_path(start: Pos, end: Pos) -> List[Pos]:
    """Generate Manhattan path between two positions."""
    path = []
    x1, y1 = start
    x2, y2 = end
    if x1 != x2:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            path.append((x, y1))
    if y1 != y2:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            path.append((x2, y))
    return path


def _find_closest_pair_between_components(comp1: Set[Pos], comp2: Set[Pos]) -> Tuple[Optional[Pos], Optional[Pos]]:
    """Find the closest pair of cells between two components."""
    min_dist = float('inf')
    bridge_start = None
    bridge_end = None
    for c1 in comp1:
        for c2 in comp2:
            dist = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1])
            if dist < min_dist:
                min_dist = dist
                bridge_start = c1
                bridge_end = c2
    return bridge_start, bridge_end


def _connect_components_with_bridge(base: Set[Pos], other_comp: Set[Pos], 
                                    total_mods: int, central_cell: Pos) -> Set[Pos]:
    """Connect two components by adding a bridge path."""
    bridge_start, bridge_end = _find_closest_pair_between_components(base, other_comp)
    
    if not bridge_start or not bridge_end:
        return base
    
    # Add path to connect (Manhattan path)
    path = _generate_manhattan_path(bridge_start, bridge_end)
    
    for p in path:
        if p not in base and p != central_cell and len(base) < total_mods:
            base.add(p)
        if len(base) >= total_mods:
            break
    
    base.update(other_comp)
    return base


def _repair_connectivity(scaff: Set[Pos], min_x: int, max_x: int, min_y: int, max_y: int,
                         total_mods: int, central_cell: Pos, cx: float, cy: float) -> Set[Pos]:
    """Repair disconnected scaffolding by connecting components."""
    components = _find_connected_components(scaff)
    if not components:
        return scaff
    
    # Use largest component as base
    components.sort(key=len, reverse=True)
    result = components[0].copy()
    
    # Connect other components to the base
    for other_comp in components[1:]:
        if len(result) >= total_mods:
            break
        result = _connect_components_with_bridge(result, other_comp, total_mods, central_cell)
    
    # If we lost modules during repair, add them back
    if len(result) < total_mods:
        all_candidates = _generate_all_candidates(min_x, max_x, min_y, max_y, result, central_cell)
        result = _add_candidates_sorted(result, all_candidates, total_mods, cx, cy)
    
    # If we have too many, trim while maintaining connectivity
    if len(result) > total_mods:
        result = _trim_scaffold_while_connected(result, total_mods, cx, cy)
    
    return result


def _generate_all_candidates(min_x: int, max_x: int, min_y: int, max_y: int,
                             exclude: Set[Pos], central_cell: Pos) -> List[Pos]:
    """Generate all candidate positions for expansion."""
    return [
        (x, y)
        for x in range(min_x - 2, max_x + 3)
        for y in range(min_y - 2, max_y + 3)
        if (x, y) not in exclude and (x, y) != central_cell
    ]


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
    """Final verification: ensure exact module count while maintaining connectivity."""
    if len(scaff) == total_mods:
        return scaff
    
    if len(scaff) > total_mods:
        # Trim excess while maintaining connectivity
        return _trim_scaffold_while_connected(scaff, total_mods, cx, cy)
    else:
        # Add missing cells (maintaining connectivity)
        all_candidates = _generate_all_candidates(min_x, max_x, min_y, max_y, scaff, central_cell)
        return _add_candidates_sorted(scaff, all_candidates, total_mods, cx, cy)


def _update_environment(env: Environment, scaff: Set[Pos]) -> None:
    """Update environment grid with scaffolding positions."""
    env.grid.occupied.clear()
    for pos in scaff:
        env.grid.occupied[pos] = True


def compute_scaffolding_from_env(env: Environment, central_cell: Pos) -> Set[Pos]:
    """
    Phase 2: Build scaffolding from exoskeleton using sweep line structure.
    Creates a sweep line on the east (right) side with three columns:
    - Right column: full height
    - Middle column: with pattern (excluding y % 3 == 1)
    - Left column: full height
    
    If more modules are needed, additional columns are added to the left or right.
    Preserves module count and keeps central cell empty for movement.
    Updates env.grid.occupied.
    
    Based on "Sliding Squares in Parallel" - inspired by sweep.py sweep line pattern
    to facilitate parallel reconfiguration.
    """
    occupied = set(env.grid.occupied.keys())
    if not occupied:
        return set()

    # Calculate bounding box with alignment
    min_x, max_x, min_y, max_y = _calculate_bounding_box_with_alignment(occupied)
    total_mods = len(occupied)
    
    # Calculate center of mass
    cx, cy = _get_center_of_mass(occupied)
    
    # 1. Generate sweep line on the east (right) side (primary structure)
    scaff = _generate_sweep_line_on_east(min_x, max_x, min_y, max_y)
    
    # 2. If sweep line doesn't provide enough modules, extend it or add more columns
    scaff = _extend_scaffold_with_columns(scaff, min_x, max_x, min_y, max_y, total_mods)
    
    # 3. If we have too many modules, trim keeping sweep line structure and connectivity
    scaff = _trim_scaffold_preserving_sweep_line(scaff, min_x, max_x, min_y, max_y, total_mods, cx, cy)
    
    # 4. Ensure central cell is empty
    scaff = _ensure_central_cell_empty(scaff, central_cell, min_x, max_x, min_y, max_y,
                                       total_mods, cx, cy)
    
    # 5. Ensure scaffolding center is empty
    scaff = _ensure_scaffolding_center_empty(scaff, total_mods, cx, cy)
    
    # Final verification
    scaff = _finalize_scaffolding_count(scaff, min_x, max_x, min_y, max_y, total_mods,
                                       central_cell, cx, cy)
    
    # 6. Final connectivity check and repair
    if not is_connected(scaff):
        print(f"[Phase 2] WARNING: Scaffolding is not connected! Attempting to repair...")
        scaff = _repair_connectivity(scaff, min_x, max_x, min_y, max_y, total_mods, central_cell, cx, cy)
    
    # Update environment
    _update_environment(env, scaff)
    
    connected_status = "connected" if is_connected(scaff) else "NOT CONNECTED"
    print(f"[Phase 2] Sweep line scaffolding generated with {len(scaff)} modules (target = {total_mods}), {connected_status}")
    return scaff

