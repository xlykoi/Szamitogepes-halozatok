from typing import Set, Tuple
from environment import Environment

Pos = Tuple[int, int]

def compute_scaffolding_from_env(env: Environment, central_cell: Pos) -> Set[Pos]:
    """
    Phase 2: Build scaffolding from exoskeleton.
    Moves modules into an 'L' shape, preserving module count.
    Central cell remains empty for movement.
    Updates env.grid.occupied.
    """
    occupied = set(env.grid.occupied.keys())
    if not occupied:
        return set()

    # Bounding box
    min_x = min(x for x, _ in occupied)
    max_x = max(x for x, _ in occupied)
    min_y = min(y for _, y in occupied)
    max_y = max(y for _, y in occupied)
    # Align max_y to multiple of 3
    if (max_y - min_y + 1) % 3 != 0:
        max_y += 3 - ((max_y - min_y + 1) % 3)
    total_mods = len(occupied)

    # Start with rightmost column as vertical scaffolding
    rightmost_x = max_x
    vertical_column = {(rightmost_x, y) for y in range(min_y, max_y + 1)}

    # Fill remaining modules to form horizontal base (L shape)
    exo = set(vertical_column)
    cx = sum(x for x, _ in occupied) / total_mods
    cy = sum(y for _, y in occupied) / total_mods

    # Candidates: everything inside bounding box except vertical column and central cell
    candidates = [
        (x, y)
        for x in range(min_x, max_x)
        for y in range(min_y, max_y + 1)
        if (x, y) not in exo and (x, y) != central_cell
    ]
    candidates.sort(key=lambda p: abs(p[0]-cx) + abs(p[1]-cy))

    for c in candidates:
        if len(exo) >= total_mods:
            break
        exo.add(c)

    # Ensure central cell is empty
    exo.discard(central_cell)

    # Update environment
    env.grid.occupied.clear()
    for pos in exo:
        env.grid.occupied[pos] = True

    return exo
