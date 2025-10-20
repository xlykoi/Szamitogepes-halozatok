"""
Sliding Squares in Parallel - Core Grid and Configuration Implementation
"""

from typing import Set, Tuple, List, Optional
import json
from dataclasses import dataclass


@dataclass
class Point:
    """Represents a 2D point with integer coordinates."""
    x: int
    y: int
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y
    
    def neighbors(self) -> List['Point']:
        """Get the 4-connected neighbors of this point."""
        return [
            Point(self.x - 1, self.y),
            Point(self.x + 1, self.y),
            Point(self.x, self.y - 1),
            Point(self.x, self.y + 1)
        ]


class Grid:
    """Represents a discrete 2D grid."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
    
    def is_valid(self, point: Point) -> bool:
        """Check if a point is within the grid bounds."""
        return 0 <= point.x < self.width and 0 <= point.y < self.height
    
    def get_neighbors(self, point: Point) -> List[Point]:
        """Get valid neighbors of a point within the grid."""
        neighbors = []
        for neighbor in point.neighbors():
            if self.is_valid(neighbor):
                neighbors.append(neighbor)
        return neighbors


class Configuration:
    """Represents a configuration of occupied cells on a grid."""
    
    def __init__(self, grid: Grid, occupied_cells: Set[Point]):
        self.grid = grid
        self.occupied_cells = occupied_cells.copy()
    
    def is_connected(self) -> bool:
        """Check if the configuration is connected using BFS."""
        if not self.occupied_cells:
            return True
        
        # Start BFS from any occupied cell
        start = next(iter(self.occupied_cells))
        visited = {start}
        queue = [start]
        
        while queue:
            current = queue.pop(0)
            for neighbor in self.grid.get_neighbors(current):
                if neighbor in self.occupied_cells and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return len(visited) == len(self.occupied_cells)
    
    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Return (min_x, min_y, max_x, max_y) of the bounding box."""
        if not self.occupied_cells:
            return (0, 0, 0, 0)
        
        xs = [p.x for p in self.occupied_cells]
        ys = [p.y for p in self.occupied_cells]
        return (min(xs), min(ys), max(xs), max(ys))
    
    def perimeter(self) -> int:
        """Calculate the perimeter (number of boundary edges) of the configuration."""
        if not self.occupied_cells:
            return 0
        
        perimeter = 0
        for cell in self.occupied_cells:
            for neighbor in self.grid.get_neighbors(cell):
                if neighbor not in self.occupied_cells:
                    perimeter += 1
        
        return perimeter
    
    def add_cell(self, point: Point) -> bool:
        """Add a cell to the configuration. Returns True if successful."""
        if not self.grid.is_valid(point) or point in self.occupied_cells:
            return False
        self.occupied_cells.add(point)
        return True
    
    def remove_cell(self, point: Point) -> bool:
        """Remove a cell from the configuration. Returns True if successful."""
        if point not in self.occupied_cells:
            return False
        self.occupied_cells.remove(point)
        return True
    
    def copy(self) -> 'Configuration':
        """Create a copy of this configuration."""
        return Configuration(self.grid, self.occupied_cells)
    
    def __len__(self):
        return len(self.occupied_cells)
    
    def __contains__(self, point: Point):
        return point in self.occupied_cells
    
    def __iter__(self):
        return iter(self.occupied_cells)


def load_configuration_from_json(filepath: str, grid: Grid) -> Configuration:
    """Load a configuration from a JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    occupied_cells = set()
    for cell_data in data.get('cells', []):
        point = Point(cell_data['x'], cell_data['y'])
        if grid.is_valid(point):
            occupied_cells.add(point)
    
    return Configuration(grid, occupied_cells)


def save_configuration_to_json(config: Configuration, filepath: str):
    """Save a configuration to a JSON file."""
    data = {
        'grid': {
            'width': config.grid.width,
            'height': config.grid.height
        },
        'cells': [{'x': p.x, 'y': p.y} for p in config.occupied_cells]
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
