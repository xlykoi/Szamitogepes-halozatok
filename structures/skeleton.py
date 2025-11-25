from collections import deque
from typing import Set, Tuple, List, Optional, Dict
from copy import deepcopy

# A projekthez illeszkedő osztályok (a projektben ezek a modulok léteznek)
from environment import Environment
from structures.module import Move

Pos = Tuple[int, int]

# -----------------------
# Utilities: neighbors & connectivity
# -----------------------
def neighbors4(p: Pos, max_x: int, max_y: int) -> List[Pos]:
    x, y = p
    nbs = []
    for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
        if 0 <= nx <= max_x and 0 <= ny <= max_y:
            nbs.append((nx, ny))
    return nbs

def neighbors4_unbounded(p: Pos) -> List[Pos]:
    x, y = p
    return [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]

def is_connected(positions: Set[Pos]) -> bool:
    """Simple BFS connectivity test (4-neighbors)."""
    if not positions:
        return True
    if len(positions) == 1:
        return True
    start = next(iter(positions))
    visited = {start}
    q = deque([start])
    while q:
        c = q.popleft()
        for n in neighbors4_unbounded(c):
            if n in positions and n not in visited:
                visited.add(n)
                q.append(n)
    return len(visited) == len(positions)


def _find_closest_hole(current_pos: Pos, holes: Set[Pos]) -> Optional[Pos]:
    """Finds the closest hole (position) to current_pos using Manhattan distance."""
    if not holes:
        return None
    return min(holes, key=lambda h: abs(h[0] - current_pos[0]) + abs(h[1] - current_pos[1]))


def _is_move_connectivity_safe(occupied_before_move: Set[Pos], current_pos: Pos, target_pos: Pos) -> bool:
    """Checks if moving from current_pos to target_pos maintains connectivity."""
    if current_pos == target_pos:
        return True
    # Simulate the move
    test_positions = (occupied_before_move - {current_pos}) | {target_pos}
    return is_connected(test_positions)

# -----------------------
# Skeleton & shell builders
# -----------------------
def _build_skeleton(occupied: Set[Pos], max_x: int, max_y: int) -> Set[Pos]:
    """BFS tree over occupied cells (returns the BFS reachable set / tree nodes)."""
    if not occupied:
        return set()
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
    """Return all 4-neighbors of skeleton that are not in skeleton (unbounded)."""
    shell = set()
    for (x, y) in skeleton:
        for nx, ny in neighbors4_unbounded((x, y)):
            if (nx, ny) not in skeleton:
                shell.add((nx, ny))
    return shell

