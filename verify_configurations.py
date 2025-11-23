"""
Script to verify all configurations in the configurations folder for connectivity.
"""
import os
from typing import Set, Tuple
from collections import deque

# Import connectivity check from skeleton
from sturctures.skeleton import is_connected

Pos = Tuple[int, int]
CONFIGURATIONS_DIR = "configurations"


def neighbors4_unbounded(p: Pos):
    """Return 4-connected neighbors without bounds checking."""
    x, y = p
    return [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]


def grid_to_config(grid, offset_x: int = 0, offset_y: int = 0) -> Set[Pos]:
    """
    Convert a grid format (matrix of 0s and 1s) to a position set.
    
    Args:
        grid: List of lists representing the grid (1 = occupied, 0 = empty)
        offset_x: X offset to add to positions
        offset_y: Y offset to add to positions
    
    Returns:
        Set of positions
    """
    config = set()
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == 1:
                config.add((x + offset_x, y + offset_y))
    return config


def load_configuration(filename: str) -> Set[Pos]:
    """
    Load a configuration from a file.
    Supports both grid format (0s and 1s) and positions format (x,y).
    
    Args:
        filename: Input filename
    
    Returns:
        Set of positions
    """
    # Try configurations folder first, then root directory, then direct path
    possible_paths = [
        os.path.join(CONFIGURATIONS_DIR, filename),
        filename,  # Root directory or direct path
    ]
    
    filepath = None
    for path in possible_paths:
        if os.path.exists(path):
            filepath = path
            break
    
    if filepath is None:
        raise FileNotFoundError(f"Configuration file not found: {filename}")
    
    config = set()
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
        
        if not lines:
            return config
        
        # Check if it's grid format (all lines contain only 0s and 1s)
        first_line = lines[0]
        if all(c in '01' for c in first_line):
            # Grid format
            grid = [[int(c) for c in line] for line in lines]
            config = grid_to_config(grid)
        else:
            # Positions format (x,y)
            for line in lines:
                if line:
                    x, y = map(int, line.split(','))
                    config.add((x, y))
    
    return config


def verify_configuration(config: Set[Pos]) -> tuple[bool, str]:
    """
    Verify that a configuration is connected.
    
    Args:
        config: Set of positions to verify
    
    Returns:
        Tuple of (is_connected, message)
    """
    if not config:
        return True, "Empty configuration"
    
    if len(config) == 1:
        return True, "Single module configuration"
    
    connected = is_connected(config)
    message = f"Configuration with {len(config)} modules is {'connected' if connected else 'NOT connected'}"
    
    return connected, message


def verify_all_configurations():
    """Verify all configuration files in the configurations folder."""
    if not os.path.exists(CONFIGURATIONS_DIR):
        print(f"Error: {CONFIGURATIONS_DIR} folder does not exist!")
        return
    
    # Get all .txt files in configurations folder
    config_files = [f for f in os.listdir(CONFIGURATIONS_DIR) if f.endswith('.txt')]
    config_files.sort()  # Sort alphabetically
    
    if not config_files:
        print(f"No configuration files found in {CONFIGURATIONS_DIR}/")
        return
    
    print("=" * 70)
    print(f"Verifying {len(config_files)} configuration files in {CONFIGURATIONS_DIR}/")
    print("=" * 70)
    print()
    
    connected_count = 0
    disconnected_count = 0
    error_count = 0
    
    for i, filename in enumerate(config_files, 1):
        try:
            config = load_configuration(filename)
            is_conn, message = verify_configuration(config)
            
            status = "✓ CONNECTED" if is_conn else "✗ NOT CONNECTED"
            print(f"[{i:2d}/{len(config_files)}] {status:15s} | {filename}")
            print(f"         {message}")
            
            if is_conn:
                connected_count += 1
            else:
                disconnected_count += 1
                print(f"         WARNING: This configuration violates connectivity requirement!")
            
            print()
            
        except FileNotFoundError:
            print(f"[{i:2d}/{len(config_files)}] ✗ FILE NOT FOUND | {filename}")
            error_count += 1
            print()
        except Exception as e:
            print(f"[{i:2d}/{len(config_files)}] ✗ ERROR         | {filename}")
            print(f"         Error: {e}")
            error_count += 1
            print()
    
    # Summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"Total files checked:     {len(config_files)}")
    print(f"✓ Connected:            {connected_count}")
    print(f"✗ Not connected:         {disconnected_count}")
    print(f"✗ Errors:                {error_count}")
    print()
    
    if disconnected_count == 0 and error_count == 0:
        print("🎉 SUCCESS: All configurations are connected!")
    elif disconnected_count > 0:
        print(f"⚠️  WARNING: {disconnected_count} configuration(s) are NOT connected!")
    if error_count > 0:
        print(f"❌ ERROR: {error_count} file(s) had errors during verification.")


if __name__ == '__main__':
    verify_all_configurations()

