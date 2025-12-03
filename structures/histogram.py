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
            print(row)
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
            env_queue.append(deepcopy(self.env.transformation(movement_dict)))
        done = did_nothing
        return done

    def shift_down(self):
        self.calculate_ideal_shape()
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
        print(self.snakes)

        if len(self.snakes) == 0:
            if self.make_snakes() == 'done':
                print('Histogram complete')
                return 'done'

        movement_dict = {}
        for snake in self.snakes:
            snake_move = snake.movement_dict()
            if snake_move == 'done':
                self.snakes.remove(snake)
                continue
            movement_dict.update(snake_move)

        print(movement_dict)
        self.env.transformation(movement_dict)
        
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        '''
        snake_ids = []
        for module in self.env.modules.values():
            found_module = False
            for position in self.goal_positions:
                if module.pos[0] == position[0] and module.pos[1] == position[1]:
                    found_module = True
                    break
            if not found_module:
                print('Module', module.id, 'at', module.pos, 'not in goal positions')
                snake_ids.append(module.id)

        module_count = len(self.env.modules)
        metamodule_height = int(len(self.rows) / 3)
        remaining_modules = module_count % 9
        number_of_potential_metamodules = int((module_count - remaining_modules) / 9)
        remaining_metamodules = int(number_of_potential_metamodules % metamodule_height)
        metamodule_column_number = int((number_of_potential_metamodules - remaining_metamodules) / metamodule_height)

        number_of_potential_snakes = int(len(snake_ids)/3) + 1
        distance_to_go = (metamodule_height * 3) + (metamodule_column_number * 3)

        steps = number_of_potential_snakes * distance_to_go
        if self.steps < steps:
            self.steps += 1
            max_x = 0
            max_y = 0
            for position in self.goal_positions:
                if position[0] > max_x:
                    max_x = position[0]
                if position[1] > max_y:
                    max_y = position[1]
            matrix = []
            for y in range(max_y+1):
                row = []
                for x in range(max_x+1):
                    if [x, y] in self.goal_positions:
                        row.append(1)
                    else:
                        row.append(0)
                matrix.append(row)

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

            return env

        return 'done'
        '''
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

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
                    print('Module', module.id, 'at', module.pos, 'in goal positions')
                    goal_ids.append(module.id)
                    found_module = True
                    break
            if not found_module:
                print('Module', module.id, 'at', module.pos, 'not in goal positions')
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
        
        for triple in triple_rows:
            snake_pos = 0
            for row in triple:
                if len(row)-1 > snake_pos:
                    snake_pos = len(row)-1
            print('snake pos in triple:', snake_pos)
            snake_modules = []
            for row in triple:
                if len(row)-1 == snake_pos and row[snake_pos].id in snake_ids:
                    snake_modules.append(row[snake_pos])
            print('snake modules:', snake_modules)
            if len(snake_modules) > 0:
                snake_head = SnakeHead(snake_modules[-1], Move.SOUTH, self.env)
                segment_ahead = snake_head
                snake_segments = []
                for module in reversed(snake_modules):
                    if module == snake_modules[-1]:
                        continue
                    segment = SnakeSegment(module, segment_ahead)
                    segment_ahead = segment
                    snake_segments.append(segment)
                self.snakes.append(Snake(snake_head, snake_segments, self.env))

            for snake in self.snakes:
                print('snake head:', snake.head.module, 'segment ahead:', snake.head.segment_ahead, 'last move:', snake.head.last_move)
                for segment in snake_segments:
                    print('segment:', segment.module, 'segment ahead:', segment.segment_ahead.module, 'last move:', segment.last_move)

    def calculate_ideal_shape(self):
        module_count = len(self.env.modules)
        metamodule_height = int(len(self.rows) / 3)
        remaining_modules = module_count % 9
        number_of_potential_metamodules = int((module_count - remaining_modules) / 9)
        remaining_metamodules = int(number_of_potential_metamodules % metamodule_height)
        metamodule_column_number = int((number_of_potential_metamodules - remaining_metamodules) / metamodule_height)
        

        print('Module count: ', module_count)
        print('Metamodule height: ', metamodule_height)
        print('Remaining modules: ', remaining_modules)
        print('Number of potential metamodules: ', number_of_potential_metamodules)
        print('Remaining metamodules: ', remaining_metamodules)
        print('Metamodule column number: ', metamodule_column_number)

        metamodule_columns = []
        for n in range(metamodule_column_number):
            metamodule_columns.append([])
        metamodule_columns.append([])

        metamodules_not_added_to_column = copy(number_of_potential_metamodules)
        for column in metamodule_columns:
            for _n in range(metamodule_height):
                if metamodules_not_added_to_column == 0:
                    column.append(0.5)
                    break
                column.append(1)
                metamodules_not_added_to_column -= 1
        
        self.goal_positions = []
        min_x, max_x, min_y, max_y = self.env.find_bounds()
        modules_not_added_to_histogram = copy(remaining_modules)
        for column_idx, column in enumerate(metamodule_columns):
            for metamodule_idx, metamodule in enumerate(column):
                if metamodule == 1:
                    for x in range(3):
                        for y in range(3):
                            self.goal_positions.append([min_x + (column_idx*3) + x, min_y + (metamodule_idx*3) + y])
                            

                
                if metamodule == 0.5:
                    for x in range(3):
                        for y in range(3):
                            if modules_not_added_to_histogram > 0:
                                self.goal_positions.append([min_x + (column_idx*3) + x, min_y + (metamodule_idx*3) + y])
                                modules_not_added_to_histogram -= 1
        
        print(self.goal_positions)
