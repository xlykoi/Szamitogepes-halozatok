from collections import deque
from typing import Set, Tuple, List, Optional
from environment import Environment

Pos = Tuple[int, int]


def neighbors4(p: Pos, max_x: int, max_y: int):
    """Return 4-connected neighbors within bounds."""
    x, y = p
    nbs = []
    for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
        if 0 <= nx <= max_x and 0 <= ny <= max_y:
            nbs.append((nx, ny))
    return nbs


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


def _build_skeleton(occupied: Set[Pos], max_x: int, max_y: int) -> Set[Pos]:
    """Build a BFS tree (skeleton) from occupied positions."""
    root = next(iter(occupied))
    parent = {root: None}
    q = deque([root])
    while q:
        c = q.popleft()
        for n in neighbors4(c, max_x, max_y):
            if n in occupied and n not in parent:
                parent[n] = c
                q.append(n)
    return set(parent.keys())


def _build_shell(skeleton: Set[Pos]) -> Set[Pos]:
    """Build shell: all free 4-neighbors of skeleton (not in skeleton)."""
    shell = set()
    for (x, y) in skeleton:
        for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
            if (nx, ny) not in skeleton:
                shell.add((nx, ny))
    return shell


def _calculate_center(positions: Set[Pos]) -> Optional[Pos]:
    """Calculate center cell of a set of positions."""
    if not positions:
        return None
    min_x = min(x for x, _ in positions)
    max_x = max(x for x, _ in positions)
    min_y = min(y for _, y in positions)
    max_y = max(y for _, y in positions)
    center_x = (min_x + max_x) // 2
    center_y = (min_y + max_y) // 2
    return (center_x, center_y)


def _get_center_of_mass(occupied: Set[Pos]) -> Tuple[float, float]:
    """Calculate center of mass of occupied positions."""
    if not occupied:
        return (0.0, 0.0)
    cx = sum(x for x, _ in occupied) / len(occupied)
    cy = sum(y for _, y in occupied) / len(occupied)
    return (cx, cy)


def _generate_candidates(min_x: int, max_x: int, min_y: int, max_y: int, 
                        exclude: Set[Pos], center_cell: Optional[Pos]) -> List[Pos]:
    """Generate candidate positions for adding to exoskeleton."""
    candidates = [
        (x, y)
        for x in range(min_x - 1, max_x + 2)
        for y in range(min_y - 1, max_y + 2)
        if (x, y) not in exclude and (x, y) != center_cell
    ]
    return candidates


def _add_candidates_to_exo(exo: Set[Pos], candidates: List[Pos], 
                          total_mods: int, cx: float, cy: float) -> Set[Pos]:
    """Add candidates to exoskeleton until reaching total_mods, sorted by distance to center of mass."""
    candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
    for c in candidates:
        if len(exo) >= total_mods:
            break
        exo.add(c)
    return exo


def _trim_exoskeleton(exo: Set[Pos], skeleton: Set[Pos], total_mods: int, 
                     cx: float, cy: float) -> Set[Pos]:
    """Trim exoskeleton to match total_mods, preferring skeleton over shell."""
    exo_sorted = sorted(
        [p for p in exo],
        key=lambda p: (p not in skeleton, abs(p[0] - cx) + abs(p[1] - cy))
    )
    return set(exo_sorted[:total_mods])


def _balance_exoskeleton_count(exo: Set[Pos], skeleton: Set[Pos], occupied: Set[Pos],
                               min_x: int, max_x: int, min_y: int, max_y: int,
                               total_mods: int, center_cell: Optional[Pos]) -> Set[Pos]:
    """Balance exoskeleton to preserve module count, ensuring center is empty."""
    exo.discard(center_cell) if center_cell else None
    
    cx, cy = _get_center_of_mass(occupied)
    
    if len(exo) > total_mods:
        exo = _trim_exoskeleton(exo, skeleton, total_mods, cx, cy)
    elif len(exo) < total_mods:
        candidates = _generate_candidates(min_x, max_x, min_y, max_y, exo, center_cell)
        exo = _add_candidates_to_exo(exo, candidates, total_mods, cx, cy)
    
    return exo


