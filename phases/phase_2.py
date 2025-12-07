from environment import Environment
from structures.module import Module, Move
from structures.scaffolding import compute_scaffolding_from_env  # a Phase 2 logikája
from structures.skeleton import _get_center_of_mass
from typing import Tuple, Set, Dict, List
from copy import deepcopy

def execute_phase(ui=None):
    print("Executing Phase 2: Building Scaffolding")

    if ui is None:
        print("No UI reference provided. Phase 2 cannot update GUI.")
        return

    # --- 1) Read matrix from UI
    matrix = ui.matrix
    rows, cols = len(matrix), len(matrix[0])

    # --- 2) Build environment
    env = Environment()
    mid = 1
    for y in range(rows):
        for x in range(cols):
            if matrix[y][x] == 1:
                grid_pos = (x, rows - 1 - y)  # convert GUI->grid
                env.add_module(Module(mid, grid_pos))
                mid += 1

    # --- 3) Calculate center cell
    min_x = 0
    max_x = cols - 1
    min_y = 0
    max_y = rows - 1
    center_x = (min_x + max_x) // 2
    center_y = (min_y + max_y) // 2
    center_cell = (center_x, center_y)

    # --- 4) Compute scaffolding
    scaff_cells = compute_scaffolding_from_env(env, center_cell)
    print(f"Scaffolding generated with {len(scaff_cells)} cells.")

    # --- 5) Update GUI matrix
    all_positions = scaff_cells
    min_x_pos = min(x for x, _ in all_positions)
    max_x_pos = max(x for x, _ in all_positions)
    min_y_pos = min(y for _, y in all_positions)
    max_y_pos = max(y for _, y in all_positions)

    new_rows = max_y_pos - min_y_pos + 1
    new_cols = max_x_pos - min_x_pos + 1
    new_matrix = [[0 for _ in range(new_cols)] for _ in range(new_rows)]

    for pos in scaff_cells:
        x, y = pos
        gui_x = x - min_x_pos
        gui_y = max_y_pos - y
        new_matrix[gui_y][gui_x] = 1

    # --- 6) Update GUI
    ui.update_matrix(new_matrix)
    ui.update_phase_label("Phase 2: Scaffolding Constructed")
    print("Phase 2 completed successfully.")

