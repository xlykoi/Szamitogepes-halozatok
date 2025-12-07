from copy import deepcopy
from environment import Environment 
from structures.module import Module, Move 
from structures.skeleton import (
    compute_exoskeleton_from_env,
    _get_center_of_mass, 
    _find_closest_hole, 
    _is_move_connectivity_safe,
    _update_env_positions,
    is_connected,
    _select_safe_moves
)
from typing import Tuple, Set, Dict, List, Optional

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
            # Use _select_safe_moves to ensure connectivity and prevent collisions
            safe_movement_dict = _select_safe_moves(env, movement_dict)
            
            if safe_movement_dict:
                if env.step(safe_movement_dict):
                    # Verify connectivity after step
                    new_positions = set(env.grid.occupied.keys())
                    if not is_connected(new_positions):
                        print(f"[WARN] Phase 1 connectivity broken at step {i+1}. This should not happen.")
                    all_moves.append(safe_movement_dict)
                else:
                    print(f"[WARN] Phase 1 elakadás a {i+1}. lépésben.")
                    break
            else:
                print(f"[WARN] Phase 1 no safe moves at step {i+1}.")
                if current_positions != exo_target:
                    print(f"[WARN] Phase 1 elakadás: nem érték el a cél alakzatot.")
                break
        else:
            if current_positions != exo_target:
                print(f"[WARN] Phase 1 elakadás: nem érték el a cél alakzatot.")
            break

    return all_moves


