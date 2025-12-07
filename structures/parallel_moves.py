# parallel_moves.py
from copy import deepcopy
from typing import Set, Tuple, List, Dict, Optional
from environment import Environment
from structures.module import Move
from structures.skeleton import (
    _assign_modules_to_targets,
    _proposed_cardinal_step,
    _select_safe_moves,
    is_connected
)

Pos = Tuple[int, int]


def compute_parallel_moves(env: Environment,
                           target_positions: Set[Pos],
                           max_iters: int = 20000,
                           movable_ids: Optional[Set[int]] = None) -> List[Dict[int, Move]]:

    if not target_positions:
        return []

    working_env = deepcopy(env)
    steps: List[Dict[int, Move]] = []

    if set(working_env.grid.occupied.keys()) == set(target_positions):
        return steps

    prev_positions = None
    no_progress = 0
    MAX_NO_PROGRESS = 60

    for it in range(max_iters):
        cur_positions = set(working_env.grid.occupied.keys())
        if cur_positions == set(target_positions):
            break

        full_assignments = _assign_modules_to_targets(working_env, set(target_positions))

        if movable_ids is not None:
            assignments = {mid: tgt for mid, tgt in full_assignments.items() if mid in movable_ids}
        else:
            assignments = full_assignments

        proposals: Dict[int, Move] = {}
        for mid, tgt in assignments.items():
            if mid not in working_env.modules:
                continue
            src = working_env.modules[mid].pos
            mv = _proposed_cardinal_step(src, tgt)
            if mv is None or mv == Move.STAY:
                continue

            new_pos = (src[0] + mv.delta[0], src[1] + mv.delta[1])

            old_dist = abs(src[0] - tgt[0]) + abs(src[1] - tgt[1])
            new_dist = abs(new_pos[0] - tgt[0]) + abs(new_pos[1] - tgt[1])

            if new_dist < old_dist:
                proposals[mid] = mv

        if not proposals:
            if prev_positions == cur_positions:
                no_progress += 1
                if no_progress > MAX_NO_PROGRESS:
                    break
            else:
                no_progress = 0

            prev_positions = cur_positions.copy()
            continue

        selected = _select_safe_moves(working_env, proposals)

        if not selected:
            single_selected = None
            for mid, mv in proposals.items():
                test_pos = set(working_env.grid.occupied.keys())
                src = working_env.modules[mid].pos
                tgt = (src[0] + mv.delta[0], src[1] + mv.delta[1])

                test_pos.discard(src)
                test_pos.add(tgt)

                if is_connected(test_pos):
                    single_selected = {mid: mv}
                    break

            if single_selected is None:
                if prev_positions == cur_positions:
                    no_progress += 1
                    if no_progress > MAX_NO_PROGRESS:
                        break
                else:
                    no_progress = 0

                prev_positions = cur_positions.copy()
                continue

            selected = single_selected

        
        ok = working_env.step(deepcopy(selected))
        if not ok:
            no_progress += 1
            if no_progress > MAX_NO_PROGRESS:
                break
            prev_positions = cur_positions.copy()
            continue

        steps.append(selected.copy())

        new_positions = set(working_env.grid.occupied.keys())

        no_progress = no_progress + 1 if new_positions == cur_positions else 0
        prev_positions = new_positions.copy()

        if no_progress > MAX_NO_PROGRESS:
            break

        if new_positions == set(target_positions):
            break

    return steps
