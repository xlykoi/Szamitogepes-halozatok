import collections
from typing import Set, Tuple
from environment import Environment


def compute_skeleton(env: Environment) -> Set[Tuple[int, int]]:
    """Compute a spanning 'skeleton' (váz) for the current configuration.
    The skeleton is a thin, connected subset of occupied cells that covers the shape
    while minimizing cycles — used as the base structure for exoskeleton construction.
    """

    occupied_cells = set(env.grid.occupied.keys())
    if not occupied_cells:
        return set()

    x_coords = sorted({x for x, _ in occupied_cells})
    min_x, max_x = x_coords[0], x_coords[-1]

    def get_column_cells(x: int) -> Set[Tuple[int, int]]:
        """Return all occupied cells that belong to a given x-column."""
        return {cell for cell in occupied_cells if cell[0] == x}

    # Step 1: gather vertical components every 2nd column
    vertical_components = []
    current_x = min_x
    while current_x <= max_x:
        column_cells = get_column_cells(current_x)
        seen_in_column = set()
        components_in_column = []

        # find connected vertical segments (BFS along y)
        for cell in column_cells:
            if cell in seen_in_column:
                continue

            segment_queue = collections.deque([cell])
            vertical_segment = {cell}
            seen_in_column.add(cell)

            while segment_queue:
                current = segment_queue.popleft()
                for neighbor in [(current[0], current[1] + 1), (current[0], current[1] - 1)]:
                    if neighbor in column_cells and neighbor not in seen_in_column:
                        seen_in_column.add(neighbor)
                        vertical_segment.add(neighbor)
                        segment_queue.append(neighbor)

            components_in_column.append(vertical_segment)

        vertical_components.extend(components_in_column)
        current_x += 2  # skip alternate columns for sparsity

    # Step 2: initial skeleton = all selected vertical components
    skeleton_cells = set()
    for segment in vertical_components:
        skeleton_cells |= segment

    # Step 3: ensure every occupied cell is covered (C ⊂ N[S])
    for cell in occupied_cells:
        if cell in skeleton_cells:
            continue
        if not any(neighbor in skeleton_cells for neighbor in env.grid.neighbors4(cell)):
            skeleton_cells.add(cell)

    # Step 4: build spanning tree over the occupied configuration
    all_nodes = occupied_cells
    root = next(iter(all_nodes))
    parent_map = {root: None}
    queue = collections.deque([root])

    while queue:
        current = queue.popleft()
        for neighbor in env.grid.neighbors4(current):
            if neighbor in all_nodes and neighbor not in parent_map:
                parent_map[neighbor] = current
                queue.append(neighbor)

    tree_nodes = set(parent_map.keys())

    # Step 5: select every other x-column node to form a thin spine
    spine_cells = {cell for cell in tree_nodes if cell[0] % 2 == 0}

    # add isolated nodes that have no east-west neighbors
    for cell in tree_nodes:
        if cell in spine_cells:
            continue
        east, west = (cell[0] + 1, cell[1]), (cell[0] - 1, cell[1])
        if east not in all_nodes and west not in all_nodes:
            spine_cells.add(cell)

    # Step 6: connect the spine nodes along BFS tree paths to ensure connectivity
    connected_skeleton = set(spine_cells)
    spine_list = list(spine_cells)
    for i in range(1, len(spine_list)):
        prev_node = spine_list[i - 1]
        current_node = spine_list[i]
        path_nodes = []
        walker = current_node
        while walker is not None and walker != prev_node:
            path_nodes.append(walker)
            walker = parent_map.get(walker)
        connected_skeleton.update(path_nodes)

    return connected_skeleton


def compute_exoskeleton(env: Environment, skeleton_cells: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
    """Build a one-cell-thick exoskeleton around the skeleton."""
    exoskeleton_cells = set(skeleton_cells)
    for cell in skeleton_cells:
        for neighbor in env.grid.neighbors4(cell):
            if neighbor not in env.grid.occupied and env.grid.in_bounds(neighbor):
                exoskeleton_cells.add(neighbor)
    return exoskeleton_cells
