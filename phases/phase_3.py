from environment import Environment
from structures.module import Module
from structures.sweepline import SweepLine
from structures.metamodule import MetaModule
from structures.histogram import Histogram
from sweep import compute_histogram_from_environment
from typing import Tuple, List
from copy import deepcopy

class Phase_3:
    def __init__(self, ui):
        self.ui = ui
        self.step_count = 0
        self.env_queue: List[Environment] = []
        self.env, mid = self.build_env_from_ui()
        self.done = False
        self.histogram_compact = False
        self.histogram = None

        self.sweep_initialized = False
        self.current_gather_index = -2
        self.need_clean_after_gather = False
        self.all_gathers_done = False
        self.advance_done = False

        xs=[]
        ys=[]
        for module in self.env.modules.values():
            xs.append(module.pos[0])
            ys.append(module.pos[1])
        
        self.sweep_line = None

    def first_clean_step(self):
        min_x, max_x, min_y, max_y = self.env.find_bounds()
        metamodules: List[MetaModule] = []
        for y in range(min_y, max_y):
            if (y - min_y) % 3 == 1:
                if self.sweep_line == None:
                    metamodules.append(MetaModule(max_x - 1, y, self.env))
                else:
                    metamodules.append(MetaModule(self.sweep_line.x - 1, y, self.env))
        if self.sweep_line == None:
            self.sweep_line = SweepLine(max_x - 1, metamodules)
        else:
            self.sweep_line = SweepLine(self.sweep_line.x - 1, metamodules)
        done = self.sweep_line.clean(self.env, self.env_queue)
        print('---Sweep Line Cleaned---')
        print('done? ', done)

    def clean_step(self):
        metamodules = []
        if len(self.env_queue) != 0:
            self.env = self.env_queue[-1]
            for metamodule in self.sweep_line.metamodules:
                x = metamodule.x
                metamodules.append(MetaModule(metamodule.x, metamodule.y, self.env))

            self.sweep_line = SweepLine(x, metamodules)
            self.sweep_line.full_diagnostic(self.env)

        done = self.sweep_line.clean(self.env, self.env_queue)
        print('---Sweep Line Cleaned---')
        print('done? ', done)

    def gather_step(self, i):
        clean_metamodules = []
        if len(self.env_queue) != 0:
            self.env = self.env_queue[-1]
            for metamodule in self.sweep_line.metamodules:
                clean_x = metamodule.x
                clean_metamodules.append(MetaModule(metamodule.x, metamodule.y, self.env))

            self.sweep_line = SweepLine(clean_x, clean_metamodules)
            self.sweep_line.full_diagnostic(self.env)

        self.sweep_line.gather_east_strip(self.env, self.env_queue, i)

    def advance_step(self):
        clean_metamodules = []
        if len(self.env_queue) != 0:
            self.env = self.env_queue[-1]
            for metamodule in self.sweep_line.metamodules:
                clean_x = metamodule.x
                clean_metamodules.append(MetaModule(metamodule.x, metamodule.y, self.env))

            self.sweep_line = SweepLine(clean_x, clean_metamodules)
            self.sweep_line.full_diagnostic(self.env)

        self.sweep_line.advance(self.env, self.env_queue)
        print('---Sweep Line Advanced---')

    def execute_step(self):
        if self.done:
            print('--Sweep line finished sweeping')
            return True
        
        print("Executing Step in Phase 3")
        
        if len(self.env_queue) > 0:
            env_to_display = self.env_queue.pop(0)
            self.env = env_to_display
            self.ui.update_matrix(env_to_display.matrix_from_environment())
            return False
        
        if not self.sweep_initialized:
            self.first_clean_step()
            self.sweep_initialized = True
            self.current_gather_index = -2
            self.need_clean_after_gather = False
            self.all_gathers_done = False
            self.advance_done = False
            
            if len(self.env_queue) == 0:
                print('--Sweep line finished sweeping')
                self.done = True
                return True
            env_to_display = self.env_queue.pop(0)
            self.env = env_to_display
            self.ui.update_matrix(env_to_display.matrix_from_environment())
            return False
        
        if not self.all_gathers_done:
            if not self.need_clean_after_gather:
                if self.current_gather_index < 1:
                    self.current_gather_index += 1
                    self.gather_step(self.current_gather_index)
                    self.need_clean_after_gather = True
                    if len(self.env_queue) > 0:
                        env_to_display = self.env_queue.pop(0)
                        self.env = env_to_display
                        self.ui.update_matrix(env_to_display.matrix_from_environment())
                        return False
                else:
                    self.all_gathers_done = True
            else:
                self.clean_step()
                self.need_clean_after_gather = False
                if len(self.env_queue) > 0:
                    env_to_display = self.env_queue.pop(0)
                    self.env = env_to_display
                    self.ui.update_matrix(env_to_display.matrix_from_environment())
                    return False
        
        if self.all_gathers_done and not self.advance_done:
            self.advance_step()
            if len(self.env_queue) > 0:
                env_to_display = self.env_queue.pop(0)
                self.env = env_to_display
                self.ui.update_matrix(env_to_display.matrix_from_environment())
                return False
            self.advance_done = True
        
        if self.advance_done:
            self.current_gather_index = -2
            self.need_clean_after_gather = False
            self.all_gathers_done = False
            self.advance_done = False
        
        if len(self.env_queue) == 0:
            print('--Sweep line finished sweeping')
            self.done = True
            return True
        
        if len(self.env_queue) > 0:
            env_to_display = self.env_queue.pop(0)
            self.env = env_to_display
            self.ui.update_matrix(env_to_display.matrix_from_environment())
            return False
        
        return False

    def execute_histogram_step(self):
        if self.histogram is None:
            self.histogram = Histogram(self.env)

        if len(self.env_queue) > 0:
            env_to_display = self.env_queue.pop(0)
            self.env = env_to_display
            self.histogram.update_env(env_to_display)
            self.ui.update_matrix(env_to_display.matrix_from_environment())
            return False

        
        if not self.histogram_compact:
            is_finished = self.histogram.compact_to_left(self.env_queue)
            
            if not is_finished:
                print(f"Compacting step generated. Queue size: {len(self.env_queue)}")
                return False
            else:
                print('Compaction complete. Switching to Vertical Shift (Snakes).')
                self.histogram_compact = True
                
                self.histogram.calculate_ideal_shape()
                return False 

        else:
            result = self.histogram.shift_down()
            
            if result == 'done':
                print('--Histogram construction complete')
                return True
            
            if isinstance(result, Environment):
                self.env = result
                self.ui.update_matrix(result.matrix_from_environment())
            
            return False
        
    def execute_phase(self):
        print("Executing Phase 3")
        
        env, mid = self.build_env_from_ui()

        histogram = compute_histogram_from_environment(env)
        print(f"Histogram generated with {len(histogram)} cells.")

        all_positions = histogram
        min_x_pos = min(x for x, _ in all_positions)
        max_x_pos = max(x for x, _ in all_positions)
        min_y_pos = min(y for _, y in all_positions)
        max_y_pos = max(y for _, y in all_positions)

        new_rows = max_y_pos - min_y_pos + 1
        new_cols = max_x_pos - min_x_pos + 1
        new_matrix = [[0 for _ in range(new_cols)] for _ in range(new_rows)]

        for pos in histogram:
            x, y = pos
            gui_x = x - min_x_pos
            gui_y = max_y_pos - y
            new_matrix[gui_y][gui_x] = 1

        self.ui.update_matrix(new_matrix)
        self.ui.update_phase_label("Phase 3: Histogram constructed")
        print("Phase 3 completed successfully.")

    def build_env_from_ui(self):
        if self.ui is None:
            print("No UI reference provided. Phase 3 cannot update GUI.")
            return

        matrix = self.ui.matrix
        rows, cols = len(matrix), len(matrix[0])


        env = Environment()
        mid = 1
        for y in range(rows):
            for x in range(cols):
                if matrix[y][x] == 1:
                    grid_pos = (x, rows - 1 - y)  # convert GUI->grid
                    env.add_module(Module(mid, grid_pos))
                    mid += 1

        return env, mid