def phase1_transformation_plan(env: Environment, exo_target: Set[Pos]) -> List[Dict[int, Move]]:
   
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

    def __init__(self, ui):
        self.ui = ui
        self.env: Environment = None
        self.sim_env: Environment = None
        self.initial_env: Environment = None
        self.done: bool = False

        self.steps: List[Dict[int, Move]] = []  # lépések queue-ja
        self.has_prepared: bool = False


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


    def _update_ui_with_env(self, env: Environment):
        final_positions = {mod.pos for mod in env.modules.values() if mod.pos is not None}
        
        module_count = len(env.modules)
        positions_count = len(final_positions)
        if module_count != positions_count:
            print(f"[Phase1] WARNING: Module count mismatch! "
                  f"Modules: {module_count}, Positions: {positions_count}")
            
            none_pos_modules = [mid for mid, mod in env.modules.items() if mod.pos is None]
            if none_pos_modules:
                print(f"[Phase1] WARNING: {len(none_pos_modules)} modules have None position: {none_pos_modules}")
            
            position_to_modules: Dict[Pos, List[int]] = {}
            for mid, mod in env.modules.items():
                if mod.pos is not None:
                    if mod.pos not in position_to_modules:
                        position_to_modules[mod.pos] = []
                    position_to_modules[mod.pos].append(mid)
            
            duplicates = {pos: mids for pos, mids in position_to_modules.items() if len(mids) > 1}
            if duplicates:
                print(f"[Phase1] ERROR: {len(duplicates)} positions have multiple modules!")
                for pos, mids in duplicates.items():
                    print(f"[Phase1]   Position {pos} has {len(mids)} modules: {mids}")
                self._fix_duplicate_positions(env, duplicates)
                final_positions = {m.pos for m in env.modules.values() if m.pos is not None}
        
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
        
        matrix_module_count = sum(sum(row) for row in new_matrix)
        if matrix_module_count != len(final_positions):
            print(f"[Phase1] WARNING: Matrix module count mismatch! "
                  f"Expected {len(final_positions)} modules, found {matrix_module_count} in matrix")
        
        self.ui.update_matrix(new_matrix)


    def execute_step(self):
        if self.done:
            print("-- Phase 1 finished")
            return True

        if not self.has_prepared:
            self.env, _ = self.build_env_from_ui()
            
            sim_env = deepcopy(self.env)
            
            exo_target = compute_exoskeleton_from_env(sim_env, ui=None, return_steps=False)
            
            phase1_steps = phase1_transformation(sim_env, exo_target)
            
            temp_env_for_steps = deepcopy(self.env)
            compute_steps = compute_exoskeleton_from_env(temp_env_for_steps, ui=None, return_steps=True)
            
            self.steps = compute_steps + phase1_steps
            
            self.final_positions = set(sim_env.grid.occupied.keys())
            
            self.has_prepared = True
            self.done = False
            
            self._update_ui_with_env(self.env)
            print(f"Phase 1 initialized. {len(self.steps)} steps planned.")
            return

        if not self.steps:
            if hasattr(self, 'final_positions'):
                _update_env_positions(self.env, self.final_positions)
            
            print("-- Phase 1 finished")
            self.done = True
            self._update_ui_with_env(self.env)
            self.ui.update_phase_label("Phase 1: Exoskeleton Constructed")
            return

        step = self.steps.pop(0)
        
        # Collision detection: check if multiple modules target the same position
        targets: Dict[int, Pos] = {}
        for mid, mv in step.items():
            if mid not in self.env.modules:
                continue
            mod = self.env.modules[mid]
            dx, dy = mv.delta
            tgt = (mod.pos[0] + dx, mod.pos[1] + dy)
            if not self.env.grid.in_bounds(tgt):
                tgt = mod.pos
            targets[mid] = tgt
        
        position_to_modules: Dict[Pos, List[int]] = {}
        for mid, tgt in targets.items():
            if tgt not in position_to_modules:
                position_to_modules[tgt] = []
            position_to_modules[tgt].append(mid)
        
        # Filter out collisions - only allow one module per target position
        safe_step: Dict[int, Move] = {}
        for pos, module_ids in position_to_modules.items():
            if len(module_ids) > 1:
                module_ids.sort()
                print(f"[Phase1] WARNING: Collision detected at {pos}! Modules {module_ids} all targeting same position.")
                print(f"[Phase1] Only allowing module {module_ids[0]} to move, others will stay in place.")
                mid = module_ids[0]
                safe_step[mid] = step[mid]
            else:
                mid = module_ids[0]
                safe_step[mid] = step[mid]
        
        # Use _select_safe_moves to ensure connectivity
        connectivity_safe_step = _select_safe_moves(self.env, safe_step)
        
        if not connectivity_safe_step:
            print(f"[Phase1] WARNING: No connectivity-safe moves in step. Skipping step.")
            if not self.steps:
                if hasattr(self, 'final_positions'):
                    _update_env_positions(self.env, self.final_positions)
                self.done = True
                self._update_ui_with_env(self.env)
                self.ui.update_phase_label("Phase 1: Exoskeleton Constructed")
            return
        
        success = self.env.step(connectivity_safe_step)
        
        if not success:
            print(f"Warning: Step execution failed. Skipping step.")
            if not self.steps:
                if hasattr(self, 'final_positions'):
                    _update_env_positions(self.env, self.final_positions)
                self.done = True
                self._update_ui_with_env(self.env)
                self.ui.update_phase_label("Phase 1: Exoskeleton Constructed")
            return
        
        # Verify connectivity after step
        new_positions = {mod.pos for mod in self.env.modules.values() if mod.pos is not None}
        if not is_connected(new_positions):
            print(f"[Phase1] ERROR: Connectivity broken after step! This should not happen.")
        
        # Sync grid with module positions
        self._sync_grid_with_modules()

        print(f"Step executed: {len(connectivity_safe_step)} modules moved")
        for mid, mv in connectivity_safe_step.items():
            cur_pos = self.env.modules[mid].pos
            prev_pos = (cur_pos[0] - mv.delta[0], cur_pos[1] - mv.delta[1])
            print(f"  Module {mid}: {prev_pos} -> {cur_pos} ({mv.name})")

        self._update_ui_with_env(self.env)
            
      


    def execute_phase(self):
        self.env, _ = self.build_env_from_ui()
        exo_target = compute_exoskeleton_from_env(self.env)

        movement_list = phase1_transformation(self.env, exo_target)

        self._update_ui_with_env(self.env)

        self.ui.update_phase_label(
            f"Phase 1: Exoskeleton Constructed ({len(movement_list)} steps)"
        )
        print("Phase 1 completed successfully.")
    
    def _fix_duplicate_positions(self, env: Environment, duplicates: Dict[Pos, List[int]]):
        """Fix duplicate positions by moving modules to empty, connectivity-safe positions."""
        from collections import deque
        from typing import Optional
        
        print(f"[Phase1] Fixing {len(duplicates)} duplicate positions...")
        
        occupied = {mod.pos for mod in env.modules.values() if mod.pos is not None}
        occupied.update(env.grid.occupied.keys())
        
        fixed_count = 0
        failed_count = 0
        all_moves = {}
        
        for pos, module_ids in duplicates.items():
            module_ids.sort()
            modules_to_move = module_ids[1:]
            
            for mid in modules_to_move:
                mod = env.modules[mid]
                old_pos = mod.pos
                
                empty_pos = self._find_nearest_empty_position_connectivity_safe(pos, occupied, env, old_pos)
                
                if empty_pos:
                    if empty_pos in occupied or empty_pos in env.grid.occupied:
                        if empty_pos in all_moves.values():
                            empty_pos = self._find_nearest_empty_position_connectivity_safe(pos, occupied, env, old_pos, exclude=set(all_moves.values()))
                            if not empty_pos:
                                print(f"[Phase1] ERROR: Could not find connectivity-safe position for module {mid}!")
                                failed_count += 1
                                continue
                        else:
                            print(f"[Phase1] WARNING: Position {empty_pos} is occupied! Skipping module {mid}.")
                            failed_count += 1
                            continue
                    
                    test_positions = occupied.copy()
                    test_positions.discard(old_pos)
                    test_positions.add(empty_pos)
                    if not is_connected(test_positions):
                        print(f"[Phase1] ERROR: Position {empty_pos} breaks connectivity! Skipping module {mid}.")
                        failed_count += 1
                        continue
                    
                    all_moves[mid] = empty_pos
                    occupied.discard(old_pos)
                    occupied.add(empty_pos)
                    fixed_count += 1
                else:
                    print(f"[Phase1] ERROR: Could not find connectivity-safe empty position for module {mid}!")
                    failed_count += 1
        
        for mid, new_pos in all_moves.items():
            mod = env.modules[mid]
            old_pos = mod.pos
            
            current_positions = {m.pos for m in env.modules.values() if m.pos is not None}
            test_positions = current_positions.copy()
            test_positions.discard(old_pos)
            test_positions.add(new_pos)
            
            if not is_connected(test_positions):
                print(f"[Phase1] ERROR: Moving module {mid} to {new_pos} would break connectivity! Skipping this move.")
                failed_count += 1
                continue
            
            print(f"[Phase1] Moving module {mid} from duplicate position {old_pos} to {new_pos} (connectivity-safe)")
            
            mod.pos = new_pos
            
            if old_pos in env.grid.occupied:
                if env.grid.occupied[old_pos] == mid:
                    env.grid.remove(old_pos)
            
            env.grid.place(mid, new_pos)
            
            new_positions = {m.pos for m in env.modules.values() if m.pos is not None}
            if not is_connected(new_positions):
                print(f"[Phase1] ERROR: Connectivity broken after moving module {mid}! Reverting move.")
                mod.pos = old_pos
                env.grid.remove(new_pos)
                env.grid.place(mid, old_pos)
                failed_count += 1
                continue
        
        print(f"[Phase1] Duplicate fix complete: {fixed_count} modules moved, {failed_count} failed")
        
        final_positions = {m.pos for m in env.modules.values() if m.pos is not None}
        if not is_connected(final_positions):
            print(f"[Phase1] ERROR: Connectivity broken after duplicate fix! This should not happen.")
        
        self._sync_grid_with_modules()
    
    def _find_nearest_empty_position_connectivity_safe(self, start_pos: Pos, occupied: Set[Pos], env: Environment, module_pos: Pos, exclude: Optional[Set[Pos]] = None) -> Optional[Pos]:
        """Find nearest empty position that maintains connectivity."""
        from collections import deque
        
        if exclude is None:
            exclude = set()
        
        MAX_SEARCH_DISTANCE = 100
        MAX_VISITED = 2000
        
        queue = deque([(start_pos, 0)])
        visited = {start_pos}
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        while queue and len(visited) < MAX_VISITED:
            current, dist = queue.popleft()
            
            if dist > MAX_SEARCH_DISTANCE:
                continue
            
            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                
                if not env.grid.in_bounds(neighbor):
                    continue
                
                neighbor_dist = abs(neighbor[0] - start_pos[0]) + abs(neighbor[1] - start_pos[1])
                if neighbor_dist > MAX_SEARCH_DISTANCE:
                    continue
                
                if neighbor in occupied or neighbor in env.grid.occupied or neighbor in exclude:
                    queue.append((neighbor, neighbor_dist))
                    continue
                
                test_positions = occupied.copy()
                test_positions.discard(module_pos)
                test_positions.add(neighbor)
                
                if is_connected(test_positions):
                    return neighbor
                
                queue.append((neighbor, neighbor_dist))
        
        if len(visited) >= MAX_VISITED:
            print(f"[Phase1] WARNING: Search limit reached ({MAX_VISITED} positions) while looking for connectivity-safe empty position near {start_pos}")
        
        return None
    
    def _sync_grid_with_modules(self):
        """Sync grid with module positions, removing duplicates and ensuring consistency."""
        self.env.grid.occupied.clear()
        
        position_to_modules: Dict[Pos, List[int]] = {}
        for mid, mod in self.env.modules.items():
            if mod.pos is not None:
                if mod.pos not in position_to_modules:
                    position_to_modules[mod.pos] = []
                position_to_modules[mod.pos].append(mid)
        
        for pos, module_ids in position_to_modules.items():
            if len(module_ids) > 1:
                print(f"[Phase1] WARNING: Grid sync found {len(module_ids)} modules at position {pos}: {module_ids}")
                module_ids.sort()
                keep_module = module_ids[0]
                modules_to_fix = module_ids[1:]
                
                self.env.grid.place(keep_module, pos)
                
                for mid in modules_to_fix:
                    mod = self.env.modules[mid]
                    occupied = {m.pos for m in self.env.modules.values() if m.pos is not None}
                    occupied.update(self.env.grid.occupied.keys())
                    empty_pos = self._find_nearest_empty_position_connectivity_safe(pos, occupied, self.env, pos)
                    if empty_pos:
                        test_positions = occupied.copy()
                        test_positions.discard(pos)
                        test_positions.add(empty_pos)
                        if is_connected(test_positions):
                            print(f"[Phase1] Moving duplicate module {mid} from {pos} to {empty_pos} during grid sync (connectivity-safe)")
                            mod.pos = empty_pos
                            self.env.grid.place(mid, empty_pos)
                        else:
                            print(f"[Phase1] ERROR: Position {empty_pos} breaks connectivity for module {mid} during grid sync!")
                    else:
                        print(f"[Phase1] ERROR: Could not find connectivity-safe empty position for duplicate module {mid} during grid sync!")
            else:
                self.env.grid.place(module_ids[0], pos)
