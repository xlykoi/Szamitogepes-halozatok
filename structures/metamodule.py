from typing import Any, Callable, List, Optional, Sequence, Tuple
from .module import Module, Move
from copy import deepcopy


class MetaModule:
    x: int = 0
    y: int = 0
    modules: List[List[Optional[Module]]]

    def __init__(self, x, y, env):
        print('Metamodule created at: ', x, y)
        self.x = x
        self.y = y
        self.modules = [
            [env.find_module_at([x-1, y+1]), env.find_module_at([x, y+1]), env.find_module_at([x+1, y+1])],
            [env.find_module_at([x-1, y]),   env.find_module_at([x, y]),   env.find_module_at([x+1, y])],
            [env.find_module_at([x-1, y-1]), env.find_module_at([x, y-1]), env.find_module_at([x+1, y-1])]
            ]

    """Check if this structure is a MetaModule."""
    def is_valid(self) -> bool:
        """Check if metamodule is either solid or clean."""
        return self.is_solid() or self.is_clean()
    
    
    """Check if this MetaModule is a separator."""
    def is_separator(self, env) -> bool:
        matrix = env.matrix_from_environment()
        empty_space_in_east_strip = False
        empty_space_in_east_strip_found = False
        num_of_collumns_in_east_strip = len(matrix[0]) - (self.x + 1)

        for i in range(num_of_collumns_in_east_strip):
            for j in range(3):
                if self.x == len(matrix):
                    return True  # Ha a metamodul a jobb szelen van, akkor separator
                elif matrix[self.y - 1 + j][self.x + 1 + i] == 0:
                    if not empty_space_in_east_strip:
                        empty_space_in_east_strip_found = True
                    else:
                        return False
                empty_space_in_east_strip = empty_space_in_east_strip_found
            
        return True

    """Check if this MetaModule is solid."""
    def is_solid(self) -> bool:
        """Check if all modules are present in the 3x3 area."""
        for i in range(3):
            for j in range(3):
                if self.modules[i][j] is None:
                    return False
        return True
    
    """Check if this MetaModule is clean."""
    def is_clean(self) -> bool:
        """Check if all modules are present except the center one in the 3x3 area."""
        if self.modules[1][1] is not None:
            return False
        for i in range(3):
            for j in range(3):
                if i == 1 and j == 1:
                    continue
                if self.modules[i][j] is None:
                    return False
        return True
    
    def full_diagnostic(self, matrix) -> None:
        print(f"MetaModule at ({self.x}, {self.y}):")
        print(f"  Valid: {self.is_valid()}")
        print(f"  Separator: {self.is_separator(matrix)}")
        print(f"  Solid: {self.is_solid()}")
        print(f"  Clean: {self.is_clean()}")

    def west_strip_full(self, env):
        min_x, max_x, min_y, max_y = env.find_bounds()
        for x in range(self.x - 2, min_x - 1, -1):
            module = env.find_module_at((x, self.y + 1))
            if not module:
                return False

        for x in range(self.x - 2, min_x - 1, -1):
            module = env.find_module_at((x, self.y))
            if not module:
                return False
            
        for x in range(self.x - 2, min_x - 1, -1):
            module = env.find_module_at((x, self.y - 1))
            if not module:
                return False
            
        return True

    def gather_east_strip(self, env, movement_dict_queue, i) -> None:
        if not self.is_clean():
            return
        trailing_module = env.find_module_at([self.x + 2, self.y + i])
        if trailing_module == None:
            print('Sweepline is misaligned')
            return
        
        else:
            movement_dict = {}
            direction_dictionary = {
                -1: Move.NORTHWEST,
                0: Move.WEST,
                1: Move.SOUTHWEST
            }
            movement_dict[self.modules[1][2].id] = Move.WEST  # Move right module left
            movement_dict[trailing_module.id] = direction_dictionary[i]
            movement_dict_queue[0].update(deepcopy(movement_dict))


    def clean(self, env, movement_dict_queue) -> bool:
        min_x, max_x, min_y, max_y = env.find_bounds()
        if self.x == min_x + 1:
            print('reached the wall')
            return True
        
        if self.west_strip_full(env):
            print('west strip full')
            return False
        # Clean the center module if it exists

        # If there is no center module
        if self.modules[1][1] == None:
            return
        else:
            movement_dict = {}
            # Gather modules in the west strip of the metamodule
            west_strip_rows = [[],[],[]]
            for x in range(self.x - 2, min_x - 1, -1):
                module = env.find_module_at((x, self.y + 1))
                if module:
                    west_strip_rows[0].append(module)
                else:
                    break

            for x in range(self.x - 2, min_x - 1, -1):
                module = env.find_module_at((x, self.y))
                if module:
                    west_strip_rows[1].append(module)  
                else:
                    break 
                
            for x in range(self.x - 2, min_x - 1, -1):
                module = env.find_module_at((x, self.y - 1))
                if module:
                    west_strip_rows[2].append(module)
                else:
                    break

            # Find shortest west strip
            shortest_row = 0
            for i, row in enumerate(west_strip_rows):
                if len(row) < len(west_strip_rows[shortest_row]):
                    shortest_row = i

            # Clean into the shortest west strip
            movement_dict = {}
            for module in west_strip_rows[shortest_row]:
                movement_dict[module.id] = Move.WEST
            if shortest_row == 0:
                movement_dict[self.modules[0][0].id] = Move.WEST
                movement_dict[self.modules[0][1].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                movement_dict = {}
                movement_dict[self.modules[1][1].id] = Move.NORTH
                movement_dict_queue[1].update(deepcopy(movement_dict))

            if shortest_row == 1:
                movement_dict[self.modules[1][0].id] = Move.WEST
                movement_dict[self.modules[1][1].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

            if shortest_row == 2:
                movement_dict[self.modules[2][0].id] = Move.WEST
                movement_dict[self.modules[2][1].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                movement_dict = {}
                movement_dict[self.modules[1][1].id] = Move.SOUTH
                movement_dict_queue[1].update(deepcopy(movement_dict))
        print(movement_dict_queue)
        return False


    def advance(self, env, movement_dict_queue, leading) -> None:
        min_x, max_x, min_y, max_y = env.find_bounds()
        if self.x == min_x + 1:
            print('reached the wall')
            return
        
        if self.west_strip_full(env):
            if self.is_clean():
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))
            print('west strip full')
            return
        # Advance the metamodule one step to the left
        # Check for obscuring modules W1, W2, W3
        W1 = env.find_module_at((self.x - 2, self.y + 1))
        W2 = env.find_module_at((self.x - 2, self.y))
        W3 = env.find_module_at((self.x - 2, self.y - 1))

        if leading:
            # Advance based on which of W1, W2, and W3 are present
            if W1 == W2 == W3 == None:
                # a) step 1
                movement_dict = {}
                movement_dict[self.modules[1][0].id] = Move.SOUTHWEST
                movement_dict[self.modules[0][1].id] = Move.SOUTHWEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # a) step 2
                movement_dict = {}
                movement_dict[self.modules[0][1].id] = Move.NORTHWEST
                movement_dict[self.modules[2][1].id] = Move.NORTHWEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

                # a) step 3
                movement_dict = {}
                movement_dict[self.modules[2][1].id] = Move.WEST
                movement_dict_queue[2].update(deepcopy(movement_dict))

                # a) step 4
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.NORTHWEST
                movement_dict[self.modules[2][2].id] = Move.WEST
                movement_dict_queue[3].update(deepcopy(movement_dict))

                # a) step 5
                movement_dict = {}
                movement_dict[self.modules[0][2].id] = Move.SOUTHWEST
                movement_dict_queue[4].update(deepcopy(movement_dict))

            if W2 == W3 == None and W1 != None:
                # b) step 1
                movement_dict = {}
                movement_dict[self.modules[1][0].id] = Move.WEST
                movement_dict[self.modules[0][1].id] = Move.SOUTHWEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # b) step 2
                movement_dict = {}
                movement_dict[self.modules[2][0].id] = Move.WEST
                movement_dict[self.modules[2][1].id] = Move.WEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

                # b) step 3
                movement_dict = {}
                movement_dict[self.modules[0][2].id] = Move.WEST
                movement_dict[self.modules[1][2].id] = Move.SOUTHWEST
                movement_dict_queue[2].update(deepcopy(movement_dict))

                # b) step 4
                movement_dict = {}
                movement_dict[self.modules[2][2].id] = Move.NORTHWEST
                movement_dict_queue[3].update(deepcopy(movement_dict))

            if W1 == W3 == None and W2 != None:
                # b) step 1
                movement_dict = {}
                movement_dict[self.modules[0][0].id] = Move.WEST
                movement_dict[self.modules[0][1].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # b) step 2
                movement_dict = {}
                movement_dict[self.modules[2][0].id] = Move.WEST
                movement_dict[self.modules[2][1].id] = Move.WEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

                # b) step 3
                movement_dict = {}
                movement_dict[self.modules[0][2].id] = Move.WEST
                movement_dict[self.modules[1][2].id] = Move.SOUTHWEST
                movement_dict_queue[2].update(deepcopy(movement_dict))

                # b) step 4
                movement_dict = {}
                movement_dict[self.modules[2][2].id] = Move.NORTHWEST
                movement_dict_queue[3].update(deepcopy(movement_dict))

            if W1 == W2 == None and W3 != None:
                # b) step 1
                movement_dict = {}
                movement_dict[self.modules[1][0].id] = Move.WEST
                movement_dict[self.modules[2][1].id] = Move.NORTHWEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # b) step 2
                movement_dict = {}
                movement_dict[self.modules[2][0].id] = Move.WEST
                movement_dict[self.modules[2][1].id] = Move.WEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

                # b) step 3
                movement_dict = {}
                movement_dict[self.modules[0][2].id] = Move.WEST
                movement_dict[self.modules[1][2].id] = Move.SOUTHWEST
                movement_dict_queue[2].update(deepcopy(movement_dict))

                # b) step 4
                movement_dict = {}
                movement_dict[self.modules[2][2].id] = Move.NORTHWEST
                movement_dict_queue[3].update(deepcopy(movement_dict))

            if W1 == None and W2 != None and W3 != None:
                # c) step 1
                movement_dict = {}
                movement_dict[self.modules[0][0].id] = Move.WEST
                movement_dict[self.modules[0][1].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # c) step 2
                movement_dict = {}
                movement_dict[self.modules[0][2].id] = Move.WEST
                movement_dict[self.modules[1][2].id] = Move.WEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

            if W1 != None and W2 == None and W3 != None:
                # c) step 1
                movement_dict = {}
                movement_dict[self.modules[1][0].id] = Move.WEST
                movement_dict[self.modules[2][1].id] = Move.NORTHWEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # c) step 2
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.WEST
                movement_dict[self.modules[2][2].id] = Move.WEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

            if W1 != None and W2 != None and W3 == None:
                # c) step 1
                movement_dict = {}
                movement_dict[self.modules[2][0].id] = Move.WEST
                movement_dict[self.modules[2][1].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # c) step 2
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.WEST
                movement_dict[self.modules[2][2].id] = Move.WEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

            if W1 != None and W2 != None and W3 != None:
                # d) step 1
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

        if not leading:
            if W1 == W2 == W3 == None:
                # a*) step 1
                movement_dict = {}
                movement_dict[self.modules[1][0].id] = Move.SOUTHWEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # a*) step 2
                movement_dict = {}
                movement_dict[self.modules[0][0].id] = Move.WEST
                movement_dict[self.modules[2][0].id] = Move.NORTHWEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

                # a*) step 3
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.WEST
                movement_dict_queue[2].update(deepcopy(movement_dict))

                # a*) step 4
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.NORTHWEST
                movement_dict[self.modules[2][2].id] = Move.NORTHWEST
                movement_dict_queue[3].update(deepcopy(movement_dict))

                # a*) step 5
                movement_dict = {}
                movement_dict[self.modules[0][2].id] = Move.SOUTHWEST
                movement_dict[self.modules[2][2].id] = Move.SOUTHWEST
                movement_dict_queue[4].update(deepcopy(movement_dict))

            if W1 != None and W2 == W3 == None:
                # e) step 1
                movement_dict = {}
                movement_dict[self.modules[1][0].id] = Move.WEST
                movement_dict[self.modules[2][0].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # e) step 2
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.WEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

                # e) step 3
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.SOUTHWEST
                movement_dict[self.modules[2][2].id] = Move.NORTHWEST
                movement_dict_queue[2].update(deepcopy(movement_dict))

                # e) step 4
                movement_dict = {}
                movement_dict[self.modules[2][2].id] = Move.WEST
                movement_dict[self.modules[0][2].id] = Move.SOUTHWEST
                movement_dict_queue[3].update(deepcopy(movement_dict))

            if W1 == None and W2 != W3 == None:
                # e) step 1
                movement_dict = {}
                movement_dict[self.modules[0][0].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # e) step 2
                movement_dict = {}
                movement_dict[self.modules[1][0].id] = Move.NORTH
                movement_dict[self.modules[2][0].id] = Move.WEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

                # e) step 3
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.WEST
                movement_dict_queue[2].update(deepcopy(movement_dict))

                # e) step 4
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.SOUTHWEST
                movement_dict[self.modules[2][2].id] = Move.NORTHWEST
                movement_dict_queue[3].update(deepcopy(movement_dict))

                # e) step 5
                movement_dict = {}
                movement_dict[self.modules[2][2].id] = Move.WEST
                movement_dict[self.modules[0][2].id] = Move.SOUTHWEST
                movement_dict_queue[4].update(deepcopy(movement_dict))

            if W1 == W2 == None and W3 != None:
                # e) step 1
                movement_dict = {}
                movement_dict[self.modules[0][0].id] = Move.WEST
                movement_dict[self.modules[1][0].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # e) step 2
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.WEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

                # e) step 3
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.NORTHWEST
                movement_dict[self.modules[2][2].id] = Move.NORTHWEST
                movement_dict_queue[2].update(deepcopy(movement_dict))

                # e) step 4
                movement_dict = {}
                movement_dict[self.modules[2][2].id] = Move.WEST
                movement_dict[self.modules[0][2].id] = Move.SOUTHWEST
                movement_dict_queue[3].update(deepcopy(movement_dict))

            if W1 != W2 == None != W3:
                # f) step 1
                movement_dict = {}
                movement_dict[self.modules[1][0].id] = Move.WEST
                movement_dict[self.modules[2][1].id] = Move.NORTHWEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # f) step 2
                movement_dict = {}
                movement_dict[self.modules[2][2].id] = Move.NORTHWEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

                # f) step 3
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.SOUTHWEST
                movement_dict_queue[2].update(deepcopy(movement_dict))

            if W1 != None and W2 != W3 == None:
                # f) step 1
                movement_dict = {}
                movement_dict[self.modules[2][0].id] = Move.WEST
                movement_dict[self.modules[2][1].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # f) step 2
                movement_dict = {}
                movement_dict[self.modules[2][2].id] = Move.NORTHWEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

                # f) step 3
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.SOUTHWEST
                movement_dict_queue[2].update(deepcopy(movement_dict))

            if W1 == None != W2 and W3 != None:
                # f) step 1
                movement_dict = {}
                movement_dict[self.modules[0][0].id] = Move.WEST
                movement_dict[self.modules[0][1].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))

                # f) step 2
                movement_dict = {}
                movement_dict[self.modules[0][2].id] = Move.SOUTHWEST
                movement_dict_queue[1].update(deepcopy(movement_dict))

                # f) step 3
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.NORTHWEST
                movement_dict_queue[2].update(deepcopy(movement_dict))

            if W1 != None and W2 != None and W3 != None:
                # g) step 1
                movement_dict = {}
                movement_dict[self.modules[1][2].id] = Move.WEST
                movement_dict_queue[0].update(deepcopy(movement_dict))


    def advance_move(self, move_number : int, moves : dict, movement_dict_queue, env):
        movement_dict = {}
        for id, direction in moves.items():
            movement_dict[id] = direction
        movement_dict_queue[move_number-1].update(deepcopy(movement_dict))
        self = MetaModule(self.x, self.y, env)
