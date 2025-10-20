"""
Sliding Squares in Parallel - Main Package

A Python implementation of the "Sliding Squares in Parallel" algorithm.
"""

__version__ = "1.0.0"
__author__ = "Sliding Squares Team"
__email__ = "team@slidingsquares.com"

# Core modules
from .grid_config import Grid, Configuration, Point
from .moves_collisions import Move, CollisionType, detect_collisions
from .connectivity_validator import ConnectivityValidator
from .planner_algorithm import PlannerAlgorithm
from .simulator import Simulator, SimulationResult, SimulationStep

__all__ = [
    # Core classes
    'Grid',
    'Configuration', 
    'Point',
    'Move',
    'CollisionType',
    'ConnectivityValidator',
    'PlannerAlgorithm',
    'Simulator',
    'SimulationResult',
    'SimulationStep',
    
    # Utility functions
    'detect_collisions',
    
    # Package info
    '__version__',
    '__author__',
    '__email__',
]