def _bfs_reachables(start: Pos, free: Set[Pos]) -> Set[Pos]:
    """BFS to find all reachable positions from start in free space."""
    q = deque([start])
    visited = {start}
    while q:
        x, y = q.popleft()
        for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
            if (nx, ny) in free and (nx, ny) not in visited:
                visited.add((nx, ny))
                q.append((nx, ny))
    return visited


def _ensure_center_reachable(exo: Set[Pos], occupied: Set[Pos],
                            min_x: int, max_x: int, min_y: int, max_y: int,
                            total_mods: int, center_cell: Optional[Pos]) -> Set[Pos]:
    """Ensure the center cell is reachable (not fully enclosed)."""
    if not center_cell:
        return exo
    
    all_coords = {
        (x, y)
        for x in range(min_x - 2, max_x + 3)
        for y in range(min_y - 2, max_y + 3)
    }
    free = all_coords - exo
    outer_start = (min_x - 2, min_y - 2)
    reachable = _bfs_reachables(outer_start, free)
    
    # If center cell is NOT reachable, remove one shell cell next to it
    if center_cell not in reachable:
        for n in [
            (center_cell[0] - 1, center_cell[1]),
            (center_cell[0] + 1, center_cell[1]),
            (center_cell[0], center_cell[1] - 1),
            (center_cell[0], center_cell[1] + 1),
        ]:
            if n in exo:
                exo.remove(n)
                cx, cy = _get_center_of_mass(occupied)
                candidates = _generate_candidates(min_x, max_x, min_y, max_y, exo, center_cell)
                exo = _add_candidates_to_exo(exo, candidates, total_mods, cx, cy)
                break
    
    return exo


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


def _connect_components(components: List[Set[Pos]], skeleton: Set[Pos],
                       total_mods: int, center_cell: Optional[Pos]) -> Set[Pos]:
    """Connect disconnected components by finding shortest paths."""
    if len(components) <= 1:
        return components[0] if components else set()
    
    # Use largest component as base
    components.sort(key=len, reverse=True)
    exo = components[0].copy()
    
    # Connect other components to the base
    for other_comp in components[1:]:
        # Find closest pair of cells between components
        min_dist = float('inf')
        bridge_start = None
        bridge_end = None
        for c1 in exo:
            for c2 in other_comp:
                dist = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1])
                if dist < min_dist:
                    min_dist = dist
                    bridge_start = c1
                    bridge_end = c2
        
        # Add path to connect (Manhattan path)
        if bridge_start and bridge_end:
            path = []
            x1, y1 = bridge_start
            x2, y2 = bridge_end
            if x1 != x2:
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    path.append((x, y1))
            if y1 != y2:
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    path.append((x2, y))
            
            for p in path:
                if p not in exo and p != center_cell:
                    exo.add(p)
                    if len(exo) > total_mods:
                        break
            exo.update(other_comp)
    
    # Trim if we have too many
    if len(exo) > total_mods:
        if exo:
            exo_center_x = sum(x for x, _ in exo) / len(exo)
            exo_center_y = sum(y for _, y in exo) / len(exo)
        else:
            exo_center_x, exo_center_y = 0, 0
        
        exo_sorted = sorted(
            [p for p in exo],
            key=lambda p: (p not in skeleton, abs(p[0] - exo_center_x) + abs(p[1] - exo_center_y))
        )
        temp_exo = set()
        for p in exo_sorted:
            if len(temp_exo) >= total_mods:
                break
            temp_exo.add(p)
            if len(temp_exo) > 1:
                has_neighbor = any(n in temp_exo for n in neighbors4_unbounded(p))
                if not has_neighbor and len(temp_exo) < total_mods:
                    temp_exo.discard(p)
        exo = temp_exo
    
    if center_cell:
        exo.discard(center_cell)
    
    return exo


