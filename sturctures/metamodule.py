from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Sequence, Tuple
from .module import Module

@dataclass
class MetaModule:
    x: int = 0
    y: int = 0
    modules: Tuple[Tuple[Module]]

    def __init__(self, x, y, modules):
        self.x = x
        self.y = y
        self.modules = modules

    """Check if this structure is a MetaModule."""
    def is_valid(self) -> bool:
        """Check if metamodule is either solid or clean."""
        return self.is_solid() or self.is_clean()
    
    
    """Check if this MetaModule is a separator."""
    def is_separator(self, matrix) -> bool:
        empty_space_in_east_strip = False
        empty_space_in_east_strip_found = False
        num_of_collumns_in_east_strip = len(matrix[0]) - (self.x + 1)

        for i in num_of_collumns_in_east_strip:
            for j in 3:
                if matrix[self.y - 1 + j][self.x + 2 + i] == 0:
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