# module.py
from dataclasses import dataclass
from enum import Enum

class Move(Enum):
    STAY = (0, 0)
    NORTH = (0, 1)
    SOUTH = (0, -1)
    WEST = (-1, 0)
    EAST = (1, 0)
    NORTHWEST = (-1, 1)
    NORTHEAST = (1, 1)
    SOUTHWEST = (-1, -1)
    SOUTHEAST = (1, -1)

    @property
    def delta(self):
        return self.value

from dataclasses import dataclass, field

@dataclass
class Module:
    id: int
    _pos: tuple[int, int] = field(repr=False)

    def __post_init__(self):
        self.pos = self._pos  # Initialize using the property setter

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value: tuple[int, int]):
        self._pos = value
        print(f'Module {self.id} pos changed to {self._pos}')    

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


    def move(self, move: Move, env):
        dx, dy = move.delta
        new_pos = (self.pos[0] + dx, self.pos[1] + dy)
        self.move_to(new_pos, env)
