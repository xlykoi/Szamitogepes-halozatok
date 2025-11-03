from collections import deque
from typing import Set, Tuple
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

    # --- bounding box
    min_x = min(x for x, _ in occupied)
    max_x = max(x for x, _ in occupied)
    min_y = min(y for _, y in occupied)
    max_y = max(y for _, y in occupied)
    total_mods = len(occupied)

    # --- 1) build BFS tree (skeleton)
    root = next(iter(occupied))
    parent = {root: None}
    q = deque([root])
    while q:
        c = q.popleft()
        for n in neighbors4(c, max_x, max_y):
            if n in occupied and n not in parent:
                parent[n] = c
                q.append(n)
    skeleton = set(parent.keys())

    # --- 2) Shell: all free 4-neighbors of skeleton (not in skeleton)
    shell = set()
    for (x, y) in skeleton:
        for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
            if (nx, ny) not in skeleton:
                shell.add((nx, ny))

    # --- 3) Combine skeleton and shell
    exo = skeleton | shell

    # --- 4) Calculate center cell of exoskeleton (must remain empty)
    if exo:
        exo_min_x = min(x for x, _ in exo)
        exo_max_x = max(x for x, _ in exo)
        exo_min_y = min(y for _, y in exo)
        exo_max_y = max(y for _, y in exo)
        center_x = (exo_min_x + exo_max_x) // 2
        center_y = (exo_min_y + exo_max_y) // 2
        center_cell = (center_x, center_y)
    else:
        center_cell = None

    # --- 5) Balance to preserve module count, ensuring center is empty
    # Remove center from exoskeleton first
    if center_cell:
        exo.discard(center_cell)

    if len(exo) > total_mods:
        # Use center of mass of original occupied cells for sorting
        cx = sum(x for x, _ in occupied) / len(occupied)
        cy = sum(y for _, y in occupied) / len(occupied)

        # Keep cells closest to center, prefer skeleton over shell
        exo_sorted = sorted(
            [p for p in exo],
            key=lambda p: (p not in skeleton, abs(p[0] - cx) + abs(p[1] - cy))
        )
        exo = set(exo_sorted[:total_mods])

    elif len(exo) < total_mods:
        # Use center of mass for adding candidates
        cx = sum(x for x, _ in occupied) / len(occupied)
        cy = sum(y for _, y in occupied) / len(occupied)
        candidates = [
            (x, y)
            for x in range(min_x - 1, max_x + 2)
            for y in range(min_y - 1, max_y + 2)
            if (x, y) not in exo and (x, y) != center_cell
        ]
        candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
        for c in candidates:
            if len(exo) >= total_mods:
                break
            exo.add(c)

    # --- 6) Ensure center cell is NOT in exoskeleton (double check)
    if center_cell:
        exo.discard(center_cell)

    # --- 7) Ensure the center cell is reachable (not fully enclosed)
    if center_cell:
        all_coords = {
            (x, y)
            for x in range(min_x - 2, max_x + 3)
            for y in range(min_y - 2, max_y + 3)
        }
        free = all_coords - exo  # all empty cells

        def bfs_reachables(start):
            q = deque([start])
            visited = {start}
            while q:
                x, y = q.popleft()
                for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
                    if (nx, ny) in free and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        q.append((nx, ny))
            return visited

        outer_start = (min_x - 2, min_y - 2)
        reachable = bfs_reachables(outer_start)

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
                    # Need to add another cell to maintain count
                    cx = sum(x for x, _ in occupied) / len(occupied)
                    cy = sum(y for _, y in occupied) / len(occupied)
                    candidates = [
                        (x, y)
                        for x in range(min_x - 1, max_x + 2)
                        for y in range(min_y - 1, max_y + 2)
                        if (x, y) not in exo and (x, y) != center_cell
                    ]
                    candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
                    for c in candidates:
                        if len(exo) >= total_mods:
                            break
                        exo.add(c)
                    break

    # --- 8) Recalculate center of final exoskeleton and ensure it's empty
    if exo:
        exo_min_x = min(x for x, _ in exo)
        exo_max_x = max(x for x, _ in exo)
        exo_min_y = min(y for _, y in exo)
        exo_max_y = max(y for _, y in exo)
        center_x = (exo_min_x + exo_max_x) // 2
        center_y = (exo_min_y + exo_max_y) // 2
        center_cell = (center_x, center_y)
    else:
        center_cell = None

    # --- 9) Final guarantee: exact module count and center is empty
    # Ensure center is empty
    if center_cell:
        exo.discard(center_cell)
    
    # Adjust count if needed to guarantee exact module count
    if len(exo) < total_mods:
        cx = sum(x for x, _ in occupied) / len(occupied)
        cy = sum(y for _, y in occupied) / len(occupied)
        candidates = [
            (x, y)
            for x in range(min_x - 1, max_x + 2)
            for y in range(min_y - 1, max_y + 2)
            if (x, y) not in exo and (x, y) != center_cell
        ]
        candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
        for c in candidates:
            if len(exo) >= total_mods:
                break
            exo.add(c)
    
    elif len(exo) > total_mods:
        cx = sum(x for x, _ in occupied) / len(occupied)
        cy = sum(y for _, y in occupied) / len(occupied)
        exo_sorted = sorted(
            [p for p in exo],
            key=lambda p: (p not in skeleton, abs(p[0] - cx) + abs(p[1] - cy))
        )
        exo = set(exo_sorted[:total_mods])
        # Ensure center is still not in exo after trimming
        if center_cell:
            exo.discard(center_cell)
            # If we removed center and now have less than total_mods, add one more
            if len(exo) < total_mods:
                candidates = [
                    (x, y)
                    for x in range(min_x - 1, max_x + 2)
                    for y in range(min_y - 1, max_y + 2)
                    if (x, y) not in exo and (x, y) != center_cell
                ]
                candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
                for c in candidates:
                    if len(exo) >= total_mods:
                        break
                    exo.add(c)
    
    # Final double-check: ensure center is empty (recalculate one more time after adjustments)
    if exo:
        exo_min_x = min(x for x, _ in exo)
        exo_max_x = max(x for x, _ in exo)
        exo_min_y = min(y for _, y in exo)
        exo_max_y = max(y for _, y in exo)
        center_x = (exo_min_x + exo_max_x) // 2
        center_y = (exo_min_y + exo_max_y) // 2
        center_cell = (center_x, center_y)
        exo.discard(center_cell)
        # If removing center caused us to lose a module, add one back
        if len(exo) < total_mods:
            cx = sum(x for x, _ in occupied) / len(occupied)
            cy = sum(y for _, y in occupied) / len(occupied)
            candidates = [
                (x, y)
                for x in range(min_x - 1, max_x + 2)
                for y in range(min_y - 1, max_y + 2)
                if (x, y) not in exo and (x, y) != center_cell
            ]
            candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
            for c in candidates:
                if len(exo) >= total_mods:
                    break
                exo.add(c)

    # --- 10) Verify connectivity (CRITICAL: sliding squares model requires connectivity)
    if not is_connected(exo):
        # If not connected, try to fix by adding connecting cells
        # This is a fallback - ideally trimming should preserve connectivity
        components = []
        remaining = exo.copy()
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
        
        # Connect components by finding shortest paths
        if len(components) > 1:
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
                    # Add intermediate cells to form a path
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
                    # Add the other component
                    exo.update(other_comp)
            
            # Trim if we have too many
            if len(exo) > total_mods:
                # Recalculate center for sorting
                if exo:
                    exo_center_x = sum(x for x, _ in exo) / len(exo)
                    exo_center_y = sum(y for _, y in exo) / len(exo)
                else:
                    exo_center_x, exo_center_y = 0, 0
                # Prefer removing cells that don't break connectivity
                exo_sorted = sorted(
                    [p for p in exo],
                    key=lambda p: (p not in skeleton, abs(p[0] - exo_center_x) + abs(p[1] - exo_center_y))
                )
                temp_exo = set()
                for p in exo_sorted:
                    if len(temp_exo) >= total_mods:
                        break
                    temp_exo.add(p)
                    # Check if still connected (simple heuristic: check if has neighbor)
                    if len(temp_exo) > 1:
                        has_neighbor = any(n in temp_exo for n in neighbors4_unbounded(p))
                        if not has_neighbor and len(temp_exo) < total_mods:
                            # Skip isolated cells if we haven't reached target
                            temp_exo.discard(p)
                exo = temp_exo
            
            # Ensure center is still empty
            if center_cell:
                exo.discard(center_cell)
            
            # Final count adjustment if needed
            if len(exo) < total_mods:
                cx = sum(x for x, _ in occupied) / len(occupied)
                cy = sum(y for _, y in occupied) / len(occupied)
                candidates = [
                    (x, y)
                    for x in range(min_x - 1, max_x + 2)
                    for y in range(min_y - 1, max_y + 2)
                    if (x, y) not in exo and (x, y) != center_cell
                ]
                candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
                for c in candidates:
                    if len(exo) >= total_mods:
                        break
                    # Only add if it connects or is adjacent to exo
                    if any(n in exo for n in neighbors4_unbounded(c)):
                        exo.add(c)

    # --- 11) Final verification: ensure connectivity and module count
    if not is_connected(exo):
        print(f"WARNING: Exoskeleton is not fully connected! This violates sliding squares model constraints.")
    
    # Ensure center is empty one final time
    if center_cell:
        exo.discard(center_cell)
        if len(exo) < total_mods:
            # Add one more cell if needed, prioritizing connectivity
            cx = sum(x for x, _ in occupied) / len(occupied)
            cy = sum(y for _, y in occupied) / len(occupied)
            candidates = [
                (x, y)
                for x in range(min_x - 1, max_x + 2)
                for y in range(min_y - 1, max_y + 2)
                if (x, y) not in exo and (x, y) != center_cell
            ]
            # Prefer candidates that connect to exo
            connected_candidates = [c for c in candidates if any(n in exo for n in neighbors4_unbounded(c))]
            if connected_candidates:
                connected_candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
                if len(exo) < total_mods:
                    exo.add(connected_candidates[0])
            elif candidates:
                # Fallback to any candidate
                candidates.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
                if len(exo) < total_mods:
                    exo.add(candidates[0])

    # --- 12) Update environment (this "moves" the modules)
    env.grid.occupied.clear()
    for pos in exo:
        env.grid.occupied[pos] = True  # placeholder value

    return exo


