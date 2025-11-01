from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Sequence, Tuple
from metamodule import MetaModule

@dataclass
class SweepLine:
    x: int = 0
    metamodules: List[MetaModule] = None

    def __init__(self, x, metamodules):
        self.x = x
        self.metamodules = metamodules

    """Check if this structure is a Sweepline."""
    def is_valid(self) -> bool:
        """Check if metamodules are aligned on the same x coordinate."""
        for metamodule in self.metamodules:
            if metamodule.x != self.x:
                return False
            
        """Check if all metamodules are valid."""
        for metamodule in self.metamodules:
            if not metamodule.is_valid():
                return False
            
        return True
            
    """Check if the Sweepline is a separator."""
    def is_separator(self) -> bool:
        """Check if all metamodules are separators."""
        for metamodule in self.metamodules:
            if not metamodule.is_separator():
                return False
        return True
    
    """Check if the Sweepline is solid."""
    def is_solid(self) -> bool:
        """Check if all metamodules are solid."""
        for metamodule in self.metamodules:
            if not metamodule.is_solid():
                return False
        return True
    
    """Check if the Sweepline is clean."""
    def is_clean(self) -> bool:
        """Check if all metamodules are clean."""
        for metamodule in self.metamodules:
            if not metamodule.is_clean():
                return False
        return True