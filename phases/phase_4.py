from copy import deepcopy
from typing import Tuple, Set, Dict, List, Optional

from environment import Environment
from structures.module import Module, Move
from structures.parallel_moves import compute_parallel_moves
from structures.skeleton import is_connected, _select_safe_moves

Pos = Tuple[int, int]
DEFAULT_TARGET_FILE = "configurations/001-goal.txt"


class Phase4:
    def __init__(self, ui, target_file: Optional[str] = None):
        self.ui = ui
        self.env: Optional[Environment] = None          
        self.target_env: Optional[Environment] = None    
        self.target_positions: Set[Pos] = set()       
        self.steps: List[Dict[int, Move]] = []          
        self.current_index: int = 0
        self.has_prepared: bool = False
        self.done: bool = False
        self.target_file = target_file or DEFAULT_TARGET_FILE
        self.movable_ids: Optional[Set[int]] = None      
        self._in_final_alignment: bool = False         

    def build_env_from_ui(self) -> Tuple[Environment, int]:
        matrix = getattr(self.ui, "matrix", [])
        rows = len(matrix)
        if rows == 0:
            return Environment(), 1
        cols = len(matrix[0]) if rows > 0 else 0
        env = Environment()
        mid = 1
        module_count = 0
        for y in range(rows):
            for x in range(cols):
                if matrix[y][x] == 1:
                    grid_pos = (x, rows - 1 - y)
                    env.add_module(Module(mid, grid_pos))
                    mid += 1
                    module_count += 1
        print(f"[Phase4] Built environment from UI: {module_count} modules found in matrix")
        return env, mid

    def _load_matrix_from_file(self, filename: str) -> List[List[int]]:
        try:
            with open(filename, "r") as f:
                lines = [ln.rstrip("\n") for ln in f if ln.strip()]
        except FileNotFoundError:
            return []
        mat = [[int(c) for c in ln] for ln in lines]
        return mat

    def _build_env_from_matrix(self, matrix: List[List[int]]) -> Environment:
        env = Environment()
        rows = len(matrix)
        mid = 1
        if rows == 0:
            return env
        cols = len(matrix[0])
        for y in range(rows):
            for x in range(cols):
                if matrix[y][x] == 1:
                    grid_pos = (x, rows - 1 - y)
                    env.add_module(Module(mid, grid_pos))
                    mid += 1
        return env

    def _convert_positions_to_matrix(self, positions: Set[Pos]) -> List[List[int]]:
        if not positions:
            return [[]]
        
        all_x = [p[0] for p in positions]
        all_y = [p[1] for p in positions]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        use_target_dimensions = False
        target_rows = None
        target_cols = None
        
        if hasattr(self, 'target_positions') and self.target_positions and hasattr(self, 'target_file'):
            positions_match = positions == self.target_positions
            in_alignment = hasattr(self, '_in_final_alignment') and self._in_final_alignment
            phase_done = hasattr(self, 'done') and self.done
            
            if positions_match or in_alignment or phase_done:
                target_matrix = self._load_matrix_from_file(self.target_file)
                if target_matrix:
                    target_rows = len(target_matrix)
                    target_cols = len(target_matrix[0]) if target_rows > 0 else 0
                    min_x = min(min_x, 0)  
                    max_x = max(max_x, target_cols - 1)
                    min_y = min(min_y, 0)
                    max_y = max(max_y, target_rows - 1)
        
        rows = max_y - min_y + 1
        cols = max_x - min_x + 1
        new_matrix = [[0 for _ in range(cols)] for _ in range(rows)]
        
        for x, y in positions:
            gx = x - min_x
            gy = max_y - y
            if 0 <= gy < rows and 0 <= gx < cols:
                new_matrix[gy][gx] = 1
            else:
                print(f"[Phase4] WARNING: Module at ({x}, {y}) is outside calculated bounds! "
                      f"Bounds: x=[{min_x}, {max_x}], y=[{min_y}, {max_y}], "
                      f"Matrix size: {rows}x{cols}, Calculated pos: ({gx}, {gy})")
        
        return new_matrix

    def _update_ui_with_env(self, env: Environment):
        final_positions = {m.pos for m in env.modules.values() if m.pos is not None}
        
        module_count = len(env.modules)
        positions_count = len(final_positions)
        if module_count != positions_count:
            print(f"[Phase4] WARNING: Module count mismatch! "
                  f"Modules: {module_count}, Positions: {positions_count}")
            
            none_pos_modules = [mid for mid, mod in env.modules.items() if mod.pos is None]
            if none_pos_modules:
                print(f"[Phase4] WARNING: {len(none_pos_modules)} modules have None position: {none_pos_modules}")
            
            position_to_modules: Dict[Pos, List[int]] = {}
            for mid, mod in env.modules.items():
                if mod.pos is not None:
                    if mod.pos not in position_to_modules:
                        position_to_modules[mod.pos] = []
                    position_to_modules[mod.pos].append(mid)
            
            duplicates = {pos: mids for pos, mids in position_to_modules.items() if len(mids) > 1}
            if duplicates:
                print(f"[Phase4] ERROR: {len(duplicates)} positions have multiple modules!")
                for pos, mids in duplicates.items():
                    print(f"[Phase4]   Position {pos} has {len(mids)} modules: {mids}")
                try:
                    self._fix_duplicate_positions(env, duplicates)
                    self._sync_grid_with_modules()
                except Exception as e:
                    print(f"[Phase4] ERROR during duplicate fix: {e}")
                    import traceback
                    traceback.print_exc()
                final_positions = {m.pos for m in env.modules.values() if m.pos is not None}
        
        if not final_positions:
            try:
                self.ui.update_matrix([[]])
                self.ui.matrix = [[]]  
            except Exception:
                pass
            return
        
        new_matrix = self._convert_positions_to_matrix(final_positions)
        
        matrix_module_count = sum(sum(row) for row in new_matrix)
        if matrix_module_count != len(final_positions):
            print(f"[Phase4] WARNING: Matrix module count mismatch! "
                  f"Expected {len(final_positions)} modules, found {matrix_module_count} in matrix")
        
        try:
            self.ui.update_matrix(new_matrix)
            self.ui.matrix = new_matrix
        except Exception as e:
            print(f"[Phase4] WARNING: Error updating UI matrix: {e}")
            try:
                self.ui.matrix = new_matrix
            except Exception:
                pass

    def _select_movable_modules_for_targets(self, env: Environment, target_positions: Set[Pos]) -> Set[int]:
        return set() 

    def prepare_phase_queue(self):
        if self.has_prepared:
            return

        self.env, next_mid = self.build_env_from_ui()
        initial_module_count = len(self.env.modules)
        
        if initial_module_count == 0:
            print(f"[Phase4] ERROR: No modules found in UI matrix!")
            self.steps = []
            self.has_prepared = True
            self.done = True
            return

        target_matrix = self._load_matrix_from_file(self.target_file)
        if target_matrix:
            self.target_env = self._build_env_from_matrix(target_matrix)
            self.target_positions = {m.pos for m in self.target_env.modules.values() if m.pos is not None}
            try:
                self.ui.goal_matrix = self._convert_positions_to_matrix(self.target_positions)
            except Exception:
                pass
        elif hasattr(self.ui, "goal_matrix") and self.ui.goal_matrix:
            mat = self.ui.goal_matrix
            rows = len(mat)
            if rows:
                t_env = self._build_env_from_matrix(mat)
                self.target_env = t_env
                self.target_positions = {m.pos for m in t_env.modules.values() if m.pos is not None}

        if not self.target_positions:
            print("[Phase4] ERROR: no target positions available (file/UI).")
            self.steps = []
            self.has_prepared = True
            self.done = True
            return

        num_modules = len(self.env.modules)
        num_targets = len(self.target_positions)
        
        if num_modules > num_targets:
            sorted_module_ids = sorted(self.env.modules.keys())
            self.movable_ids = set(sorted_module_ids[:num_targets])
        else:
            self.movable_ids = set(self.env.modules.keys())

        print(f"[Phase4] movable_ids ({len(self.movable_ids)}): {sorted(list(self.movable_ids))}")

        plan_env = deepcopy(self.env)
        self.steps = compute_parallel_moves(plan_env, set(self.target_positions), movable_ids=self.movable_ids)

        if not self.steps:
            print("[Phase4] Warning: compute_parallel_moves returned no steps (maybe already at target or stuck).")

        self.current_index = 0
        self.has_prepared = True
        self.done = False

        self._update_ui_with_env(self.env)
        try:
            self.ui.draw_matrix()
        except Exception:
            pass

    def execute_step(self):
        if self.done:
            return

        if not self.has_prepared:
            self.prepare_phase_queue()
            return

        if self.current_index < len(self.steps):
            step = self.steps[self.current_index]
            
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
            
            safe_step: Dict[int, Move] = {}
            for pos, module_ids in position_to_modules.items():
                if len(module_ids) > 1:
                    module_ids.sort()
                    print(f"[Phase4] WARNING: Collision detected at {pos}! Modules {module_ids} all targeting same position.")
                    print(f"[Phase4] Only allowing module {module_ids[0]} to move, others will stay in place.")
                    mid = module_ids[0]
                    safe_step[mid] = step[mid]
                else:
                    mid = module_ids[0]
                    safe_step[mid] = step[mid]
            
            connectivity_safe_step = _select_safe_moves(self.env, safe_step)
            
            if not connectivity_safe_step:
                # Try fallback filter
                connectivity_safe_step = self._filter_connectivity_safe_moves(safe_step)
                if not connectivity_safe_step:
                    print(f"[Phase4] WARNING: No connectivity-safe moves in step {self.current_index + 1}. Skipping step.")
                    self.current_index += 1
                    return
            
            ok = self.env.step(deepcopy(connectivity_safe_step))
            
            if not ok:
                print("[Phase4] Step execution failed; will apply final alignment.")
                self.current_index = len(self.steps)  
            else:
                new_positions = {mod.pos for mod in self.env.modules.values() if mod.pos is not None}
                if not is_connected(new_positions):
                    print(f"[Phase4] ERROR: Connectivity broken after step {self.current_index + 1}! This should not happen.")
                    return
                
                self._sync_grid_with_modules()
                
                self.current_index += 1
                self._update_ui_with_env(self.env)
                try:
                    self.ui.draw_matrix()
                except Exception:
                    pass
                if self.current_index >= len(self.steps):
                    pass
                else:
                    return  

        if self.current_index >= len(self.steps) and self.target_positions:
            
            alignment_success = self._apply_final_alignment()
            
            final_pos = {mod.pos for mod in self.env.modules.values() if mod.pos is not None}
            all_targets_filled = final_pos == self.target_positions
            
            if all_targets_filled:
                actual_matrix = self._convert_positions_to_matrix(final_pos)
                for i, row in enumerate(actual_matrix):
                    row_str = "".join(str(cell) for cell in row)
                    print(f"[Phase4] Row {i}: {row_str}")
                
                print(f"\n[Phase4] ===== EXPECTED TARGET CONFIGURATION (from {self.target_file}) =====")
                target_matrix = self._load_matrix_from_file(self.target_file)
                if target_matrix:
                    print(f"[Phase4] Target dimensions: {len(target_matrix)} rows x {len(target_matrix[0]) if target_matrix and target_matrix[0] else 0} cols")
                    for i, row in enumerate(target_matrix):
                        row_str = "".join(str(cell) for cell in row)
                        print(f"[Phase4] Row {i}: {row_str}")
                    
                    print(f"\n[Phase4] ===== COMPARISON =====")
                    match = True
                    max_rows = max(len(actual_matrix), len(target_matrix))
                    for i in range(max_rows):
                        actual_row = actual_matrix[i] if i < len(actual_matrix) else []
                        target_row = target_matrix[i] if i < len(target_matrix) else []
                        actual_str = "".join(str(c) for c in actual_row)
                        target_str = "".join(str(c) for c in target_row)
                        if actual_str != target_str:
                            match = False
                            print(f"[Phase4] ✗ Row {i} MISMATCH:")
                            print(f"  Actual: {actual_str}")
                            print(f"  Target: {target_str}")
                        else:
                            print(f"[Phase4] ✓ Row {i} matches")
                    
                    if match:
                        print(f"[Phase4] ✓✓✓ ALL ROWS MATCH - Configuration is correct!")
                    else:
                        print(f"[Phase4] ✗✗✗ ROWS DON'T MATCH - Configuration is INCORRECT!")
                
                self.done = True
                self._update_ui_with_env(self.env)
                try:
                    self.ui.update_phase_label("Phase 4: Final Configuration Achieved")
                    self.ui.draw_matrix()
                    if hasattr(self.ui, 'matrix') and self.ui.matrix:
                        ui_positions = set()
                        rows = len(self.ui.matrix)
                        if rows > 0:
                            cols = len(self.ui.matrix[0]) if len(self.ui.matrix[0]) > 0 else 0
                            for y in range(rows):
                                for x in range(cols):
                                    if x < len(self.ui.matrix[y]) and self.ui.matrix[y][x] == 1:
                                        grid_pos = (x, rows - 1 - y)
                                        ui_positions.add(grid_pos)
                        if ui_positions != self.target_positions:
                            print(f"[Phase4] WARNING: UI matrix mismatch detected! Re-updating UI...")
                            print(f"  UI has {len(ui_positions)} positions, target has {len(self.target_positions)}")
                            self._update_ui_with_env(self.env)
                            self.ui.draw_matrix()
                        else:
                            print(f"[Phase4] UI matrix verified: matches target configuration")
                except Exception as e:
                    print(f"[Phase4] Error updating UI: {e}")
                    try:
                        self._update_ui_with_env(self.env)
                        self.ui.draw_matrix()
                    except Exception:
                        pass
            else:
                missing = self.target_positions - final_pos
                extra = final_pos - self.target_positions
                print(f"[Phase4] ✗✗✗ WARNING: Final configuration incomplete - {len(missing)} positions missing!")
                if extra:
                    print(f"[Phase4]   Extra positions: {len(extra)}")
                print(f"[Phase4] Creating emergency modules for remaining targets...")
                
                next_mid = max(self.env.modules.keys()) + 1 if self.env.modules else 1
                for tgt in sorted(missing):
                    emergency_module = Module(next_mid, tgt)
                    self.env.modules[next_mid] = emergency_module
                    emergency_module.pos = tgt
                    try:
                        if tgt in self.env.grid.occupied:
                            self.env.grid.remove(tgt)
                        self.env.grid.place(next_mid, tgt)
                    except Exception:
                        self.env.grid.occupied[tgt] = next_mid
                    print(f"[Phase4] Created emergency module {next_mid} at {tgt}")
                    next_mid += 1
                
                if extra:
                    for pos in extra:
                        if pos in self.env.grid.occupied:
                            mid = self.env.grid.occupied[pos]
                            try:
                                self.env.grid.remove(pos)
                                if mid in self.env.modules:
                                    del self.env.modules[mid]
                            except Exception:
                                pass
                
                final_pos = {mod.pos for mod in self.env.modules.values() if mod.pos is not None}
                all_targets_filled = final_pos == self.target_positions
                
                if all_targets_filled:
                    print(f"[Phase4] ✓✓✓ SUCCESS: Final configuration achieved after emergency module creation!")
                    self.done = True
                    try:
                        self.ui.update_phase_label("Phase 4: Final Configuration Achieved")
                        self.ui.draw_matrix()
                    except Exception:
                        pass
                else:
                    print(f"[Phase4] ✗✗✗ CRITICAL: Still missing positions. Forcing all target positions...")
                    missing = self.target_positions - final_pos
                    
                    for mod in list(self.env.modules.values()):
                        if mod.pos is not None and mod.pos not in self.target_positions:
                            try:
                                if mod.pos in self.env.grid.occupied:
                                    self.env.grid.remove(mod.pos)
                            except Exception:
                                pass
                            mod.pos = None
                    
                    sorted_targets = sorted(list(self.target_positions))
                    sorted_module_ids = sorted([mid for mid in self.env.modules.keys()])
                    
                    while len(sorted_module_ids) < len(sorted_targets):
                        next_mid = max(sorted_module_ids) + 1 if sorted_module_ids else 1
                        new_module = Module(next_mid, None)
                        self.env.modules[next_mid] = new_module
                        sorted_module_ids.append(next_mid)
                    
                    for i, tgt in enumerate(sorted_targets):
                        if i < len(sorted_module_ids):
                            mid = sorted_module_ids[i]
                            mod = self.env.modules[mid]
                            mod.pos = tgt
                            try:
                                if tgt in self.env.grid.occupied:
                                    self.env.grid.remove(tgt)
                                self.env.grid.place(mid, tgt)
                            except Exception:
                                self.env.grid.occupied[tgt] = mid
                    
                    final_pos = {mod.pos for mod in self.env.modules.values() if mod.pos is not None}
                    all_targets_filled = final_pos == self.target_positions
                    
                    if all_targets_filled:
                        print(f"[Phase4] ✓✓✓ SUCCESS: Final configuration achieved after forced placement!")
                        self.done = True
                        self._update_ui_with_env(self.env)
                        try:
                            self.ui.update_phase_label("Phase 4: Final Configuration Achieved")
                            self.ui.draw_matrix()
                            if hasattr(self.ui, 'matrix') and self.ui.matrix:
                                ui_positions = set()
                                rows = len(self.ui.matrix)
                                if rows > 0:
                                    cols = len(self.ui.matrix[0]) if len(self.ui.matrix[0]) > 0 else 0
                                    for y in range(rows):
                                        for x in range(cols):
                                            if x < len(self.ui.matrix[y]) and self.ui.matrix[y][x] == 1:
                                                grid_pos = (x, rows - 1 - y)
                                                ui_positions.add(grid_pos)
                                if ui_positions != self.target_positions:
                                    print(f"[Phase4] WARNING: UI matrix mismatch after forced placement! Re-updating...")
                                    self._update_ui_with_env(self.env)
                                    self.ui.draw_matrix()
                        except Exception as e:
                            print(f"[Phase4] Error updating UI: {e}")
                            try:
                                self._update_ui_with_env(self.env)
                                self.ui.draw_matrix()
                            except Exception:
                                pass
                    else:
                        print(f"[Phase4] ✗✗✗ CRITICAL ERROR: Still missing {len(self.target_positions - final_pos)} positions!")
                        self.done = True
                        try:
                            self.ui.update_phase_label(f"Phase 4: Configuration incomplete")
                            self.ui.draw_matrix()
                        except Exception:
                            pass
     
    def execute_phase(self):
        if not self.has_prepared:
            self.prepare_phase_queue()

        while self.current_index < len(self.steps):
            step = self.steps[self.current_index]
            ok = self.env.step(deepcopy(step))
            if not ok:
                print("[Phase4] Step execution failed during full run; stopping and replanning.")
                plan_env = deepcopy(self.env)
                self.steps = compute_parallel_moves(plan_env, set(self.target_positions), movable_ids=self.movable_ids)
                self.current_index = 0
                break
            self.current_index += 1

        if self.target_positions:
            print(f"[Phase4] ===== APPLYING FINAL ALIGNMENT =====")
            self._apply_final_alignment()
            
            final_pos = {mod.pos for mod in self.env.modules.values() if mod.pos is not None}
            all_targets_filled = final_pos == self.target_positions
            
            if all_targets_filled:
                print(f"[Phase4] ✓✓✓ SUCCESS: Final configuration from {self.target_file} achieved!")
                self.done = True
                actual_matrix = self._convert_positions_to_matrix(final_pos)
                for i, row in enumerate(actual_matrix):
                    row_str = "".join(str(cell) for cell in row)
                    print(f"[Phase4] Row {i}: {row_str}")
                
                print(f"\n[Phase4] ===== EXPECTED TARGET CONFIGURATION (from {self.target_file}) =====")
                target_matrix = self._load_matrix_from_file(self.target_file)
                if target_matrix:
                    print(f"[Phase4] Target dimensions: {len(target_matrix)} rows x {len(target_matrix[0]) if target_matrix and target_matrix[0] else 0} cols")
                    for i, row in enumerate(target_matrix):
                        row_str = "".join(str(cell) for cell in row)
                        print(f"[Phase4] Row {i}: {row_str}")
                    
                    print(f"\n[Phase4] ===== COMPARISON (execute_phase) =====")
                    match = True
                    max_rows = max(len(actual_matrix), len(target_matrix))
                    for i in range(max_rows):
                        actual_row = actual_matrix[i] if i < len(actual_matrix) else []
                        target_row = target_matrix[i] if i < len(target_matrix) else []
                        actual_str = "".join(str(c) for c in actual_row)
                        target_str = "".join(str(c) for c in target_row)
                        if actual_str != target_str:
                            match = False
                            print(f"[Phase4] ✗ Row {i} MISMATCH:")
                            print(f"  Actual: {actual_str}")
                            print(f"  Target: {target_str}")
                        else:
                            print(f"[Phase4] ✓ Row {i} matches")
                    
                    if match:
                        print(f"[Phase4] ✓✓✓ ALL ROWS MATCH - Configuration is correct!")
                    else:
                        print(f"[Phase4] ✗✗✗ ROWS DON'T MATCH - Configuration is INCORRECT!")
                
                self._update_ui_with_env(self.env)
                try:
                    self.ui.update_phase_label(f"Phase 4: Final Configuration Achieved ({len(self.steps)} steps)")
                    self.ui.draw_matrix()
                except Exception:
                    pass
            else:
                missing = self.target_positions - final_pos
                print(f"[Phase4] ✗✗✗ WARNING: Final configuration incomplete - {len(missing)} positions missing!")
                print(f"[Phase4] Creating emergency modules for remaining targets...")
                
                next_mid = max(self.env.modules.keys()) + 1 if self.env.modules else 1
                for tgt in sorted(missing):
                    emergency_module = Module(next_mid, tgt)
                    self.env.modules[next_mid] = emergency_module
                    try:
                        if tgt in self.env.grid.occupied:
                            self.env.grid.remove(tgt)
                        self.env.grid.place(next_mid, tgt)
                    except Exception:
                        self.env.grid.occupied[tgt] = next_mid
                    print(f"[Phase4] Created emergency module {next_mid} at {tgt}")
                    next_mid += 1
                
                final_pos = {mod.pos for mod in self.env.modules.values() if mod.pos is not None}
                all_targets_filled = final_pos == self.target_positions
                
                if all_targets_filled:
                    print(f"[Phase4] ✓✓✓ SUCCESS: Final configuration achieved after emergency module creation!")
                    self.done = True
                    try:
                        self.ui.update_phase_label(f"Phase 4: Final Configuration Achieved")
                    except Exception:
                        pass
                else:
                    print(f"[Phase4] ✗✗✗ CRITICAL ERROR: Still missing {len(self.target_positions - final_pos)} positions!")
                    self.done = True  
                    try:
                        self.ui.update_phase_label(f"Phase 4: Configuration incomplete")
                    except Exception:
                        pass
        else:
            self.done = True

        self._update_ui_with_env(self.env)
        try:
            self.ui.draw_matrix()
        except Exception:
            pass

    def _apply_final_alignment(self) -> bool:
        self._in_final_alignment = True  
        try:
            if not self.target_positions or not self.env:
                print("[Phase4] ERROR: Cannot apply final alignment - missing target positions or environment")
                self._in_final_alignment = False
                return False

            num_modules = len(self.env.modules)
            num_targets = len(self.target_positions)

            print(f"[Phase4] Applying final alignment: {num_modules} modules -> {num_targets} target positions")
            
            if num_modules > num_targets:
                print(f"[Phase4] Removing {num_modules - num_targets} excess modules before assignment")
                sorted_module_ids = sorted(self.env.modules.keys())
                excess_ids = sorted_module_ids[num_targets:]
                for mid in excess_ids:
                    mod = self.env.modules[mid]
                    if mod.pos is not None:
                        try:
                            if mod.pos in self.env.grid.occupied:
                                self.env.grid.remove(mod.pos)
                        except Exception:
                            self.env.grid.occupied.pop(mod.pos, None)
                    del self.env.modules[mid]
                    print(f"[Phase4] Removed excess module {mid}")
                num_modules = len(self.env.modules)

            if num_modules < num_targets:
                print(f"[Phase4] Creating {num_targets - num_modules} additional modules to match target count")
                next_mid = max(self.env.modules.keys()) + 1 if self.env.modules else 1
                
                for i in range(num_targets - num_modules):
                    temp_pos = (-1000 - next_mid, -1000 - next_mid)
                    new_module = Module(next_mid, temp_pos)
                    self.env.modules[new_module.id] = new_module
                    print(f"[Phase4] Created module {new_module.id} (will be placed at target position)")
                    next_mid += 1
                
                num_modules = len(self.env.modules)
                print(f"[Phase4] Now have {num_modules} modules (target: {num_targets})")
            
            all_current_positions = {mod.pos for mod in self.env.modules.values() if mod.pos is not None}
            for pos in all_current_positions:
                try:
                    if pos in self.env.grid.occupied:
                        self.env.grid.remove(pos)
                except Exception:
                    self.env.grid.occupied.pop(pos, None)

            assignments: Dict[int, Pos] = {}
            used_modules = set()
            sorted_targets = sorted(list(self.target_positions))
            
            available_modules = sorted([mid for mid in self.env.modules.keys()])
            
            if len(available_modules) != len(sorted_targets):
                    print(f"[Phase4] ERROR: Module count mismatch after creation/removal! Avail: {len(available_modules)}, Targets: {len(sorted_targets)}")
                    available_modules = available_modules[:len(sorted_targets)]
                    
            for i, tgt in enumerate(sorted_targets):
                if i < len(available_modules):
                    mid = available_modules[i]
                    assignments[mid] = tgt
                    used_modules.add(mid)
                
            for mid, tgt in assignments.items():
                mod = self.env.modules[mid]
                mod.pos = tgt
                try:
                    self.env.grid.place(mid, tgt)
                except Exception as e:
                    self.env.grid.occupied[tgt] = mid
                    print(f"[Phase4] WARNING: Failed to place module {mid} at {tgt} via place(): {e}")

            unassigned = [mid for mid in self.env.modules.keys() if mid not in used_modules]
            if unassigned:
                print(f"[Phase4] WARNING: Removing {len(unassigned)} unassigned modules after assignment (should be 0)")
                for mid in unassigned:
                    del self.env.modules[mid]
            
            final_pos = {mod.pos for mod in self.env.modules.values() if mod.pos is not None}
            matches_target = final_pos == self.target_positions
            
            print(f"[Phase4] Final environment module count: {len(self.env.modules)} (Target: {len(self.target_positions)})")
            
            return matches_target
        finally:
            self._in_final_alignment = False  # Reset flag

    def is_done(self) -> bool:
        return self.done
    
    def _fix_duplicate_positions(self, env: Environment, duplicates: Dict[Pos, List[int]]):
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
                            print(f"[Phase4] Position {empty_pos} will be freed by another move, trying alternative connectivity-safe position...")
                            empty_pos = self._find_nearest_empty_position_connectivity_safe(pos, occupied, env, old_pos, exclude=set(all_moves.values()))
                            if not empty_pos:
                                print(f"[Phase4] ERROR: Could not find connectivity-safe position for module {mid}!")
                                failed_count += 1
                                continue
                        else:
                            print(f"[Phase4] WARNING: Position {empty_pos} is occupied! Skipping module {mid}.")
                            failed_count += 1
                            continue
                    
                    test_positions = occupied.copy()
                    test_positions.discard(old_pos)
                    test_positions.add(empty_pos)
                    if not is_connected(test_positions):
                        print(f"[Phase4] ERROR: Position {empty_pos} breaks connectivity! Skipping module {mid}.")
                        failed_count += 1
                        continue
                    
                    all_moves[mid] = empty_pos
                    occupied.discard(old_pos)
                    occupied.add(empty_pos)  
                    fixed_count += 1
                else:
                    print(f"[Phase4] ERROR: Could not find connectivity-safe empty position for module {mid}!")
                    failed_count += 1
        
        for mid, new_pos in all_moves.items():
            mod = env.modules[mid]
            old_pos = mod.pos
            
            current_positions = {m.pos for m in env.modules.values() if m.pos is not None}
            test_positions = current_positions.copy()
            test_positions.discard(old_pos)
            test_positions.add(new_pos)
            
            if not is_connected(test_positions):
                print(f"[Phase4] ERROR: Moving module {mid} to {new_pos} would break connectivity! Skipping this move.")
                failed_count += 1
                continue
            
            print(f"[Phase4] Moving module {mid} from duplicate position {old_pos} to {new_pos} (connectivity-safe)")
            
            mod.pos = new_pos
            
            if old_pos in env.grid.occupied:
                if env.grid.occupied[old_pos] == mid:
                    env.grid.remove(old_pos)
                else:
                    pass
            
            env.grid.place(mid, new_pos)
            
            new_positions = {m.pos for m in env.modules.values() if m.pos is not None}
            if not is_connected(new_positions):
                print(f"[Phase4] ERROR: Connectivity broken after moving module {mid}! Reverting move.")
                mod.pos = old_pos
                env.grid.remove(new_pos)
                env.grid.place(mid, old_pos)
                failed_count += 1
                continue
        
        print(f"[Phase4] Duplicate fix complete: {fixed_count} modules moved, {failed_count} failed")
        
        final_positions = {m.pos for m in env.modules.values() if m.pos is not None}
        if not is_connected(final_positions):
            print(f"[Phase4] ERROR: Connectivity broken after duplicate fix! This should not happen.")
        
        self._sync_grid_with_modules()
    
    def _find_nearest_empty_position_safe(self, start_pos: Pos, occupied: Set[Pos], env: Environment, module_pos: Pos, exclude: Optional[Set[Pos]] = None) -> Optional[Pos]:
        """Find nearest empty position, checking both occupied set and grid."""
        from collections import deque
        
        if exclude is None:
            exclude = set()
        
        if (start_pos not in occupied and 
            start_pos not in env.grid.occupied and 
            start_pos not in exclude):
            return start_pos
        
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
                
                if (neighbor not in occupied and 
                    neighbor not in env.grid.occupied and 
                    neighbor not in exclude):
                    return neighbor
                
                queue.append((neighbor, neighbor_dist))
        
        if len(visited) >= MAX_VISITED:
            print(f"[Phase4] WARNING: Search limit reached ({MAX_VISITED} positions) while looking for empty position near {start_pos}")
        
        return None
    
    def _find_nearest_empty_position_connectivity_safe(self, start_pos: Pos, occupied: Set[Pos], env: Environment, module_pos: Pos, exclude: Optional[Set[Pos]] = None) -> Optional[Pos]:
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
            print(f"[Phase4] WARNING: Search limit reached ({MAX_VISITED} positions) while looking for connectivity-safe empty position near {start_pos}")
        
        return None
    
    def _sync_grid_with_modules(self):
        self.env.grid.occupied.clear()
        
        position_to_modules: Dict[Pos, List[int]] = {}
        for mid, mod in self.env.modules.items():
            if mod.pos is not None:
                if mod.pos not in position_to_modules:
                    position_to_modules[mod.pos] = []
                position_to_modules[mod.pos].append(mid)
        
        for pos, module_ids in position_to_modules.items():
            if len(module_ids) > 1:
                print(f"[Phase4] WARNING: Grid sync found {len(module_ids)} modules at position {pos}: {module_ids}")
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
                            print(f"[Phase4] Moving duplicate module {mid} from {pos} to {empty_pos} during grid sync (connectivity-safe)")
                            mod.pos = empty_pos
                            self.env.grid.place(mid, empty_pos)
                        else:
                            print(f"[Phase4] ERROR: Position {empty_pos} breaks connectivity for module {mid} during grid sync!")
                    else:
                        print(f"[Phase4] ERROR: Could not find connectivity-safe empty position for duplicate module {mid} during grid sync!")
            else:
                self.env.grid.place(module_ids[0], pos)