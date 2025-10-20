# Sliding Squares Configuration Visualizer

A simple configuration visualizer for displaying modular robot configurations loaded from a text file.

## Files

- `step_by_step_visualizer.py` - Main configuration visualizer application
- `configurations.txt` - Configuration file containing module coordinates
- `src/` - Core algorithm modules (for reference):
  - `grid_config.py` - Grid and configuration classes
  - `moves_collisions.py` - Move validation and collision detection
  - `connectivity_validator.py` - Backbone connectivity validation
  - `planner_algorithm.py` - O(P) optimal planning algorithm
  - `simulator.py` - Step execution simulator
  - `__init__.py` - Package initialization

## How to Run

```bash
python step_by_step_visualizer.py
```

## Features

- **File-based Configuration Loading**: Loads configurations from `configurations.txt`
- **Clean Grid Visualization**: Displays modules as blue squares on an 8x8 grid
- **Configuration Information**: Shows module count, perimeter, connectivity, and bounding box
- **Read-only Display**: Configuration is purely visual (no interactive editing)
- **Reset Functionality**: Return to original loaded configuration

## Configuration File Format

The `configurations.txt` file should contain module coordinates in the format:

```
# Starting Configuration
# Format: Coordinates in format (x,y) separated by spaces

(3,3) (4,3) (5,3) (4,2) (4,4) (4,5) (2,2) (6,2) (2,5)
```

## Usage

1. **Create Configuration**: Edit `configurations.txt` with your desired module coordinates
2. **Run Application**: Execute `python step_by_step_visualizer.py`
3. **View Configuration**: The grid displays your configuration as blue squares
4. **Load New Configuration**: Click "Load Configuration" to reload from file
5. **Reset**: Click "Reset Configuration" to return to original loaded state

## Configuration Properties

The visualizer displays:

- **Module Count**: Number of occupied cells
- **Perimeter**: Number of boundary edges
- **Connectivity**: Whether all modules form a connected component
- **Bounding Box**: Minimum and maximum coordinates
