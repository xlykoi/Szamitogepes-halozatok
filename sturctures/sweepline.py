from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Sequence, Tuple
from node import Node
from metamodule import MetaModule

@dataclass
class SweepLine:
    x: int = 0
    metamodules: List[MetaModule] = None

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
            