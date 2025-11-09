from typing import Any, Callable, List, Optional, Sequence, Tuple
from .module import Module, Move

class MetaModule:
    x: int = 0
    y: int = 0
    modules: Tuple[Tuple[Optional[Module], ...]]

    def __init__(self, x, y, env):
        self.x = x
        self.y = y
        self.modules = ((env.find_module_at([x-1, y+1]), env.find_module_at([x, y+1]), env.find_module_at([x+1, y+1])),
                        (env.find_module_at([x-1, y]),   env.find_module_at([x, y]),   env.find_module_at([x+1, y])),
                        (env.find_module_at([x-1, y-1]), env.find_module_at([x, y-1]), env.find_module_at([x+1, y-1])))

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
                elif matrix[self.y - 1 + j][self.x + 2 + i] == 0:
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

    def clean(self, env, ui) -> None:
        # Clean the center module if it exists
        
        # Return if there is no center module
        center_module = self.modules[1][1]
        if center_module is None:
            return
        
        # Gather modules in the west strip of the metamodule
        west_strip_modules = []
        for module in env.modules.values():
            x, y = module.pos
            if x < self.x - 1 and abs(y - self.y) <= 1:
                west_strip_modules.append(module)

        west_strip_rows = [[],[],[]]
        for x in range(self.x - 2, -1, -1):
            module = env.find_module_at((x, self.y + 1))
            if module:
                west_strip_rows[0].append(module)

            module = env.find_module_at((x, self.y))
            if module:
                west_strip_rows[1].append(module)   
            
            module = env.find_module_at((x, self.y - 1))
            if module:
                west_strip_rows[2].append(module)
            
        if len(west_strip_rows[0]) > len(west_strip_rows[1]) == len(west_strip_rows[2]):
            # Trivial case: Push row 2 to the left
            movement_dict = {}
            for module in west_strip_rows[1]:
                movement_dict[module.id] = Move.WEST

            movement_dict[self.modules[1][1].id] = Move.WEST  # Move center module left
            movement_dict[self.modules[1][0].id] = Move.WEST  # Move left module left
        
        if len(west_strip_rows[0]) == len(west_strip_rows[1]) == len(west_strip_rows[2]):
            # Trivial case 2: Push row 2 to the left, and rotate the leftmost module up
            movement_dict = {}
            for i, module in enumerate(west_strip_rows[1]):
                if i != len(west_strip_rows[1]) - 1:
                    movement_dict[module.id] = Move.WEST
                else:
                    movement_dict[module.id] = Move.NORTHWEST

            movement_dict[self.modules[1][1].id] = Move.WEST  # Move center module left
            movement_dict[self.modules[1][0].id] = Move.WEST  # Move left module left
        
        env.transformation(movement_dict, ui)


    def advance(self, env, ui) -> None:
        # Advance the metamodule one step to the left
        return