class Phase2:
    def __init__(self, ui):
        self.ui = ui
        self.env, mid = self.build_env_from_ui()
        self.setup()
        self.env_queue = []
        self.line_1_done = False
        self.line_2_done = False
        self.line_3_done = False
        self.done = False

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
    
    def setup(self):
        # Calculating extended bounding box, so that its height is multiple of 3
        bounding_box_height = max(len(self.ui.matrix) , len(self.ui.goal_matrix))
        extended_bounding_box_height = bounding_box_height
        if bounding_box_height % 3 != 0:
            extended_bounding_box_height += 3 - (bounding_box_height % 3)
        
        min_x, max_x, min_y, max_y = self.env.find_bounds()
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = min_y + extended_bounding_box_height - 1
        print('Max x:', self.max_x, 'Min y:', self.min_y, 'Max y:', self.max_y)
        positions = []
        for module in self.env.modules.values():
            positions.append(module.pos)

        center_x, center_y = _get_center_of_mass(positions)
        center_x = round(center_x)
        
        center_y = round(center_y)
        if self.env.find_module_at([center_x, center_y]) == None:
            self.center_pos = [center_x, center_y]
        else:
            if self.env.find_module_at([center_x + 1, center_y]) == None:
                self.center_pos = [center_x + 1, center_y]
            if self.env.find_module_at([center_x - 1, center_y]) == None:
                self.center_pos = [center_x - 1, center_y]
            if self.env.find_module_at([center_x, center_y + 1]) == None:
                self.center_pos = [center_x, center_y + 1]
            if self.env.find_module_at([center_x, center_y - 1]) == None:
                self.center_pos = [center_x, center_y - 1]
            if self.env.find_module_at([center_x + 1, center_y + 1]) == None:
                self.center_pos = [center_x + 1, center_y + 1]
            if self.env.find_module_at([center_x - 1, center_y - 1]) == None:
                self.center_pos = [center_x - 1, center_y - 1]
            if self.env.find_module_at([center_x + 1, center_y - 1]) == None:
                self.center_pos = [center_x + 1, center_y - 1]
            if self.env.find_module_at([center_x - 1, center_y + 1]) == None:
                self.center_pos = [center_x - 1, center_y + 1]


        if type(self.env.find_module_at(self.center_pos)) == Module:
            print('Baj van!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

        if self.center_pos[0] == self.max_x - 2:
            self.center_pos[0] = self.max_x - 3
            module_to_move = self.env.find_module_at([self.max_x - 3, self.center_pos[1]])
            movement_dict = {}
            movement_dict[module_to_move.id] = Move.EAST
            self.env.transformation(movement_dict)
            self.env_queue.append(deepcopy(self.env))
        
        elif self.center_pos[0] == self.max_x - 1:
            self.center_pos[0] = self.max_x - 3
            modules_to_move = [self.env.find_module_at([self.max_x - 3, self.center_pos[1]]), self.env.find_module_at([self.max_x - 2, self.center_pos[1]])]
            movement_dict = {}
            for module_to_move in modules_to_move:
                movement_dict[module_to_move.id] = Move.EAST
            self.env.transformation(movement_dict)
            self.env_queue.append(deepcopy(self.env))

        elif self.center_pos[0] == self.max_x:
            self.center_pos[0] = self.max_x - 3
            modules_to_move = [self.env.find_module_at([self.max_x - 3, self.center_pos[1]]), self.env.find_module_at([self.max_x - 2, self.center_pos[1]]), self.env.find_module_at([self.max_x - 1, self.center_pos[1]])]
            movement_dict = {}
            for module_to_move in modules_to_move:
                movement_dict[module_to_move.id] = Move.EAST
            self.env.transformation(movement_dict)
            self.env_queue.append(deepcopy(self.env))
            

            
        print('Center pos:', self.center_pos)

        # Grow arm
        self.arm = []
        for x in range(self.center_pos[0], max_x + 1):
            self.arm.append(self.env.find_module_at([x, self.center_pos[1]]))

        print('Arm:', self.arm)

    def execute_step(self):
        print("-- Phase 2 step")

        if len(self.env_queue) == 0:
            self.gather_modules()
            self.build_sweepline()
            
        print(self.env_queue)
        env_to_display = self.env_queue.pop(0)
        self.ui.update_matrix(env_to_display.matrix_from_environment())

        if self.done:
            print('Phase 2 done.')
            return True

    def build_sweepline(self):
        min_x, max_x, min_y, max_y = self.env.find_bounds()
        

        if not self.line_1_done:
            print('Building line 1')
            max_x = self.max_x
            
        elif not self.line_2_done:
            print('Building line 2')
            max_x = self.max_x - 1

        elif not self.line_3_done:
            print('Building line 3')
            max_x = self.max_x - 2

        # Grow arm
        self.arm = []
        for x in range(self.center_pos[0], max_x + 1):
            self.arm.append(self.env.find_module_at([x, self.center_pos[1]]))

        print('Arm:', self.arm)

        movement_dict = {}
        for i, module in enumerate(self.arm):
            if i < len(self.arm) - 1:
                movement_dict[module.id] = Move.EAST

        if not self.line_1_done or not self.line_2_done or not self.line_3_done:
            # Push up?
            modules_to_move = []
            for y in range(self.center_pos[1], self.max_y + 1):
                module = self.env.find_module_at([max_x, y])
                if type(module) == Module:
                    modules_to_move.append(module)
                else:
                    break
            
            # If no spaces above push down
            if len(modules_to_move) == max_y - self.center_pos[1] + 1:
                modules_to_move = []
                for y in range(self.center_pos[1], self.min_y - 1, -1):
                    module = self.env.find_module_at([max_x, y])
                    if type(module) == Module:
                        modules_to_move.append(module)
                    else:
                        break
                # If no space below either, move on to next line
                if len(modules_to_move) == self.center_pos[1] - self.min_y + 1:
                    if not self.line_1_done:
                        self.line_1_done = True
                        self.build_sweepline()
                    elif not self.line_2_done:
                        self.line_2_done = True
                        self.build_sweepline()
                    elif not self.line_3_done:
                        self.line_3_done = True
                        self.build_sweepline()
                else:
                    for module in modules_to_move:
                        movement_dict[module.id] = Move.SOUTH
                    self.env.transformation(movement_dict)
                    self.env_queue.append(deepcopy(self.env))
                    return
            else:
                for module in modules_to_move:
                    movement_dict[module.id] = Move.NORTH
                self.env.transformation(movement_dict)
                self.env_queue.append(deepcopy(self.env))
                return

        else:
            print('Sweepline done.')
            self.done = True

    def gather_modules(self):
        scanned_modules = self.scan()
        print('Scanned modules:', [(mod, mod.pos, direction) for mod, direction in scanned_modules])

        if len(scanned_modules) == 0:
            print('No modules to gather.')
            return

        movement_dict = {}
        for module, direction in scanned_modules:
            movement_dict[module.id] = direction

        self.env.transformation(movement_dict)
        self.env_queue.append(deepcopy(self.env))

    def scan(self):
        min_x, max_x, min_y, max_y = self.env.find_bounds()
        scanned_modules = []
        # Scan north of center
        for y in range(self.center_pos[1] + 1, max_y + 1):

            module = self.env.find_module_at([self.center_pos[0], y])
            if type(module) == Module:
                scanned_modules.append([module, Move.SOUTH])
            else:
                break

        northwest_scanned_modules = []
        northeast_scanned_modules = []
        southwest_scanned_modules = []
        southeast_scanned_modules = []
        if len(scanned_modules) > 0:
            nortwest_y = scanned_modules[-1][0].pos[1]
            for x in range(self.center_pos[0] - 1, min_x - 1, -1):
                module = self.env.find_module_at([x, nortwest_y])
                if type(module) == Module:
                    northwest_scanned_modules.append([module, Move.EAST])
                else:
                    break
            
            northeast_y = scanned_modules[-1][0].pos[1]
            for x in range(self.center_pos[0] + 1, max_x - 2):
                module = self.env.find_module_at([x, northeast_y])
                if type(module) == Module:
                    northeast_scanned_modules.append([module, Move.WEST])
                else:
                    break
            
        if len(northwest_scanned_modules) > 0:
            for module, direction in northwest_scanned_modules:
                scanned_modules.append([module, direction])
        
        elif len(northeast_scanned_modules) > 0:
            for module, direction in northeast_scanned_modules:
                scanned_modules.append([module, direction])

        if len(scanned_modules) == 0:
            # Scan south of center
            for y in range(self.center_pos[1] - 1, min_y - 1, -1):
                module = self.env.find_module_at([self.center_pos[0], y])
                if type(module) == Module:
                    scanned_modules.append([module, Move.NORTH])
                else:
                    break
            
            southwest_y = scanned_modules[-1][0].pos[1]
            for x in range(self.center_pos[0] - 1, min_x - 1, -1):
                module = self.env.find_module_at([x, southwest_y])
                if type(module) == Module:
                    southwest_scanned_modules.append([module, Move.EAST])
                else:
                    break

            southeast_y = scanned_modules[-1][0].pos[1]
            for x in range(self.center_pos[0] + 1, max_x - 2):
                module = self.env.find_module_at([x, southeast_y])
                if type(module) == Module:
                    southeast_scanned_modules.append([module, Move.WEST])
                else:
                    break
            
            if len(southwest_scanned_modules) > 0:
                for module, direction in southwest_scanned_modules:
                    scanned_modules.append([module, direction])

            elif len(southeast_scanned_modules) > 0:
                for module, direction in southeast_scanned_modules:
                    scanned_modules.append([module, direction])

        if len(scanned_modules) == 0:
            # Scan west of center
            for x in range(self.center_pos[0] - 1, min_x - 1, -1):
                module = self.env.find_module_at([x, self.center_pos[1]])
                if type(module) == Module:
                    scanned_modules.append([module, Move.EAST])
                else:
                    break

        return scanned_modules
