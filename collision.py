# collision.py
from sturctures.module import Move
from typing import Dict, Tuple, List
Pos = Tuple[int,int]

def detect_collisions(moves: Dict[int, Tuple[Pos, Pos]]) -> List[str]:
    """
    moves: {module_id: (src, dst)}
    Returns a list of strings describing detected collisions.
    """
    collisions = []
    ids = list(moves.keys())

    # (i) same target
    targets = {}
    for mid, (_, dst) in moves.items():
        if dst in targets:
            collisions.append(f"same target: {mid} and {targets[dst]} both to {dst}")
        targets[dst] = mid

    # (ii) swap
    for i in range(len(ids)):
        for j in range(i+1, len(ids)):
            a, b = ids[i], ids[j]
            src_a, dst_a = moves[a]
            src_b, dst_b = moves[b]
            if dst_a == src_b and dst_b == src_a:
                collisions.append(f"swap between {a} and {b}")

    # (iii) orthogonal cross
    for i in range(len(ids)):
        for j in range(i+1, len(ids)):
            a, b = ids[i], ids[j]
            src_a, dst_a = moves[a]
            src_b, dst_b = moves[b]
            dx_a, dy_a = dst_a[0]-src_a[0], dst_a[1]-src_a[1]
            dx_b, dy_b = dst_b[0]-src_b[0], dst_b[1]-src_b[1]
            # orthogonal if one horizontal, one vertical
            if dx_a*dx_b + dy_a*dy_b == 0:  
                # check if their paths cross
                if dst_a == dst_b or dst_a == src_b or dst_b == src_a:
                    collisions.append(f"orthogonal cross between {a} and {b}")

    # (iv) convex/slide interference placeholder (simple version)
    # In full model, would need intermediate path points.
    # Here we just check if a move "passes through" another's target.
    for i in range(len(ids)):
        for j in range(i+1, len(ids)):
            a, b = ids[i], ids[j]
            src_a, dst_a = moves[a]
            src_b, dst_b = moves[b]
            if abs(dst_a[0]-src_b[0]) <= 1 and abs(dst_a[1]-src_b[1]) <= 1:
                # they come too close (1-cell Manhattan distance)
                collisions.append(f"proximity between {a} and {b}")

    return collisions
