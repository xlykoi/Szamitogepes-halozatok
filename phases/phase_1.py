from copy import deepcopy
from environment import Environment 
from structures.module import Module, Move 
from structures.skeleton import (
    compute_exoskeleton_from_env,
    _get_center_of_mass, 
    _find_closest_hole, 
    _is_move_connectivity_safe
)
from typing import Tuple, Set, Dict, List

Pos = Tuple[int, int]


def _get_move_direction(source: Pos, target: Pos) -> Move:
    dx = target[0] - source[0]
    dy = target[1] - source[1]

    if abs(dx) + abs(dy) == 1:
        if dx == 1: return Move.EAST
        if dx == -1: return Move.WEST
        if dy == 1: return Move.NORTH
        if dy == -1: return Move.SOUTH

    return Move.STAY


def phase1_transformation(env: Environment, exo_target: Set[Pos]) -> List[Dict[int, Move]]:
    """Teljes Phase-1 átrendezés (ez marad a FULL RUN-nak)."""
    all_moves = []
    max_iterations = 2 * len(env.modules) ** 2

    for i in range(max_iterations):
        current_positions = set(env.grid.occupied.keys())

        if current_positions == exo_target:
            break

        holes_to_fill = exo_target - current_positions
        movement_dict = {}

        cx, cy = _get_center_of_mass(current_positions)

        movable_modules_sorted = sorted(
            list(env.modules.values()),
            key=lambda mod: (
                mod.pos in exo_target and not _find_closest_hole(mod.pos, holes_to_fill),
                abs(mod.pos[0] - cx) + abs(mod.pos[1] - cy)
            )
        )

        planned_target_positions = set()
        temp_holes = holes_to_fill.copy()

        for module in movable_modules_sorted:
            mid = module.id
            current_pos = module.pos
            target_pos = _find_closest_hole(current_pos, temp_holes)

            if target_pos:
                move = _get_move_direction(current_pos, target_pos)
                if move != Move.STAY and target_pos not in planned_target_positions:
                    if _is_move_connectivity_safe(current_positions, current_pos, target_pos):
                        movement_dict[mid] = move
                        planned_target_positions.add(target_pos)
                        temp_holes.discard(target_pos)
                        if current_pos in exo_target:
                            temp_holes.add(current_pos)

        if movement_dict:
            if env.step(movement_dict):
                all_moves.append(movement_dict)
            else:
                print(f"[WARN] Phase 1 elakadás a {i+1}. lépésben.")
                break
        else:
            if current_positions != exo_target:
                print(f"[WARN] Phase 1 elakadás: nem érték el a cél alakzatot.")
            break

    return all_moves


def phase1_transformation_plan(env: Environment, exo_target: Set[Pos]) -> List[Dict[int, Move]]:
    """
    Phase-1 lépések gyűjtése MÓDOSÍTÁS NÉLKÜL.
    
    Ez a függvény ugyanazt az algoritmust használja mint phase1_transformation,
    de nem módosítja az eredeti environment-et, csak visszaadja a lépéseket.
    
    Args:
        env: Environment to plan for (will NOT be modified)
        exo_target: Target exoskeleton positions
    
    Returns:
        List of movement dictionaries (one per step)
    """
    # Create a deep copy to work on, so original env is never modified
    working_env = deepcopy(env)
    
    all_moves = []
    max_iterations = 2 * len(working_env.modules) ** 2

    for i in range(max_iterations):
        current_positions = set(working_env.grid.occupied.keys())

        if current_positions == exo_target:
            break

        holes_to_fill = exo_target - current_positions
        movement_dict = {}

        cx, cy = _get_center_of_mass(current_positions)

        movable_modules_sorted = sorted(
            list(working_env.modules.values()),
            key=lambda mod: (
                mod.pos in exo_target and not _find_closest_hole(mod.pos, holes_to_fill),
                abs(mod.pos[0] - cx) + abs(mod.pos[1] - cy)
            )
        )

        planned_target_positions = set()
        temp_holes = holes_to_fill.copy()

        for module in movable_modules_sorted:
            mid = module.id
            current_pos = module.pos
            target_pos = _find_closest_hole(current_pos, temp_holes)

            if target_pos:
                move = _get_move_direction(current_pos, target_pos)
                if move != Move.STAY and target_pos not in planned_target_positions:
                    if _is_move_connectivity_safe(current_positions, current_pos, target_pos):
                        movement_dict[mid] = move
                        planned_target_positions.add(target_pos)
                        temp_holes.discard(target_pos)
                        if current_pos in exo_target:
                            temp_holes.add(current_pos)

        if movement_dict:
            if working_env.step(movement_dict):
                all_moves.append(movement_dict)
            else:
                print(f"[WARN] Phase 1 elakadás a {i+1}. lépésben (planning).")
                break
        else:
            if current_positions != exo_target:
                print(f"[WARN] Phase 1 elakadás: nem érték el a cél alakzatot (planning).")
            break

    return all_moves


