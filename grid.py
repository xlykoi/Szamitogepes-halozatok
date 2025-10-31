from typing import Tuple, Dict, List, Optional


Pos = Tuple[int, int]


class Grid:
    def __init__(self, rows: Optional[int] = None, cols: Optional[int] = None):
        self.occupied: Dict[Pos, int] = {}
        self.rows = rows
        self.cols = cols

    def in_bounds(self, p: Pos) -> bool:
        if self.rows is None or self.cols is None:
            return True
        x, y = p
        return 0 <= x < self.cols and 0 <= y < self.rows

    def is_free(self, p: Pos) -> bool:
        return self.in_bounds(p) and p not in self.occupied

    def place(self, mid, p):
        """Helyezzen el egy modult. Ha a cella már foglalt, felülírjuk (vizuális mód)."""
        self.occupied[p] = mid

    def remove(self, p):
        """Eltávolít egy modult a cella ból."""
        self.occupied.pop(p, None)

    def move(self, mid: int, src: Pos, dst: Pos) -> None:
        if self.occupied.get(src) != mid:
            raise ValueError("Source mismatch")
        del self.occupied[src]
        self.occupied[dst] = mid

    def neighbors4(self, p: Pos) -> List[Pos]:
        x, y = p
        return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

    def neighbors8(self, p: Pos) -> List[Pos]:
        x, y = p
        return [
            (x + dx, y + dy)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if not (dx == 0 and dy == 0)
        ]
