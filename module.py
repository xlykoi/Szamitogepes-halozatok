from dataclasses import dataclass
from enum import Enum, auto


@dataclass
class Module:
    id: int
    pos: tuple[int, int]


class Move(Enum):
    STAY = (0, 0)
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self):
        return self.value
