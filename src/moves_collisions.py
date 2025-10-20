"""
Sliding Squares in Parallel - Moves and Collision Detection
"""

from typing import Set, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from .grid_config import Point, Configuration


class CollisionType(Enum):
    """Types of collisions that can occur during parallel moves."""
    DIRECT = "direct"           # Two modules try to move to the same cell
    SWAP = "swap"              # Two modules try to swap positions
    CHAIN = "chain"            # Circular dependency in move sequence
    CONNECTIVITY = "connectivity"  # Move would disconnect the configuration


@dataclass
class Move:
    """Represents a single move from one cell to another."""
    from_cell: Point
    to_cell: Point
    
    def __hash__(self):
        return hash((self.from_cell, self.to_cell))
    
    def __eq__(self, other):
        return (isinstance(other, Move) and 
                self.from_cell == other.from_cell and 
                self.to_cell == other.to_cell)


@dataclass
class Collision:
    """Represents a detected collision."""
    collision_type: CollisionType
    moves: List[Move]
    description: str


def is_valid_move(config: Configuration, move: Move) -> bool:
    """
    Check if a single move is locally legal.
    
    A move is valid if:
    1. Source cell is occupied
    2. Destination cell is empty
    3. Source and destination are neighbors
    """
    # Check if source is occupied
    if move.from_cell not in config.occupied_cells:
        return False
    
    # Check if destination is empty
    if move.to_cell in config.occupied_cells:
        return False
    
    # Check if source and destination are neighbors
    if move.to_cell not in move.from_cell.neighbors():
        return False
    
    return True


def detect_direct_collisions(moves: List[Move]) -> List[Collision]:
    """Detect direct collisions where multiple moves target the same cell."""
    collisions = []
    target_cells = {}
    
    for move in moves:
        if move.to_cell in target_cells:
            # Direct collision detected
            collision = Collision(
                collision_type=CollisionType.DIRECT,
                moves=[target_cells[move.to_cell], move],
                description=f"Multiple moves target cell ({move.to_cell.x}, {move.to_cell.y})"
            )
            collisions.append(collision)
        else:
            target_cells[move.to_cell] = move
    
    return collisions


def detect_swap_collisions(moves: List[Move]) -> List[Collision]:
    """Detect swap collisions where two modules try to swap positions."""
    collisions = []
    move_map = {move.from_cell: move for move in moves}
    
    for move in moves:
        # Check if there's a move from the destination back to the source
        if move.to_cell in move_map:
            reverse_move = move_map[move.to_cell]
            if reverse_move.to_cell == move.from_cell:
                collision = Collision(
                    collision_type=CollisionType.SWAP,
                    moves=[move, reverse_move],
                    description=f"Swap collision between ({move.from_cell.x}, {move.from_cell.y}) and ({move.to_cell.x}, {move.to_cell.y})"
                )
                collisions.append(collision)
    
    return collisions


def detect_chain_collisions(moves: List[Move]) -> List[Collision]:
    """
    Detect chain collisions where moves form circular dependencies.
    
    This uses a graph-based approach to detect cycles in the move dependency graph.
    """
    collisions = []
    
    # Build dependency graph
    graph = {}
    for move in moves:
        if move.from_cell not in graph:
            graph[move.from_cell] = []
        graph[move.from_cell].append(move.to_cell)
    
    # Detect cycles using DFS
    visited = set()
    rec_stack = set()
    
    def has_cycle(node, path):
        if node in rec_stack:
            # Found a cycle
            cycle_start = path.index(node)
            cycle_path = path[cycle_start:] + [node]
            
            # Convert cycle to moves
            cycle_moves = []
            for i in range(len(cycle_path) - 1):
                from_cell = cycle_path[i]
                to_cell = cycle_path[i + 1]
                # Find the move that corresponds to this edge
                for move in moves:
                    if move.from_cell == from_cell and move.to_cell == to_cell:
                        cycle_moves.append(move)
                        break
            
            if cycle_moves:
                collision = Collision(
                    collision_type=CollisionType.CHAIN,
                    moves=cycle_moves,
                    description=f"Chain collision with {len(cycle_moves)} moves forming a cycle"
                )
                collisions.append(collision)
            return True
        
        if node in visited:
            return False
        
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        if node in graph:
            for neighbor in graph[node]:
                if has_cycle(neighbor, path):
                    return True
        
        rec_stack.remove(node)
        path.pop()
        return False
    
    # Check for cycles starting from each node
    for node in graph:
        if node not in visited:
            has_cycle(node, [])
    
    return collisions


def detect_connectivity_collisions(config: Configuration, moves: List[Move]) -> List[Collision]:
    """
    Detect connectivity collisions where moves would disconnect the configuration.
    
    This checks if removing the moving modules would disconnect the backbone.
    """
    collisions = []
    
    # Get the set of moving cells
    moving_cells = {move.from_cell for move in moves}
    
    # Create a temporary configuration without moving cells
    temp_config = config.copy()
    for cell in moving_cells:
        temp_config.remove_cell(cell)
    
    # Check if the remaining configuration is connected
    if not temp_config.is_connected():
        collision = Collision(
            collision_type=CollisionType.CONNECTIVITY,
            moves=moves,
            description=f"Connectivity collision: removing {len(moving_cells)} moving cells disconnects the configuration"
        )
        collisions.append(collision)
    
    return collisions


def detect_collisions(config: Configuration, moves: List[Move]) -> List[Collision]:
    """
    Detect all types of collisions in a set of parallel moves.
    
    Returns a list of all detected collisions.
    """
    all_collisions = []
    
    # Detect each type of collision
    all_collisions.extend(detect_direct_collisions(moves))
    all_collisions.extend(detect_swap_collisions(moves))
    all_collisions.extend(detect_chain_collisions(moves))
    all_collisions.extend(detect_connectivity_collisions(config, moves))
    
    return all_collisions


def is_collision_free(config: Configuration, moves: List[Move]) -> bool:
    """Check if a set of moves is collision-free."""
    return len(detect_collisions(config, moves)) == 0


def filter_valid_moves(config: Configuration, candidate_moves: List[Move]) -> List[Move]:
    """
    Filter a list of candidate moves to only include valid ones.
    
    This checks individual move validity but not collisions between moves.
    """
    valid_moves = []
    for move in candidate_moves:
        if is_valid_move(config, move):
            valid_moves.append(move)
    return valid_moves


def generate_all_possible_moves(config: Configuration) -> List[Move]:
    """
    Generate all possible valid moves from the current configuration.
    
    This is useful for planning algorithms that need to explore all options.
    """
    possible_moves = []
    
    for cell in config.occupied_cells:
        for neighbor in config.grid.get_neighbors(cell):
            if neighbor not in config.occupied_cells:
                move = Move(cell, neighbor)
                if is_valid_move(config, move):
                    possible_moves.append(move)
    
    return possible_moves
