from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Sequence, Tuple
from node import Node

@dataclass
class MetaModule:
    x: int = 0
    y: int = 0
    nodes: List[Node] = None

    """Check if this structure is a MetaModule."""
    def is_valid(self) -> bool:
        """Check if there are at least 8 nodes."""
        if not self.nodes or len(self.nodes) < 8:
            return False
        
        """Check if 2 nodes have the same coordinates."""
        coords = [(n.x, n.y) for n in self.nodes]
        if len(coords) != len(set(coords)):
            return False

        """Possible coordiantes within the MetaModule."""
        offsets: List[Tuple[int, int]] = [
            (-1, -1), (-1, 0), (-1, 1), 
            (0, -1), (0, 0), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]

        """Check if all nodes are within the expected offsets."""
        for node in self.nodes:
            relative_x = node.x - self.x
            relative_y = node.y - self.y
            if (relative_x, relative_y) not in offsets:
                return False
            elif (relative_x, relative_y) == (0, 0) and len(self.nodes) == 8:
                return False

        return True