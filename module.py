# module.py
from dataclasses import dataclass
from enum import Enum

@dataclass
class Module:
    id: int
    pos: tuple[int, int]

    def move_to(self, new_pos: tuple[int, int], env):
        """Közvetlenül áthelyezi a modult a megadott pozícióba."""
        # Ensure new_pos is a tuple (not a list)
        if not isinstance(new_pos, tuple):
            new_pos = tuple(new_pos)
        if not env.grid.in_bounds(new_pos):
            raise ValueError(f"Target {new_pos} is out of bounds")
        if new_pos in env.grid.occupied:
            print(f"[WARN] Cell {new_pos} is occupied, overwriting")
            env.grid.remove(new_pos)
        # frissítés: régi hely törlése, új hely lefoglalása
        env.grid.remove(self.pos)
        env.grid.place(self.id, new_pos)
        self.pos = new_pos


class Move(Enum):
    STAY = (0, 0)
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self):
        return self.value