def _calculate_center(positions: Set[Pos]) -> Optional[Pos]:
    if not positions:
        return None
    min_x = min(x for x, _ in positions)
    max_x = max(x for x, _ in positions)
    min_y = min(y for _, y in positions)
    max_y = max(y for _, y in positions)
    return ((min_x + max_x) // 2, (min_y + max_y) // 2)

def _get_center_of_mass(occupied: Set[Pos]) -> Tuple[float, float]:
    if not occupied:
        return (0.0, 0.0)
    cx = sum(x for x, _ in occupied) / len(occupied)
    cy = sum(y for _, y in occupied) / len(occupied)
    return (cx, cy)

def _generate_candidates(min_x: int, max_x: int, min_y: int, max_y: int,
                         exclude: Set[Pos], center_cell: Optional[Pos]) -> List[Pos]:
    candidates = [
        (x, y)
        for x in range(min_x - 1, max_x + 2)
        for y in range(min_y - 1, max_y + 2)
        if (x, y) not in exclude and (x, y) != center_cell
    ]
    return candidates

def _trim_exoskeleton_unsafe(exo: Set[Pos], skeleton: Set[Pos], total_mods: int, cx: float, cy: float) -> Set[Pos]:
    exo_sorted = sorted([p for p in exo], key=lambda p: (p not in skeleton, abs(p[0] - cx) + abs(p[1] - cy)))
    return set(exo_sorted[:total_mods])

# safe trim that preserves connectivity where possible
def _safe_trim_exoskeleton(exo: Set[Pos], skeleton: Set[Pos], total_mods: int, cx: float, cy: float) -> Set[Pos]:
    # remove far-away non-skeleton cells first, but never break connectivity
    candidates = sorted([p for p in exo], key=lambda p: (p in skeleton, abs(p[0] - cx) + abs(p[1] - cy)), reverse=True)
    current = exo.copy()
    for c in candidates:
        if len(current) <= total_mods:
            break
        test = current - {c}
        if is_connected(test):
            current = test
    return current

def _find_connected_components(positions: Set[Pos]) -> List[Set[Pos]]:
    components = []
    rem = set(positions)
    while rem:
        start = next(iter(rem))
        comp = set()
        q = deque([start])
        visited = {start}
        while q:
            cur = q.popleft()
            comp.add(cur)
            rem.discard(cur)
            for n in neighbors4_unbounded(cur):
                if n in rem and n not in visited:
                    visited.add(n)
                    q.append(n)
        components.append(comp)
    return components

def _connect_components(components: List[Set[Pos]], center_cell: Optional[Pos]) -> Set[Pos]:
    if not components:
        return set()
    components.sort(key=len, reverse=True)
    exo = components[0].copy()
    for other in components[1:]:
        # find closest pair
        best = (None, None, float('inf'))
        for a in exo:
            for b in other:
                d = abs(a[0]-b[0]) + abs(a[1]-b[1])
                if d < best[2]:
                    best = (a, b, d)
        a, b, _ = best
        if a is None:
            continue
        # Manhattan path
        x1, y1 = a; x2, y2 = b
        path = set()
        for x in range(min(x1,x2), max(x1,x2)+1):
            path.add((x, y1))
        for y in range(min(y1,y2), max(y1,y2)+1):
            path.add((x2, y))
        for p in path:
            if p != center_cell:
                exo.add(p)
        exo.update(other)
    if center_cell:
        exo.discard(center_cell)
    return exo

# -----------------------
# UI & console helpers
# -----------------------
def _env_to_console_matrix(positions: Set[Pos]) -> List[List[str]]:
    if not positions:
        return [["0"]]
    min_x = min(x for x, _ in positions)
    max_x = max(x for x, _ in positions)
    min_y = min(y for _, y in positions)
    max_y = max(y for _, y in positions)
    w = max_x - min_x + 1
    h = max_y - min_y + 1
    grid = [["0" for _ in range(w)] for _ in range(h)]
    for x, y in positions:
        gx = x - min_x
        gy = max_y - y 
        grid[gy][gx] = "1"
    return grid

def _print_console_matrix(positions: Set[Pos], title: Optional[str] = None) -> None:
    if title:
        print(title)
    grid = _env_to_console_matrix(positions)
    for row in grid:
        print("".join(row))
    print()

def _ui_update_from_positions(ui, positions: Set[Pos], keep_centered: bool = True):
    """
    Update UI matrix from absolute positions.
    If keep_centered (A option) -> translate positions so bounding box is centered in UI.
    Assumes ui has attributes: matrix (2D list) and methods update_matrix(new_matrix), update_phase_label(text).
    """
    if ui is None:
        return
    # current UI size
    rows = len(ui.matrix)
    cols = len(ui.matrix[0]) if rows>0 else 0
    if not positions:
        ui.update_matrix([[0]*cols for _ in range(rows)])
        return
    min_x = min(x for x, _ in positions)
    max_x = max(x for x, _ in positions)
    min_y = min(y for _, y in positions)
    max_y = max(y for _, y in positions)
    exo_w = max_x - min_x + 1
    exo_h = max_y - min_y + 1

    # create a matrix sized to UI but place exo centered
    target_h = rows
    target_w = cols
    # If UI matrix size is 0, create bounding box of exo
    if target_h == 0 or target_w == 0:
        target_h = exo_h
        target_w = exo_w

    new_matrix = [[0 for _ in range(target_w)] for _ in range(target_h)]
    # top-left corner for centering
    offset_x = (target_w - exo_w) // 2
    offset_y = (target_h - exo_h) // 2

    for (x, y) in positions:
        gx = x - min_x + offset_x
        gy = y - min_y + offset_y
        # transform to GUI coords (row-major with top row index 0)
        gui_row = target_h - 1 - gy
        gui_col = gx
        if 0 <= gui_row < target_h and 0 <= gui_col < target_w:
            new_matrix[gui_row][gui_col] = 1

    ui.update_matrix(new_matrix)

# -----------------------
# Movement logic
# -----------------------
def _assign_modules_to_targets(env: Environment, target_exo: Set[Pos]) -> Dict[int, Pos]:
    """Greedy assignment module id -> target position (nearest)."""
    assignments: Dict[int, Pos] = {}
    remaining = set(target_exo)
    for mid in sorted(env.modules.keys()):
        if not remaining:
            break
        src = env.modules[mid].pos
        # Use min with Manhattan distance
        best = min(remaining, key=lambda t: abs(t[0]-src[0]) + abs(t[1]-src[1]))
        assignments[mid] = best
        remaining.remove(best)
    return assignments

def _proposed_cardinal_step(src: Pos, tgt: Pos):
    """Return Move that reduces Manhattan distance by 1 (cardinal)."""
    if src == tgt:
        return None
    x0,y0 = src; x1,y1 = tgt
    dx = x1 - x0; dy = y1 - y0
    if abs(dx) >= abs(dy):
        if dx > 0: return Move.EAST
        if dx < 0: return Move.WEST
    if abs(dy) >= abs(dx):
        if dy > 0: return Move.NORTH
        if dy < 0: return Move.SOUTH
    return None

def _select_safe_moves(env: Environment, proposals: Dict[int, Move]) -> Dict[int, Move]:
    """
    Try to select a maximal subset of proposed moves that preserves connectivity.
    If none or selection empty, try to allow a single move that preserves connectivity (one-module moves).
    
    CRITICAL: Adds deterministic tie-breaking for the greedy selection.
    """
    if not proposals:
        return {}

    positions = {mid: env.modules[mid].pos for mid in proposals}
    targets = {mid: (positions[mid][0]+mv.delta[0], positions[mid][1]+mv.delta[1]) for mid,mv in proposals.items()}

    # Build conflict graph: same target or swapping
    conflicts: Dict[int, Set[int]] = {m:set() for m in proposals}
    mids = list(proposals.keys())
    for i in range(len(mids)):
        A = mids[i]
        for j in range(i+1, len(mids)):
            B = mids[j]
            # Conflict if they target the same spot, or if they swap places
            if targets[A] == targets[B] or (targets[A] == positions[B] and targets[B] == positions[A]):
                conflicts[A].add(B); conflicts[B].add(A)

    selected: Set[int] = set()
    remaining: Set[int] = set(proposals.keys())
    current_occ: Set[Pos] = set(env.grid.occupied.keys())

    # Greedy choose candidate with fewest conflicts, with module ID tie-breaker
    while remaining:
        # Prioritize candidate with fewest conflicts, then lowest module ID for deterministic tie-breaking
        cand = min(remaining, key=lambda m: (len(conflicts[m] & remaining), m))
        
        trial = selected | {cand}
        
        # Simulate move for the set of candidates 'trial'
        occ_after = current_occ.copy()
        for mid in trial:
            occ_after.discard(positions[mid]) # Remove current positions
        for mid in trial:
            occ_after.add(targets[mid]) # Add target positions
            
        if is_connected(occ_after):
            selected.add(cand)
            # remove conflicting ones (can't move same target, etc.)
            remaining.remove(cand)
            # Remove direct conflicts of 'cand' from remaining, as they can no longer be chosen in this step
            remaining -= (conflicts[cand] & remaining) 
        else:
            remaining.remove(cand) # Can't move 'cand' with current 'selected' set

    if selected:
        return {mid: proposals[mid] for mid in selected}

    # if none multi-move safe, try single moves (select one that preserves connectivity)
    # The sorting here is based on module ID (since distance reduction is always 1), which is deterministic
    for mid, mv in sorted(proposals.items(), key=lambda it: (abs(env.modules[it[0]].pos[0]- (env.modules[it[0]].pos[0] + it[1].delta[0])) + abs(env.modules[it[0]].pos[1] - (env.modules[it[0]].pos[1] + it[1].delta[1])), it[0])):
        occ_after = set(env.grid.occupied.keys())
        src = env.modules[mid].pos
        tgt = (src[0]+mv.delta[0], src[1]+mv.delta[1])
        occ_after.discard(src)
        occ_after.add(tgt)
        if is_connected(occ_after):
            return {mid: mv}

    return {}

# -----------------------
# Main API: compute exoskeleton and stepwise move modules
# -----------------------
def compute_exoskeleton_from_env(env: Environment, ui=None, max_iters: int = 10000, return_steps: bool=False):
    """
    1) compute target exoskeleton (skeleton + shell), leaving center empty
    2) iteratively move modules (one or more per step) toward assigned targets while preserving connectivity
    3) update UI after every step and print console matrix
    Returns final positions (set of Pos) or list of steps if return_steps True.
    """
    occupied = set(env.grid.occupied.keys())
    if not occupied:
        if ui:
            _ui_update_from_positions(ui, set())
        return set() if not return_steps else []

    min_x = min(x for x,_ in occupied); max_x = max(x for x,_ in occupied)
    min_y = min(y for _,y in occupied); max_y = max(y for _,y in occupied)
    total_mods = len(occupied)

    # Build target: skeleton + shell
    skeleton = _build_skeleton(occupied, max_x, max_y)
    shell = _build_shell(skeleton)
    target_exo = skeleton | shell

    # leave center empty (so modules can slide around)
    center_cell = _calculate_center(target_exo)
    if center_cell and center_cell in target_exo:
        target_exo.discard(center_cell)

    # Balance count: if target larger/smaller, pick nearest to center_of_mass
    cx, cy = _get_center_of_mass(occupied)
    if len(target_exo) > total_mods:
        target_sorted = sorted(list(target_exo), key=lambda p: (abs(p[0]-cx)+abs(p[1]-cy)))
        target_exo = set(target_sorted[:total_mods])
    elif len(target_exo) < total_mods:
        candidates = _generate_candidates(min_x, max_x, min_y, max_y, target_exo, center_cell)
        candidates.sort(key=lambda p: abs(p[0]-cx)+abs(p[1]-cy))
        for c in candidates:
            if len(target_exo) >= total_mods:
                break
            target_exo.add(c)
        # ensure center removed
        if center_cell and center_cell in target_exo:
            target_exo.discard(center_cell)

    # ensure final target connected; if not, connect components via shortest paths
    if not is_connected(target_exo):
        comps = _find_connected_components(target_exo)
        target_exo = _connect_components(comps, center_cell)
        # trim if too many
        if len(target_exo) > total_mods:
            target_exo = _trim_exoskeleton_unsafe(target_exo, skeleton, total_mods, cx, cy)
        if center_cell and center_cell in target_exo:
            target_exo.discard(center_cell)

    # Assignment (initial) - not strictly necessary here but left for clarity
    assignments = _assign_modules_to_targets(env, target_exo)

    steps_executed: List[Dict[int, Move]] = []
    it = 0
    # Start iterative movement loop
    while it < max_iters:
        it += 1
        # recompute assignments each iteration (greedy)
        assignments = _assign_modules_to_targets(env, target_exo)

        # proposals: move each module one cardinal step towards its assigned target
        proposals: Dict[int, Move] = {}
        for mid, tgt in assignments.items():
            src = env.modules[mid].pos
            mv = _proposed_cardinal_step(src, tgt)
            if mv is not None and mv != Move.STAY:
                proposals[mid] = mv

        if not proposals:
            # no proposals -> reached target positions
            print(f"Step {it}: no more moves; modules at targets (or cannot propose).")
            break

        # select safe moves (maximal preserving connectivity, else single)
        selected = _select_safe_moves(env, proposals)
        if not selected:
            # stuck: cannot move without breaking connectivity
            print(f"Step {it}: cannot move further without breaking connectivity. Stopping.")
            break

        # apply moves via env.step(selected)
        # env.step expects dict {module_id: Move}
        
        env.step(deepcopy(selected))
        steps_executed.append(selected.copy())

        # Console + UI update
        print(f"Step {it}: executed {len(selected)} moves")
        for mid, mv in selected.items():
            cur = env.modules[mid].pos
            prev = (cur[0]-mv.delta[0], cur[1]-mv.delta[1])
            print(f"  Module {mid}: {prev} -> {cur} ({mv.name})")

        final_positions = set(env.grid.occupied.keys())
        _print_console_matrix(final_positions, title=f"After step {it} (console view):")
        if ui:
            _ui_update_from_positions(ui, final_positions, keep_centered=True)
            # also update a phase label if exists
            try:
                ui.update_phase_label(f"Phase 1: step {it}")
            except Exception:
                pass

        # Check goal reached
        if final_positions == target_exo:
            print(f"All modules reached target exoskeleton at step {it}.")
            break

    # final adjustments: ensure final set is connected and has correct count
    final_occ = set(env.grid.occupied.keys())
    if len(final_occ) != total_mods:
        # try to correct by adding/removing near center
        if len(final_occ) > total_mods:
            final_occ = set(sorted(final_occ, key=lambda p: (abs(p[0]-cx)+abs(p[1]-cy)))[:total_mods])
        else:
            candidates = _generate_candidates(min_x, max_x, min_y, max_y, final_occ, center_cell)
            candidates.sort(key=lambda p: abs(p[0]-cx)+abs(p[1]-cy))
            for c in candidates:
                if len(final_occ) >= total_mods:
                    break
                final_occ.add(c)

    # final connectivity fix (last resort: connect components)
    if not is_connected(final_occ):
        comps = _find_connected_components(final_occ)
        final_occ = _connect_components(comps, center_cell)
        if len(final_occ) > total_mods:
            final_occ = set(sorted(final_occ, key=lambda p: (abs(p[0]-cx)+abs(p[1]-cy)))[:total_mods])
    # ensure center empty
    if center_cell and center_cell in final_occ:
        final_occ.discard(center_cell)

    # push final positions into environment (and UI)

    _update_env_positions(env, final_occ)
    if ui:
        _ui_update_from_positions(ui, final_occ, keep_centered=True)
        try:
            ui.update_phase_label("Phase 1: Exoskeleton Constructed")
        except Exception:
            pass
    _print_console_matrix(final_occ, title="Final exoskeleton (console view):")

    if return_steps:
        return steps_executed
    return final_occ

# helper that writes final positions back into env.grid.occupied and modules' pos
def _update_env_positions(env: Environment, final_occ: Set[Pos]) -> None:
    """
    Write final_occ into env.grid.occupied and update module positions to match.
    This function tries to keep module objects consistent: assign nearest modules to final positions.
    """
    # greedy assign modules to final positions by distance
    mods = sorted(env.modules.keys())
    remaining_targets = set(final_occ)
    assignments: Dict[int, Pos] = {}
    for mid in mods:
        pos = env.modules[mid].pos
        if not remaining_targets:
            break
        best = min(remaining_targets, key=lambda t: abs(t[0]-pos[0]) + abs(t[1]-pos[1]))
        assignments[mid] = best
        remaining_targets.remove(best)
    # apply by directly setting module.pos and env.grid.occupied
    env.grid.occupied.clear()
    for mid, tgt in assignments.items():
        env.modules[mid].pos = tgt
        env.grid.occupied[tgt] = True
    # If any leftover targets (more targets than modules mapping), add them
    for t in remaining_targets:
        env.grid.occupied[t] = True

