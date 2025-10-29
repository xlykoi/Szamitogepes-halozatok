from dataclasses import dataclass

@dataclass
class Node:
    id: int = 0
    x: int = 0
    y: int = 0

    def move(self, dx: int = 0, dy: int = 0) -> None:
        """Move this node in-place by (dx, dy)."""
        self.x += dx
        self.y += dy

    def moved(self, dx: int = 0, dy: int = 0) -> "Node":
        """Return a new Node moved by (dx, dy)."""
        return Node(self.x + dx, self.y + dy)