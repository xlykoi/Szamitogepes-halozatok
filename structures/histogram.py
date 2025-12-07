from typing import Any, Callable, List, Optional, Sequence, Tuple
from .module import Module, Move
from .metamodule import MetaModule
from copy import copy, deepcopy
from .snake import Snake, SnakeHead, SnakeSegment
import math
from environment import Environment

class Histogram:
    rows: List[List[Optional[Module]]]
    
    def __init__(self, env):
        self.goal_positions = []
        self.snakes = []
        self.steps = 0
        self.end_config = []
        self.update_env(env)

    def update_env(self, env):
        self.env = env
        self.setup_from_env(env)
        if len(self.snakes) > 0:
            for snake in self.snakes:
                snake.update_env(env)   


    def setup_from_env(self, env):
        self.rows = []
        min_x, max_x, min_y, max_y = env.find_bounds()
        for i, y in enumerate(range(max_y, min_y-1, -1)):
            found_rightmost_module = False
            self.rows.append([])
            for x in range(max_x, min_x-1, -1):
                if not found_rightmost_module:
                    module = env.find_module_at([x, y])
                    if module != None:
                        self.rows[i].insert(0, module)
                        found_rightmost_module = True
                else:
                    module = env.find_module_at([x, y])
                    self.rows[i].insert(0, module)

    def compact_to_left(self, env_queue) -> bool:
        self.setup_from_env(self.env)
        for row in self.rows:
            pass
        did_nothing = True
        movement_dict = {}
        for row in self.rows:
            found_hole = False
            for module in row:
                if not found_hole:
                    if module == None:
                        found_hole = True
                elif found_hole:
                    if module != None:
                        did_nothing = False
                        movement_dict[module.id] = Move.WEST

        if not did_nothing:
            new_env = self.env.transformation(movement_dict)
            env_queue.append(deepcopy(new_env))
            self.env = new_env
        
        done = did_nothing
        return done

    def shift_down(self):
        if not self.goal_positions:
             self.calculate_ideal_shape()
        
        if len(self.snakes) == 0:
            result = self.make_snakes()
            if result == 'done':
                print('Histogram complete')
                return 'done'

        movement_dict = {}
        for snake in list(self.snakes):
            snake_move = snake.movement_dict()
            if snake_move == 'done':
                self.snakes.remove(snake)
                continue
            if snake_move is None:
                self.snakes.remove(snake)
                continue
            if isinstance(snake_move, dict):
                for module_id, move in snake_move.items():
                    if isinstance(move, Move) and hasattr(move, 'delta'):
                        movement_dict[module_id] = move
                    else:
                        print(f'Warning: Invalid move for module {module_id}: {move}')

        if not movement_dict and len(self.snakes) == 0:
             print('Histogram complete')
             return 'done'

        if not movement_dict:
            print('Warning: No valid movements from snakes')
            return self.env

        print(f'Applying {len(movement_dict)} snake movements')
        
        for module_id in movement_dict.keys():
            if module_id in self.env.modules:
                old_pos = self.env.modules[module_id].pos
                self.env.grid.remove(old_pos)
        
        self.env = self.env.transformation(movement_dict)
        
        for module_id in movement_dict.keys():
            if module_id in self.env.modules:
                new_pos = self.env.modules[module_id].pos
                self.env.grid.place(module_id, new_pos)
        
        for snake in self.snakes:
            snake.update_env(self.env)
        
        return self.env
        
    def make_snakes(self):
        print('Making snakes')
        goal_ids = []
        snake_ids = []

        self.setup_from_env(self.env)

        for module in self.env.modules.values():
            found_module = False
            for position in self.goal_positions:
                if module.pos[0] == position[0] and module.pos[1] == position[1]:
                    goal_ids.append(module.id)
                    found_module = True
                    break
            if not found_module:
                snake_ids.append(module.id)

        print('Snake IDs:', snake_ids)

        if len(snake_ids) == 0:
            print('all modules in goal positions')
            return 'done'

        triple_rows = []
        triple_row = []
        row_counter = 0
        for row in self.rows:
            triple_row.append(row)
            row_counter += 1
            if row_counter == 3:
                triple_rows.append(triple_row)
                triple_row = []
                row_counter = 0
        
        self.snakes = []

        for triple in triple_rows:
            snake_pos = 0
            
            current_max_x = -1
            for row in triple:
                for module in row:
                     if module is not None and module.pos[0] > current_max_x:
                         current_max_x = module.pos[0]
            
            snake_pos = current_max_x
            
            snake_modules = []
            for row in triple:
                for module in row:
                    if module is not None and module.pos[0] == snake_pos and module.id in snake_ids:
                        snake_modules.append(module)
            
            if len(snake_modules) > 0:
                snake_head_module = snake_modules[0]
                
                snake_segments_modules = snake_modules[1:]
                
                snake_head = SnakeHead(snake_head_module, Move.SOUTH, self.env)
                
                segment_ahead = snake_head
                snake_segments = []
                
                for module in snake_segments_modules:
                    segment = SnakeSegment(module, segment_ahead)
                    segment_ahead = segment
                    snake_segments.append(segment)
                
                self.snakes.append(Snake(snake_head, snake_segments, self.env))

        for snake in self.snakes:
            print('New Snake Created. Head:', snake.head.module.id)

    def calculate_ideal_shape(self):
        module_count = len(self.env.modules)
        min_x, max_x, min_y, max_y = self.env.find_bounds()
        
        total_height = len(self.rows)
        if total_height % 3 != 0:
             pass 
             
        metamodule_height = int(total_height / 3)
        
        remaining_modules = module_count % 9
        number_of_potential_metamodules = int((module_count - remaining_modules) / 9)
        
        metamodule_column_number = math.ceil(number_of_potential_metamodules / metamodule_height)
        
        metamodule_columns = []
        for n in range(metamodule_column_number + 1):
            metamodule_columns.append([])

        metamodules_to_place = number_of_potential_metamodules
        
        current_col = 0
        while metamodules_to_place > 0:
            if len(metamodule_columns[current_col]) < metamodule_height:
                metamodule_columns[current_col].append(1)
                metamodules_to_place -= 1
            else:
                current_col += 1
                
        if remaining_modules > 0:
             placed = False
             for col in metamodule_columns:
                 if len(col) < metamodule_height:
                     col.append(0.5)
                     placed = True
                     break
             if not placed:
                 metamodule_columns[-1].append(0.5)

        self.goal_positions = []
        modules_not_added_to_histogram = copy(remaining_modules)
        
        for column_idx, column in enumerate(metamodule_columns):
            for metamodule_idx, metamodule_type in enumerate(column):
                base_x = min_x + (column_idx * 3)
                base_y = min_y + (metamodule_idx * 3)
                
                if metamodule_type == 1:
                    for x in range(3):
                        for y in range(3):
                            self.goal_positions.append([base_x + x, base_y + y])
                            
                elif metamodule_type == 0.5:
                    for x in range(3):
                        for y in range(3):
                            if modules_not_added_to_histogram > 0:
                                self.goal_positions.append([base_x + x, base_y + y])
                                modules_not_added_to_histogram -= 1
        