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

    def find_module_at(self, pos: Pos, check_for_oob: bool = False):
        min_x, max_x, min_y, max_y = self.find_bounds()
        if pos[0] < min_x or pos[0] > max_x or pos[1] < min_y or pos[1] > max_y:
            print(pos, 'out of bounds')
            if check_for_oob:
                return 'oob'
            return None
        # accept list or tuple, normalize to tuple key for dict lookup
        for module in self.modules.values():
            if module.pos[0] == pos[0] and module.pos[1] == pos[1]:
                return module
        return None
    
    def matrix_from_environment(self) -> List[List[int]]:
        min_x, max_x, min_y, max_y = self.find_bounds()

        rows = max_y - min_y + 1
        cols = max_x - min_x + 1
        matrix = [[0 for _ in range(cols)] for _ in range(rows)]

        for module in self.modules.values():
            x = module.pos[0]
            y = module.pos[1]
            gui_x = x - min_x
            gui_y = max_y - y
            matrix[gui_y][gui_x] = 1

        return matrix
    
    def find_bounds(self) -> Tuple[int, int, int, int]:
        min_x = None
        max_x = None
        min_y = None
        max_y = None

        for module in self.modules.values():
            if min_x == None:
                min_x = module.pos[0]
            elif module.pos[0] < min_x:
                min_x = module.pos[0]

            if max_x == None:
                max_x = module.pos[0]
            elif module.pos[0] > max_x:
                max_x = module.pos[0]

            if min_y == None:
                min_y = module.pos[1]
            elif module.pos[1] < min_y:
                min_y = module.pos[1]

            if max_y == None:
                max_y = module.pos[1]
            elif module.pos[1] > max_y:
                max_y = module.pos[1]
        
        return [min_x, max_x, min_y, max_y]

    def transformation(self, movement_dict: Dict[int, Move]):
        modules_to_move = {}
        for id in movement_dict.keys():
            modules_to_move[id] = self.modules[id]
        
        for id, move in movement_dict.items():
            dx, dy = move.delta
            new_pos = (modules_to_move[id].pos[0] + dx, modules_to_move[id].pos[1] + dy)

            self.modules[id].pos = new_pos

        return self
        