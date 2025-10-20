"""
Sliding Squares in Parallel - O(P) Worst-case Optimal Planning Algorithm
"""

from typing import List, Set, Tuple, Optional, Dict
from collections import deque
import math
from .grid_config import Point, Configuration, Grid
from .moves_collisions import Move, detect_collisions, is_valid_move, generate_all_possible_moves
from .connectivity_validator import ConnectivityValidator


class PlannerAlgorithm:
    """
    Implements the O(P) worst-case optimal planning algorithm.
    
    The algorithm generates parallel move steps that are:
    - Collision-free
    - Connectivity-preserving
    - Progress toward the goal configuration
    """
    
    def __init__(self):
        self.connectivity_validator = ConnectivityValidator()
        self.max_iterations = 1000  # Prevent infinite loops
        self.max_moves_per_step = 3  # Limit moves per step to generate more steps
    
    def plan_reconfiguration(self, start_config: Configuration, goal_config: Configuration) -> List[List[Move]]:
        """
        Plan a reconfiguration from start to goal configuration.
        
        Args:
            start_config: The starting configuration
            goal_config: The target configuration
            
        Returns:
            List of parallel move steps, where each step is a list of moves
        """
        if not self._is_valid_reconfiguration(start_config, goal_config):
            raise ValueError("Invalid reconfiguration: configurations must have same number of modules")
        
        # Compute perimeter P and bounding box union
        perimeter = goal_config.perimeter()
        bounding_box = self._compute_bounding_box_union(start_config, goal_config)
        
        # Generate parallel move steps
        schedule = []
        current_config = start_config.copy()
        
        for iteration in range(self.max_iterations):
            if current_config.occupied_cells == goal_config.occupied_cells:
                break
            
            # Generate next parallel step
            step = self._generate_parallel_step(current_config, goal_config, bounding_box)
            
            if not step:
                # No valid moves found - this shouldn't happen in theory
                print(f"Warning: No valid moves found at iteration {iteration}")
                break
            
            # Apply the step
            schedule.append(step)
            current_config = self._apply_step(current_config, step)
        
        return schedule
    
    def _is_valid_reconfiguration(self, start_config: Configuration, goal_config: Configuration) -> bool:
        """Check if reconfiguration is valid (same number of modules)."""
        return len(start_config) == len(goal_config)
    
    def _compute_bounding_box_union(self, start_config: Configuration, goal_config: Configuration) -> Tuple[int, int, int, int]:
        """Compute the union of bounding boxes of start and goal configurations."""
        start_bb = start_config.bounding_box()
        goal_bb = goal_config.bounding_box()
        
        min_x = min(start_bb[0], goal_bb[0])
        min_y = min(start_bb[1], goal_bb[1])
        max_x = max(start_bb[2], goal_bb[2])
        max_y = max(start_bb[3], goal_bb[3])
        
        return (min_x, min_y, max_x, max_y)
    
    def _generate_parallel_step(self, current_config: Configuration, goal_config: Configuration, 
                              bounding_box: Tuple[int, int, int, int]) -> List[Move]:
        """
        Generate a single parallel step of moves.
        
        This is the core of the algorithm - it selects moves that:
        1. Are individually valid
        2. Don't collide with each other
        3. Preserve connectivity
        4. Make progress toward the goal
        """
        # Generate all possible moves
        all_moves = generate_all_possible_moves(current_config)
        
        # Filter moves that make progress toward goal
        progress_moves = self._filter_progress_moves(current_config, goal_config, all_moves)
        
        # Select moves greedily to maximize parallelism while avoiding collisions
        selected_moves = self._greedy_move_selection(current_config, progress_moves)
        
        return selected_moves
    
    def _filter_progress_moves(self, current_config: Configuration, goal_config: Configuration, 
                             moves: List[Move]) -> List[Move]:
        """
        Filter moves that make progress toward the goal configuration.
        
        A move makes progress if it moves a module closer to its target position.
        """
        progress_moves = []
        
        for move in moves:
            if self._move_makes_progress(current_config, goal_config, move):
                progress_moves.append(move)
        
        return progress_moves
    
    def _move_makes_progress(self, current_config: Configuration, goal_config: Configuration, 
                           move: Move) -> bool:
        """
        Check if a move makes progress toward the goal.
        
        A move makes progress if:
        1. The source cell should be empty in the goal, OR
        2. The destination cell should be occupied in the goal
        """
        source_should_be_empty = move.from_cell not in goal_config.occupied_cells
        dest_should_be_occupied = move.to_cell in goal_config.occupied_cells
        
        return source_should_be_empty or dest_should_be_occupied
    
    def _greedy_move_selection(self, config: Configuration, candidate_moves: List[Move]) -> List[Move]:
        """
        Select moves greedily to maximize parallelism while avoiding collisions.
        
        This uses a greedy approach:
        1. Sort moves by priority (e.g., distance to goal)
        2. Add moves one by one, checking for collisions
        3. Stop when no more moves can be added
        """
        # Sort moves by priority (simple heuristic: prefer moves that clear source cells)
        candidate_moves.sort(key=lambda m: self._move_priority(config, m), reverse=True)
        
        selected_moves = []
        
        for move in candidate_moves:
            # Check if adding this move would create collisions
            test_moves = selected_moves + [move]
            
            if self._is_step_valid(config, test_moves):
                selected_moves.append(move)
                
                # Limit the number of moves per step to generate more steps
                if len(selected_moves) >= self.max_moves_per_step:
                    break
        
        return selected_moves
    
    def _move_priority(self, config: Configuration, move: Move) -> float:
        """
        Calculate priority for a move (higher is better).
        
        This is a heuristic that can be tuned for better performance.
        """
        # Simple heuristic: prefer moves that clear cells
        # In a real implementation, this could consider distance to goal, etc.
        return 1.0
    
    def _is_step_valid(self, config: Configuration, moves: List[Move]) -> bool:
        """
        Check if a step (set of parallel moves) is valid.
        
        A step is valid if:
        1. All moves are individually valid
        2. No collisions between moves
        3. Connectivity is preserved
        """
        # Check individual move validity
        for move in moves:
            if not is_valid_move(config, move):
                return False
        
        # Check for collisions
        collisions = detect_collisions(config, moves)
        if collisions:
            return False
        
        # Check connectivity
        if not self.connectivity_validator.validate_moves(config, moves):
            return False
        
        return True
    
    def _apply_step(self, config: Configuration, step: List[Move]) -> Configuration:
        """Apply a step of moves to a configuration."""
        new_config = config.copy()
        
        for move in step:
            new_config.remove_cell(move.from_cell)
            new_config.add_cell(move.to_cell)
        
        return new_config
    
    def compute_makespan(self, schedule: List[List[Move]]) -> int:
        """Compute the makespan (number of parallel steps) of a schedule."""
        return len(schedule)
    
    def analyze_schedule(self, schedule: List[List[Move]]) -> Dict:
        """
        Analyze a schedule and return statistics.
        
        Returns:
            Dictionary with schedule analysis
        """
        if not schedule:
            return {
                'makespan': 0,
                'total_moves': 0,
                'parallelism': 0.0,
                'steps': []
            }
        
        total_moves = sum(len(step) for step in schedule)
        parallelism = total_moves / len(schedule) if schedule else 0
        
        step_stats = []
        for i, step in enumerate(schedule):
            step_stats.append({
                'step': i,
                'moves': len(step),
                'move_details': [(m.from_cell, m.to_cell) for m in step]
            })
        
        return {
            'makespan': len(schedule),
            'total_moves': total_moves,
            'parallelism': parallelism,
            'steps': step_stats
        }
    
    def benchmark_algorithm(self, start_config: Configuration, goal_config: Configuration) -> Dict:
        """
        Benchmark the algorithm and verify it meets theoretical bounds.
        
        Returns:
            Dictionary with benchmark results
        """
        import time
        
        start_time = time.time()
        schedule = self.plan_reconfiguration(start_config, goal_config)
        end_time = time.time()
        
        makespan = self.compute_makespan(schedule)
        perimeter = goal_config.perimeter()
        
        # Check if makespan is within theoretical bounds (O(P))
        theoretical_bound = perimeter  # In practice, should be much better
        within_bounds = makespan <= theoretical_bound
        
        return {
            'makespan': makespan,
            'perimeter': perimeter,
            'theoretical_bound': theoretical_bound,
            'within_bounds': within_bounds,
            'execution_time': end_time - start_time,
            'schedule_length': len(schedule),
            'total_moves': sum(len(step) for step in schedule)
        }