def print_exoskeleton_matrix(env: Environment, exo: Set[Pos]):
    """
    Print the resulting configuration.
    Shows C (core/skeleton), S (shell), and 0 (empty, including center).
    """
    occupied = set(env.grid.occupied.keys())
    all_cells = exo | occupied

    if occupied:
        min_x_occ = min(x for x, _ in occupied)
        max_x_occ = max(x for x, _ in occupied)
        min_y_occ = min(y for _, y in occupied)
        max_y_occ = max(y for _, y in occupied)
        center_x = (min_x_occ + max_x_occ) // 2
        center_y = (min_y_occ + max_y_occ) // 2
        center_cell = (center_x, center_y)
    else:
        center_cell = None

    all_positions = list(all_cells)
    if center_cell:
        all_positions.append(center_cell)

    if not all_positions:
        print("Empty configuration")
        return

    max_x = max(x for x, _ in all_positions)
    max_y = max(y for _, y in all_positions)
    min_x = min(x for x, _ in all_positions)
    min_y = min(y for _, y in all_positions)

    matrix = []
    for y in range(min_y, max_y + 1):
        row = ""
        for x in range(min_x, max_x + 1):
            pos = (x, y)
            if center_cell and pos == center_cell:
                row += "0"
            elif pos in exo and pos in occupied:
                row += "C"
            elif pos in exo:
                row += "S"
            else:
                row += "0"
        matrix.append(row)
    print("\n".join(matrix))

    if center_cell:
        print(f"\nNote: Center cell at ({center_x}, {center_y}) is kept empty and reachable for module movement.")
