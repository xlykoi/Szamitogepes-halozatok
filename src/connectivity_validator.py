"""
Sliding Squares in Parallel - Connectivity and Backbone Validator
"""

from typing import Set, List, Optional
from collections import deque
from .grid_config import Point, Configuration
from .moves_collisions import Move


class ConnectivityValidator:
    """
    Validates that moves preserve backbone connectivity.
    
    The backbone is the set of modules that remain stationary during a move step.
    After removing moving modules, the backbone must remain connected.
    """
    
    def __init__(self):
        pass
    
    def has_connected_backbone(self, config: Configuration, moving_cells: Set[Point]) -> bool:
        """
        Check if the backbone (non-moving cells) remains connected.
        
        Args:
            config: The current configuration
            moving_cells: Set of cells that will be moved
            
        Returns:
            True if the backbone is connected, False otherwise
        """
        # If no cells are moving, the backbone is trivially connected
        if not moving_cells:
            return config.is_connected()
        
        # If all cells are moving, there's no backbone to check
        if len(moving_cells) == len(config.occupied_cells):
            return True
        
        # Create backbone by removing moving cells
        backbone_cells = config.occupied_cells - moving_cells
        
        # If backbone is empty, it's trivially connected
        if not backbone_cells:
            return True
        
        # Check connectivity of backbone using BFS
        return self._is_connected_subset(config.grid, backbone_cells)
    
    def _is_connected_subset(self, grid, cells: Set[Point]) -> bool:
        """
        Check if a subset of cells is connected using BFS.
        
        Args:
            grid: The grid containing the cells
            cells: Set of cells to check for connectivity
            
        Returns:
            True if the cells form a connected component
        """
        if not cells:
            return True
        
        # Start BFS from any cell in the subset
        start = next(iter(cells))
        visited = {start}
        queue = deque([start])
        
        while queue:
            current = queue.popleft()
            
            # Check all neighbors
            for neighbor in grid.get_neighbors(current):
                if neighbor in cells and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # Check if all cells were visited
        return len(visited) == len(cells)
    
    def validate_moves(self, config: Configuration, moves: List[Move]) -> bool:
        """
        Validate that a set of moves preserves backbone connectivity.
        
        Args:
            config: The current configuration
            moves: List of moves to validate
            
        Returns:
            True if all moves preserve connectivity, False otherwise
        """
        moving_cells = {move.from_cell for move in moves}
        return self.has_connected_backbone(config, moving_cells)
    
    def get_connected_components(self, config: Configuration, moving_cells: Set[Point]) -> List[Set[Point]]:
        """
        Get all connected components of the backbone.
        
        Args:
            config: The current configuration
            moving_cells: Set of cells that will be moved
            
        Returns:
            List of connected components (sets of points)
        """
        backbone_cells = config.occupied_cells - moving_cells
        
        if not backbone_cells:
            return []
        
        components = []
        visited = set()
        
        for cell in backbone_cells:
            if cell not in visited:
                # Start BFS from this cell
                component = set()
                queue = deque([cell])
                
                while queue:
                    current = queue.popleft()
                    if current in visited:
                        continue
                    
                    visited.add(current)
                    component.add(current)
                    
                    # Add unvisited neighbors
                    for neighbor in config.grid.get_neighbors(current):
                        if neighbor in backbone_cells and neighbor not in visited:
                            queue.append(neighbor)
                
                components.append(component)
        
        return components
    
    def find_bridge_cells(self, config: Configuration, moving_cells: Set[Point]) -> Set[Point]:
        """
        Find cells that are critical for maintaining connectivity.
        
        These are cells whose removal would disconnect the backbone.
        
        Args:
            config: The current configuration
            moving_cells: Set of cells that will be moved
            
        Returns:
            Set of bridge cells that are critical for connectivity
        """
        backbone_cells = config.occupied_cells - moving_cells
        bridge_cells = set()
        
        for cell in backbone_cells:
            # Temporarily remove this cell and check connectivity
            temp_backbone = backbone_cells - {cell}
            if temp_backbone and not self._is_connected_subset(config.grid, temp_backbone):
                bridge_cells.add(cell)
        
        return bridge_cells
    
    def can_move_cell(self, config: Configuration, cell: Point, target: Point) -> bool:
        """
        Check if moving a specific cell to a target position preserves connectivity.
        
        Args:
            config: The current configuration
            cell: The cell to move
            target: The target position
            
        Returns:
            True if the move preserves connectivity
        """
        if cell not in config.occupied_cells:
            return False
        
        if target in config.occupied_cells:
            return False
        
        # Create a temporary configuration with the move applied
        temp_config = config.copy()
        temp_config.remove_cell(cell)
        temp_config.add_cell(target)
        
        # Check if the resulting configuration is connected
        return temp_config.is_connected()
    
    def get_safe_moves(self, config: Configuration, candidate_moves: List[Move]) -> List[Move]:
        """
        Filter candidate moves to only include those that preserve connectivity.
        
        Args:
            config: The current configuration
            candidate_moves: List of candidate moves to filter
            
        Returns:
            List of moves that preserve connectivity
        """
        safe_moves = []
        
        for move in candidate_moves:
            if self.can_move_cell(config, move.from_cell, move.to_cell):
                safe_moves.append(move)
        
        return safe_moves
    
    def analyze_connectivity_impact(self, config: Configuration, moves: List[Move]) -> dict:
        """
        Analyze the connectivity impact of a set of moves.
        
        Args:
            config: The current configuration
            moves: List of moves to analyze
            
        Returns:
            Dictionary with connectivity analysis results
        """
        moving_cells = {move.from_cell for move in moves}
        
        # Get connected components before moves
        components_before = self.get_connected_components(config, set())
        
        # Get connected components after removing moving cells
        components_after = self.get_connected_components(config, moving_cells)
        
        # Find bridge cells
        bridge_cells = self.find_bridge_cells(config, moving_cells)
        
        return {
            'is_valid': self.has_connected_backbone(config, moving_cells),
            'components_before': len(components_before),
            'components_after': len(components_after),
            'bridge_cells': bridge_cells,
            'moving_cells_count': len(moving_cells),
            'backbone_size': len(config.occupied_cells) - len(moving_cells)
        }
