from typing import Dict, List, Tuple, Optional
import collections
from grid import Grid
from structures.module import Module, Move
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

    def find_module_at(self, pos: Pos) -> Optional[Module]:
        # accept list or tuple, normalize to tuple key for dict lookup
        try:
            key = tuple(pos)
        except TypeError:
            key = pos
        mid = self.grid.occupied.get(key)
        if mid is not None:
            return self.modules.get(mid)
        return None
    
    def matrix_from_environment(self) -> List[List[int]]:
        if not self.grid.occupied:
            return []

        occupied = set(self.grid.occupied.keys())
        min_x = min(x for x, _ in occupied)
        max_x = max(x for x, _ in occupied)
        min_y = min(y for _, y in occupied)
        max_y = max(y for _, y in occupied)

        rows = max_y - min_y + 1
        cols = max_x - min_x + 1
        matrix = [[0 for _ in range(cols)] for _ in range(rows)]

        for (x, y) in occupied:
            gui_x = x - min_x
            gui_y = max_y - y
            matrix[gui_y][gui_x] = 1

        return matrix
    
    def transformation(self, movement_dict: Dict[int, Move], ui):
        modules_to_move = {}
        for id in movement_dict.keys():
            modules_to_move[id] = self.modules[id]
            self.grid.remove(modules_to_move[id].pos)
        
        for id, move in movement_dict.items():
            dx, dy = move.delta
            new_pos = (modules_to_move[id].pos[0] + dx, modules_to_move[id].pos[1] + dy)

            self.grid.place(id, new_pos)
            self.pos = new_pos

        ui.update_matrix(self.matrix_from_environment())