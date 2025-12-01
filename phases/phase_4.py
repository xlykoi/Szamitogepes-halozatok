from copy import deepcopy
from typing import Tuple, Set, Dict, List, Optional

from environment import Environment
from structures.module import Module, Move
from structures.parallel_moves import compute_parallel_moves
from structures.skeleton import is_connected

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
        """Build an Environment from the current UI.matrix (same logic as RobotUI)."""
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
        
        use_target_dimensions = False
        if hasattr(self, 'target_positions') and self.target_positions and hasattr(self, 'target_file'):
            positions_match = positions == self.target_positions
            in_alignment = hasattr(self, '_in_final_alignment') and self._in_final_alignment
            phase_done = hasattr(self, 'done') and self.done
            
            if positions_match or in_alignment or phase_done:
                use_target_dimensions = True
                if positions_match:
                    reason = "positions match target"
                elif in_alignment:
                    reason = "in final alignment"
                elif phase_done:
                    reason = "phase is done"
                else:
                    reason = "unknown"
        
        if use_target_dimensions:
            target_matrix = self._load_matrix_from_file(self.target_file)
            if target_matrix:
                rows = len(target_matrix)
                cols = len(target_matrix[0]) if rows > 0 else 0
                new_matrix = [[0 for _ in range(cols)] for _ in range(rows)]
                for x, y in positions:
                    matrix_y = rows - 1 - y
                    matrix_x = x
                    if 0 <= matrix_y < rows and 0 <= matrix_x < cols:
                        new_matrix[matrix_y][matrix_x] = 1
                return new_matrix
        
        all_x = [p[0] for p in positions]
        all_y = [p[1] for p in positions]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        rows = max_y - min_y + 1
        cols = max_x - min_x + 1
        new_matrix = [[0 for _ in range(cols)] for _ in range(rows)]
        for x, y in positions:
            gx = x - min_x
            gy = max_y - y  
            if 0 <= gy < rows and 0 <= gx < cols:
                new_matrix[gy][gx] = 1
        return new_matrix

    def _update_ui_with_env(self, env: Environment):
        final_positions = {m.pos for m in env.modules.values() if m.pos is not None}
        if not final_positions:
            try:
                self.ui.update_matrix([[]])
                self.ui.matrix = [[]]  
            except Exception:
                pass
            return
        
        new_matrix = self._convert_positions_to_matrix(final_positions)
        
        if hasattr(self, 'target_positions') and self.target_positions and hasattr(self, 'target_file'):
            if (hasattr(self, 'done') and self.done) or (final_positions == self.target_positions):
                target_matrix = self._load_matrix_from_file(self.target_file)
                if target_matrix:
                    expected_rows = len(target_matrix)
                    expected_cols = len(target_matrix[0]) if expected_rows > 0 else 0
                    actual_rows = len(new_matrix)
                    actual_cols = len(new_matrix[0]) if actual_rows > 0 else 0
                    if actual_rows != expected_rows or actual_cols != expected_cols:
                        print(f"[Phase4] WARNING: Matrix dimensions incorrect! Expected {expected_rows}x{expected_cols}, got {actual_rows}x{actual_cols}")
                        print(f"[Phase4] Re-converting with target dimensions...")
                        self._in_final_alignment = True
                        try:
                            new_matrix = self._convert_positions_to_matrix(final_positions)
                        finally:
                            self._in_final_alignment = False
        
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

        # build env from UI
        self.env, next_mid = self.build_env_from_ui()
        initial_module_count = len(self.env.modules)
        print(f"[Phase4] ===== PHASE 4 PREPARATION =====")
        print(f"[Phase4] Initial module count from UI: {initial_module_count}")
        
        if initial_module_count == 0:
            print(f"[Phase4] ERROR: No modules found in UI matrix!")
            self.steps = []
            self.has_prepared = True
            self.done = True
            return

        # load target matrix from file and build a target_env
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

        # counts
        num_modules = len(self.env.modules)
        num_targets = len(self.target_positions)

        print(f"[Phase4] Module count: {num_modules} modules available")
        print(f"[Phase4] Target count: {num_targets} target positions")
        
        if num_modules > num_targets:
            print(f"[Phase4] INFO: More modules ({num_modules}) than targets ({num_targets})")
            print(f"[Phase4] Deterministically selecting {num_targets} modules (lowest ID) to fill targets")
            
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

        # show initial state in UI and goal
        self._update_ui_with_env(self.env)
        try:
            self.ui.draw_matrix()
        except Exception:
            pass

        try:
            self.ui.update_phase_label(f"Phase 4 prepared: {len(self.steps)} steps planned")
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
            ok = self.env.step(deepcopy(step))
            
            if not ok:
                print("[Phase4] Step execution failed; will apply final alignment.")
                self.current_index = len(self.steps)  
            else:
                self.current_index += 1
                self._update_ui_with_env(self.env)
                try:
                    self.ui.draw_matrix()
                    remaining = len(self.steps) - self.current_index
                    self.ui.update_phase_label(f"Phase 4: Step {self.current_index}/{len(self.steps)} ({remaining} remaining)")
                except Exception:
                    pass
                if self.current_index >= len(self.steps):
                    pass
                else:
                    return  

        if self.current_index >= len(self.steps) and self.target_positions:
            print(f"[Phase4] ===== APPLYING FINAL ALIGNMENT (step-by-step) =====")
            
            alignment_success = self._apply_final_alignment()
            
            final_pos = {mod.pos for mod in self.env.modules.values() if mod.pos is not None}
            all_targets_filled = final_pos == self.target_positions
            
            print(f"[Phase4] Final alignment result: success={alignment_success}, targets_filled={all_targets_filled}")
            print(f"[Phase4] Final positions: {len(final_pos)}, Target positions: {len(self.target_positions)}")
            
            if all_targets_filled:
                print(f"[Phase4] SUCCESS: Final configuration achieved!")
                
                print(f"\n[Phase4] ===== ACTUAL FINAL CONFIGURATION PRODUCED =====")
                actual_matrix = self._convert_positions_to_matrix(final_pos)
                print(f"[Phase4] Matrix dimensions: {len(actual_matrix)} rows x {len(actual_matrix[0]) if actual_matrix and actual_matrix[0] else 0} cols")
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
                            # Force re-update
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
                print(f"[Phase4] All {len(final_pos)} target positions are filled and displayed")
                
                print(f"\n[Phase4] ===== ACTUAL FINAL CONFIGURATION PRODUCED (execute_phase) =====")
                self.done = True
                actual_matrix = self._convert_positions_to_matrix(final_pos)
                print(f"[Phase4] Matrix dimensions: {len(actual_matrix)} rows x {len(actual_matrix[0]) if actual_matrix and actual_matrix[0] else 0} cols")
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
                    temp_pos = (-1000 - next_mid, -1000 - next_mid)  # Far away temporary position
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