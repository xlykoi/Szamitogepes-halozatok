from collections import deque
from typing import Set, Tuple
from environment import Environment

Pos = Tuple[int, int]


def neighbors4(p: Pos, max_x: int, max_y: int):
    """Return 4-connected neighbors within bounds."""
    x, y = p
    nbs = []
    for nx, ny in [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]:
        if 0 <= nx <= max_x and 0 <= ny <= max_y:
            nbs.append((nx, ny))
    return nbs


def compute_exoskeleton_from_env(env: Environment) -> Set[Pos]:
    """
    Build an exoskeleton (core + shell) from the environment.
    Actually updates env.grid.occupied so modules "move".
    Ensures total number of modules stays the same.
    IMPORTANT: Leaves the central cell empty to allow module movement.
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

    # --- Calculate center cell (must remain empty)
    center_x = (min_x + max_x) // 2
    center_y = (min_y + max_y) // 2
    center_cell = (center_x, center_y)

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

    # --- 2) Shell: all free 4-neighbors of skeleton (not occupied)
    shell = set()
    for (x, y) in skeleton:
        for nx, ny in [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]:
            if (nx, ny) not in skeleton and (nx, ny) != center_cell:
                shell.add((nx, ny))

    # --- 3) Remove center cell if it's in skeleton or shell
    skeleton.discard(center_cell)
    shell.discard(center_cell)

    # --- 4) Combine and balance to preserve module count
    exo = skeleton | shell

    if len(exo) > total_mods:
        cx = sum(x for x, _ in occupied) / len(occupied)
        cy = sum(y for _, y in occupied) / len(occupied)

        # Keep cells closest to center, prefer skeleton, but exclude center_cell
        exo_sorted = sorted(
            [p for p in exo if p != center_cell],
            key=lambda p: (p not in skeleton, abs(p[0]-cx) + abs(p[1]-cy))
        )
        exo = set(exo_sorted[:total_mods])

    elif len(exo) < total_mods:
        cx = sum(x for x, _ in occupied) / len(occupied)
        cy = sum(y for _, y in occupied) / len(occupied)
        candidates = [
            (x, y)
            for x in range(min_x-1, max_x+2)
            for y in range(min_y-1, max_y+2)
            if (x, y) not in exo and (x, y) != center_cell
        ]
        candidates.sort(key=lambda p: abs(p[0]-cx) + abs(p[1]-cy))
        for c in candidates:
            if len(exo) >= total_mods:
                break
            exo.add(c)

    # --- 5) Ensure center cell is NOT in exoskeleton
    exo.discard(center_cell)

    # --- 6) Update environment (this "moves" the modules)
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
    
    # Calculate center to highlight it
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

    # Expand bounds to include center if needed
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
                # Highlight center cell (empty by design)
                row += "0"  # or could use special marker like "·"
            elif pos in exo and pos in occupied:
                row += "C"
            elif pos in exo:
                row += "S"
            else:
                row += "0"
        matrix.append(row)
    print("\n".join(matrix))
    
    if center_cell:
        print(f"\nNote: Center cell at ({center_x}, {center_y}) is kept empty for module movement.")
