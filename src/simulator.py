"""
Sliding Squares in Parallel - Simulator
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
from .grid_config import Configuration, Point
from .moves_collisions import Move, detect_collisions, is_valid_move
from .connectivity_validator import ConnectivityValidator


@dataclass
class SimulationStep:
    """Represents a single step in the simulation."""
    step_number: int
    moves: List[Move]
    config_before: Configuration
    config_after: Configuration
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'step_number': self.step_number,
            'moves': [
                {
                    'from': {'x': m.from_cell.x, 'y': m.from_cell.y},
                    'to': {'x': m.to_cell.x, 'y': m.to_cell.y}
                }
                for m in self.moves
            ],
            'config_before': [{'x': p.x, 'y': p.y} for p in self.config_before.occupied_cells],
            'config_after': [{'x': p.x, 'y': p.y} for p in self.config_after.occupied_cells],
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class SimulationResult:
    """Represents the result of a complete simulation."""
    initial_config: Configuration
    final_config: Configuration
    steps: List[SimulationStep]
    success: bool
    error_message: Optional[str] = None
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'initial_config': [{'x': p.x, 'y': p.y} for p in self.initial_config.occupied_cells],
            'final_config': [{'x': p.x, 'y': p.y} for p in self.final_config.occupied_cells],
            'steps': [step.to_dict() for step in self.steps],
            'success': self.success,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'makespan': len(self.steps),
            'total_moves': sum(len(step.moves) for step in self.steps)
        }


class Simulator:
    """
    Simulates the execution of planned reconfiguration steps.
    
    The simulator executes a schedule step by step, logging all state changes
    and validating that each step is executed correctly.
    """
    
    def __init__(self, validate_steps: bool = True):
        """
        Initialize the simulator.
        
        Args:
            validate_steps: Whether to validate each step before execution
        """
        self.validate_steps = validate_steps
        self.connectivity_validator = ConnectivityValidator()
        self.simulation_history = []
    
    def run(self, initial_config: Configuration, schedule: List[List[Move]]) -> SimulationResult:
        """
        Run a complete simulation from initial configuration through the schedule.
        
        Args:
            initial_config: The starting configuration
            schedule: List of parallel move steps
            
        Returns:
            SimulationResult with complete simulation data
        """
        import time
        start_time = time.time()
        
        try:
            current_config = initial_config.copy()
            steps = []
            
            for step_number, step_moves in enumerate(schedule):
                # Validate step if requested
                if self.validate_steps:
                    if not self._validate_step(current_config, step_moves):
                        error_msg = f"Invalid step {step_number}: validation failed"
                        return SimulationResult(
                            initial_config=initial_config,
                            final_config=current_config,
                            steps=steps,
                            success=False,
                            error_message=error_msg,
                            execution_time=time.time() - start_time
                        )
                
                # Apply the step
                step_result = self.apply_step(current_config, step_moves, step_number)
                steps.append(step_result)
                
                # Update current configuration
                current_config = step_result.config_after
            
            execution_time = time.time() - start_time
            
            return SimulationResult(
                initial_config=initial_config,
                final_config=current_config,
                steps=steps,
                success=True,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return SimulationResult(
                initial_config=initial_config,
                final_config=current_config if 'current_config' in locals() else initial_config,
                steps=steps if 'steps' in locals() else [],
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
    
    def apply_step(self, config: Configuration, moves: List[Move], step_number: int) -> SimulationStep:
        """
        Apply a single step of moves to a configuration.
        
        Args:
            config: The current configuration
            moves: List of moves to apply in parallel
            step_number: The step number for logging
            
        Returns:
            SimulationStep with before/after states
        """
        # Create a copy of the configuration before applying moves
        config_before = config.copy()
        
        # Apply all moves
        config_after = config.copy()
        for move in moves:
            config_after.remove_cell(move.from_cell)
            config_after.add_cell(move.to_cell)
        
        # Create simulation step
        step = SimulationStep(
            step_number=step_number,
            moves=moves,
            config_before=config_before,
            config_after=config_after
        )
        
        # Add to history
        self.simulation_history.append(step)
        
        return step
    
    def _validate_step(self, config: Configuration, moves: List[Move]) -> bool:
        """
        Validate that a step can be safely applied.
        
        Args:
            config: The current configuration
            moves: List of moves to validate
            
        Returns:
            True if the step is valid, False otherwise
        """
        # Check individual move validity
        for move in moves:
            if not is_valid_move(config, move):
                return False
        
        # Check for collisions
        collisions = detect_collisions(config, moves)
        if collisions:
            return False
        
        # Check connectivity preservation
        if not self.connectivity_validator.validate_moves(config, moves):
            return False
        
        return True
    
    def log_state(self, config: Configuration, step_number: int, message: str = "") -> Dict[str, Any]:
        """
        Log the current state of the simulation.
        
        Args:
            config: The current configuration
            step_number: The current step number
            message: Optional message to include
            
        Returns:
            Dictionary with state information
        """
        state = {
            'step_number': step_number,
            'config': [{'x': p.x, 'y': p.y} for p in config.occupied_cells],
            'num_modules': len(config.occupied_cells),
            'is_connected': config.is_connected(),
            'perimeter': config.perimeter(),
            'bounding_box': config.bounding_box(),
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        return state
    
    def get_simulation_history(self) -> List[SimulationStep]:
        """Get the complete simulation history."""
        return self.simulation_history.copy()
    
    def clear_history(self):
        """Clear the simulation history."""
        self.simulation_history.clear()
    
    def save_simulation(self, result: SimulationResult, filepath: str):
        """
        Save a simulation result to a JSON file.
        
        Args:
            result: The simulation result to save
            filepath: Path to save the file
        """
        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
    
    def load_simulation(self, filepath: str) -> SimulationResult:
        """
        Load a simulation result from a JSON file.
        
        Args:
            filepath: Path to the file to load
            
        Returns:
            SimulationResult loaded from file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Reconstruct configurations
        initial_config = Configuration(
            grid=None,  # Will need to be set by caller
            occupied_cells={Point(p['x'], p['y']) for p in data['initial_config']}
        )
        
        final_config = Configuration(
            grid=None,  # Will need to be set by caller
            occupied_cells={Point(p['x'], p['y']) for p in data['final_config']}
        )
        
        # Reconstruct steps
        steps = []
        for step_data in data['steps']:
            moves = [
                Move(
                    from_cell=Point(m['from']['x'], m['from']['y']),
                    to_cell=Point(m['to']['x'], m['to']['y'])
                )
                for m in step_data['moves']
            ]
            
            config_before = Configuration(
                grid=None,
                occupied_cells={Point(p['x'], p['y']) for p in step_data['config_before']}
            )
            
            config_after = Configuration(
                grid=None,
                occupied_cells={Point(p['x'], p['y']) for p in step_data['config_after']}
            )
            
            step = SimulationStep(
                step_number=step_data['step_number'],
                moves=moves,
                config_before=config_before,
                config_after=config_after,
                timestamp=datetime.fromisoformat(step_data['timestamp'])
            )
            steps.append(step)
        
        return SimulationResult(
            initial_config=initial_config,
            final_config=final_config,
            steps=steps,
            success=data['success'],
            error_message=data.get('error_message'),
            execution_time=data['execution_time']
        )
    
    def verify_final_state(self, result: SimulationResult, expected_config: Configuration) -> bool:
        """
        Verify that the simulation reached the expected final state.
        
        Args:
            result: The simulation result
            expected_config: The expected final configuration
            
        Returns:
            True if the final state matches expected, False otherwise
        """
        return result.final_config.occupied_cells == expected_config.occupied_cells
    
    def get_statistics(self, result: SimulationResult) -> Dict[str, Any]:
        """
        Get statistics about a simulation result.
        
        Args:
            result: The simulation result
            
        Returns:
            Dictionary with simulation statistics
        """
        if not result.steps:
            return {
                'makespan': 0,
                'total_moves': 0,
                'parallelism': 0.0,
                'success_rate': 1.0 if result.success else 0.0,
                'execution_time': result.execution_time
            }
        
        total_moves = sum(len(step.moves) for step in result.steps)
        parallelism = total_moves / len(result.steps) if result.steps else 0
        
        return {
            'makespan': len(result.steps),
            'total_moves': total_moves,
            'parallelism': parallelism,
            'success_rate': 1.0 if result.success else 0.0,
            'execution_time': result.execution_time,
            'avg_moves_per_step': total_moves / len(result.steps) if result.steps else 0
        }