def _fix_connectivity(exo: Set[Pos], skeleton: Set[Pos], occupied: Set[Pos],
                    min_x: int, max_x: int, min_y: int, max_y: int,
                    total_mods: int, center_cell: Optional[Pos]) -> Set[Pos]:
    """Fix connectivity issues by connecting disconnected components."""
    if is_connected(exo):
        return exo
    
    components = _find_connected_components(exo)
    exo = _connect_components(components, skeleton, total_mods, center_cell)
    
    # Final count adjustment if needed
    if len(exo) < total_mods:
        cx, cy = _get_center_of_mass(occupied)
        candidates = _generate_candidates(min_x, max_x, min_y, max_y, exo, center_cell)
        for c in candidates:
            if len(exo) >= total_mods:
                break
            if any(n in exo for n in neighbors4_unbounded(c)):
                exo.add(c)
    
    return exo


def _finalize_exoskeleton(exo: Set[Pos], occupied: Set[Pos],
                         min_x: int, max_x: int, min_y: int, max_y: int,
                         total_mods: int) -> Set[Pos]:
    """Final verification: ensure connectivity and module count."""
    center_cell = _calculate_center(exo)
    exo.discard(center_cell) if center_cell else None
    
    if not is_connected(exo):
        print(f"WARNING: Exoskeleton is not fully connected! This violates sliding squares model constraints.")
    
    # Final adjustment if needed
    if len(exo) < total_mods:
        cx, cy = _get_center_of_mass(occupied)
        candidates = _generate_candidates(min_x, max_x, min_y, max_y, exo, center_cell)
        connected_candidates = [c for c in candidates if any(n in exo for n in neighbors4_unbounded(c))]
        if connected_candidates:
            connected_candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
            if len(exo) < total_mods:
                exo.add(connected_candidates[0])
        elif candidates:
            candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
            if len(exo) < total_mods:
                exo.add(candidates[0])
    
    return exo


def _update_environment(env: Environment, exo: Set[Pos]) -> None:
    """Update environment grid with exoskeleton positions."""
    env.grid.occupied.clear()
    for pos in exo:
        env.grid.occupied[pos] = True  # placeholder value


def compute_exoskeleton_from_env(env: Environment) -> Set[Pos]:
    """
    Build an exoskeleton (core + shell) from the environment.
    Actually updates env.grid.occupied so modules "move".
    Ensures total number of modules stays the same.
    IMPORTANT: Leaves the central cell of the exoskeleton empty and reachable to allow module movement.
    """
    occupied = set(env.grid.occupied.keys())
    if not occupied:
        return set()

    # Calculate bounding box
    min_x = min(x for x, _ in occupied)
    max_x = max(x for x, _ in occupied)
    min_y = min(y for _, y in occupied)
    max_y = max(y for _, y in occupied)
    total_mods = len(occupied)

    # Build skeleton and shell
    skeleton = _build_skeleton(occupied, max_x, max_y)
    shell = _build_shell(skeleton)
    exo = skeleton | shell

    # Calculate center and balance count
    center_cell = _calculate_center(exo)
    exo = _balance_exoskeleton_count(exo, skeleton, occupied, min_x, max_x, min_y, max_y, 
                                     total_mods, center_cell)
    
    # Ensure center is reachable
    exo = _ensure_center_reachable(exo, occupied, min_x, max_x, min_y, max_y, 
                                   total_mods, center_cell)
    
    # Recalculate center and balance again
    center_cell = _calculate_center(exo)
    exo = _balance_exoskeleton_count(exo, skeleton, occupied, min_x, max_x, min_y, max_y, 
                                     total_mods, center_cell)
    
    # Final double-check
    center_cell = _calculate_center(exo)
    exo.discard(center_cell) if center_cell else None
    if len(exo) < total_mods:
        cx, cy = _get_center_of_mass(occupied)
        candidates = _generate_candidates(min_x, max_x, min_y, max_y, exo, center_cell)
        exo = _add_candidates_to_exo(exo, candidates, total_mods, cx, cy)

    # Fix connectivity issues
    exo = _fix_connectivity(exo, skeleton, occupied, min_x, max_x, min_y, max_y, 
                           total_mods, center_cell)

    # Final verification
    exo = _finalize_exoskeleton(exo, occupied, min_x, max_x, min_y, max_y, total_mods)

    # Update environment
    _update_environment(env, exo)

    return exo