class Phase1:
    """Phase 1 kezelés UI snapshot queue-val (mint Phase 3)."""

    def __init__(self, ui):
        self.ui = ui
        self.env: Environment = None
        self.sim_env: Environment = None
        self.initial_env: Environment = None
        self.done: bool = False

        self.steps: List[Dict[int, Move]] = []  # lépések queue-ja
        self.has_prepared: bool = False


    # ----------------------------
    # ENV építés UI-ból
    # ----------------------------

    def build_env_from_ui(self) -> Tuple[Environment, int]:
        matrix = self.ui.matrix
        rows = len(matrix)
        if rows == 0:
            return Environment(), 1

        cols = len(matrix[0])
        env = Environment()
        mid = 1

        for y in range(rows):
            for x in range(cols):
                if matrix[y][x] == 1:
                    grid_pos = (x, rows - 1 - y)
                    env.add_module(Module(mid, grid_pos))
                    mid += 1

        return env, mid


    # ----------------------------
    # UI update bounding box-szal
    # ----------------------------

    def _update_ui_with_env(self, env: Environment):
        """Update UI with environment state using bounding box."""
        # Use actual module positions
        final_positions = {mod.pos for mod in env.modules.values()}
        
        if not final_positions:
            self.ui.update_matrix([[]])
            return
        
        all_x = [p[0] for p in final_positions]
        all_y = [p[1] for p in final_positions]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        rows = max_y - min_y + 1
        cols = max_x - min_x + 1
        new_matrix = [[0 for _ in range(cols)] for _ in range(rows)]
        
        for x, y in final_positions:
            gui_x = x - min_x
            gui_y = max_y - y
            if 0 <= gui_y < rows and 0 <= gui_x < cols:
                new_matrix[gui_y][gui_x] = 1
        
        self.ui.update_matrix(new_matrix)


    def execute_step(self):
        self.env, _ = self.build_env_from_ui()
        exo_target = compute_exoskeleton_from_env(self.env)

        movement_list = phase1_transformation(self.env, exo_target)

        self._update_ui_with_env(self.env)

        self.ui.update_phase_label(
            f"Phase 1: Exoskeleton Constructed ({len(movement_list)} steps)"
        )
            


    # ----------------------------
    # TELJES Phase-1 végrehajtása
    # ----------------------------

    def execute_phase(self):
        """FULL RUN: minden lépés egyszerre kerül végrehajtásra."""
        print("Executing Phase 1: Building Exoskeleton (Full Run)")

        self.env, _ = self.build_env_from_ui()
        exo_target = compute_exoskeleton_from_env(self.env)

        movement_list = phase1_transformation(self.env, exo_target)

        self._update_ui_with_env(self.env)

        self.ui.update_phase_label(
            f"Phase 1: Exoskeleton Constructed ({len(movement_list)} steps)"
        )
        print("Phase 1 completed successfully.")
