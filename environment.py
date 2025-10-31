from typing import Dict, List, Tuple
import collections
from grid import Grid
from module import Module, Move
from collision import detect_collisions   

Pos = Tuple[int, int]


class Environment:
    def __init__(self):
        self.grid = Grid()
        self.modules: Dict[int, Module] = {}

    def add_module(self, module: Module):
        if module.pos in self.grid.occupied:
            raise ValueError("Cell occupied")
        self.modules[module.id] = module
        self.grid.place(module.id, module.pos)

    def step(self, actions: Dict[int, Move]) -> bool:
        if not actions:
            return True

        # 1️⃣ Célpontok kiszámítása
        targets: Dict[int, Pos] = {}
        for mid, mv in actions.items():
            mod = self.modules[mid]
            dx, dy = mv.delta
            tgt = (mod.pos[0] + dx, mod.pos[1] + dy)

            # Ha kimegy a gridből, egyszerűen maradjon helyben
            if not self.grid.in_bounds(tgt):
                tgt = mod.pos
            targets[mid] = tgt

        # 2️⃣ Minden modult elmozdítunk
        # régi helyek törlése
        for mid in actions.keys():
            src = self.modules[mid].pos
            self.grid.remove(src)

        # új helyek beállítása
        for mid, tgt in targets.items():
            self.grid.place(mid, tgt)
            self.modules[mid].pos = tgt

        return True
