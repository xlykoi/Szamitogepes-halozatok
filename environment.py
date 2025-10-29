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
        """Perform a synchronous movement step with global collision detection."""
        if not actions:
            return True

        # ---- 1️⃣ Mozgások kiszámítása
        moves: Dict[int, Tuple[Pos, Pos]] = {}
        for mid, mv in actions.items():
            mod = self.modules[mid]
            dx, dy = mv.delta
            tgt = (mod.pos[0] + dx, mod.pos[1] + dy)
            if not self.grid.in_bounds(tgt):
                print(f"Out of bounds move: {mid} -> {tgt}")
                return False
            moves[mid] = (mod.pos, tgt)

        # ---- 2️⃣ Globális ütközésellenőrzés
        collisions = detect_collisions(moves)
        if collisions:
            print("COLLISION DETECTED:")
            for c in collisions:
                print("  ", c)
            return False

        # ---- 3️⃣ Backbone (kapcsolódás) ellenőrzés
        moving = set(actions.keys())
        remaining = set(self.modules.keys()) - moving
        if remaining:
            adj = {mid: set() for mid in remaining}
            pos2mid = {
                m.pos: m.id
                for m in self.modules.values()
                if m.id in remaining
            }
            for mid in remaining:
                p = self.modules[mid].pos
                for q in self.grid.neighbors4(p):
                    if q in pos2mid:
                        adj[mid].add(pos2mid[q])
            start = next(iter(remaining))
            seen = {start}
            dq = collections.deque([start])
            while dq:
                u = dq.popleft()
                for v in adj[u]:
                    if v not in seen:
                        seen.add(v)
                        dq.append(v)
            if len(seen) != len(remaining):
                print("Connectivity would break — move cancelled.")
                return False

        
        for mid in moving:
            src = self.modules[mid].pos
            self.grid.remove(src)

        # új helyek lefoglalása
        for mid, (_, dst) in moves.items():
            if not self.grid.is_free(dst):
                print(f"Target {dst} is not free.")
                return False
            self.grid.place(mid, dst)
            self.modules[mid].pos = dst

        return True
