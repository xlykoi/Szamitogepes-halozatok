from environment import Environment

class Metamodule:
    def __init__(self, center: dict, elements: list):
        self.center = center  # center is a dict with 'x' and 'y' keys
        elements.remove(center)
        self.elements = elements  # elements is a list of dicts with 'x' and 'y' keys

    def print_info(self):
        print(f"Metamodule Center: ({self.center[0]}, {self.center[1]})")
        print("Elements:")
        for elem in self.elements:
            print(f" - ({elem[0]}, {elem[1]})")

    def move_module(self, new_center: dict):
        old_x, old_y = self.center
        new_x, new_y = new_center

        # Calculate translation offset
        dx = new_x - old_x
        dy = new_y - old_y

        # Move all elements by that offset
        moved_elements = [(x + dx, y + dy) for (x, y) in self.elements]

        # Update internal state
        self.center = new_center
        self.elements = moved_elements

def searching_metamodules(min_x, max_x, min_y, max_y, occupied, left_over_robots,
                        stable_metamodule_center_coordinates, neighbors, missing_neigbors, metamodules):

    # deciding which leftover robots to move to the missing centers
    for x in range(min_x+3, max_x+1):
        for y in range(min_y, max_y+1):

            # potential center of future metamodule
            if (x % 3 == 1) and (y % 3 == 1):
                if (x, y) in left_over_robots:
                    print(f"x: {x}, y: {y} is a potential center")
                    count = 0

                    # Count all 3x3 neighbors (including diagonals)
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):

                            nx, ny = x + dx, y + dy
                            if (nx, ny) in occupied:
                                neighbors.append((nx, ny))
                                print("Neighbor found at: ", (nx, ny))
                                count += 1
                            else:
                                missing_neigbors.append((nx, ny))
                                print("Missing neighbor at: ", (nx, ny))

                    if len(neighbors) == 9:
                        metamodule = Metamodule((x,y), neighbors)
                        metamodule.print_info()
                        metamodules.append(metamodule)
                    stable_metamodule_center_coordinates[(x, y)] = count

    return stable_metamodule_center_coordinates, neighbors, missing_neigbors, metamodules

def compute_xy_monotonous_histogram_from_environment(env: Environment) -> dict:
    """
    Phase 4: Creating an XY monotonous Histogram from 
    the Y monotonous Histogram (with an empty west side),
    that got created from the Sweepying process in Phase 3.
    Updates env.grid.occupied.
    """
    metamodules = []

    occupied = set(env.grid.occupied.keys())
    if not occupied:
        return set()

    """Extended bounding box"""
    min_x = min(x for x, _ in occupied)
    max_x = max(x for x, _ in occupied)
    min_y = min(y for _, y in occupied)
    max_y = max(y for _, y in occupied)
    # Align (max_y - min_y) to multiple of 3
    if (max_y - min_y + 1) % 3 != 0:
        max_y += 3 - ((max_y - min_y + 1) % 3)
    total_mods = len(occupied)

    #for key in occupied:
    #    print(f"Occupied keys: {key}")

    # the x and y min an max koordinates that are occupied by a robot
    # total mods: the number of robots in the environment
    print(f"min_x: {min_x}, max_x: {max_x}, min_y: {min_y}, max_y: {max_y}, total_mods: {total_mods}")

    # --- Identify missing centers along the sweep line (x = 1) ---
    missing_centers = []

    # The sweep line meta-modules have centers spaced every 3 rows
    # We use the same grid alignment as the bounding box
    for y in range(min_y + 1, max_y + 1, 3):  # center row every 3 cells
        center = (1, y)  # x=1 → sweep line centers
        if center not in occupied:
            missing_centers.append(center)

    print(f"Missing centers on sweep line (x=1): {missing_centers}")
    missing_count = len(missing_centers)

    # identify the positions of the "left over robots" that are
    # not included in the west side sweepline
    left_over_robots = []

    for x in range(min_x+3, max_x+1):
        for y in range(min_y, max_y+1):
            pos = (x, y)
            if pos in occupied:
                left_over_robots.append(pos)

    left_over_count = len(left_over_robots)
    print(f"Leftover robots: {left_over_count}")

    stable_metamodule_center_coordinates = {}
    neighbors = []
    missing_neigbors = []

    stable_metamodule_center_coordinates, neighbors, missing_neigbors, metamodules = searching_metamodules(min_x, max_x, min_y, max_y, occupied,
                                                                        left_over_robots, stable_metamodule_center_coordinates,
                                                                        neighbors, missing_neigbors, metamodules)


    for (x, y), count in stable_metamodule_center_coordinates.items():
        print(f"Potential center at ({x}, {y}) has {count} neighbors.")

    for (x,y) in neighbors:
        print(f"Neighbors: ({x}, {y})")

    # fill in the missing centers with the leftover robots that are not neighbors
    counter = len(missing_centers)
    for robot in left_over_robots:
        if robot not in neighbors:
            print(f"Moving robot {robot} to fill missing center.")
            occupied.remove(robot)
            left_over_robots.remove(robot)
            occupied.add(missing_centers[0])
            counter -= 1
            print(f"Filled missing center at {missing_centers[0]}")
            print(str(counter))
            missing_centers.pop(0)
            if counter == 0:
                break

    missing_neighbor_count = len(missing_neigbors)
    still_missing_counter = missing_neighbor_count
    print(f"occupied list: {occupied}")
    for robot in left_over_robots:
        if robot not in neighbors:

            print(f"this robot will be moved: {robot}")
            if still_missing_counter > 0:
                occupied.add(missing_neigbors[still_missing_counter-1])
                print(f"still_missing_counter: {still_missing_counter}")
                still_missing_counter -= 1
                occupied.remove(robot)
            else:
                print("No more neighbors to fill.")
                break

    # mintha nem adna hozza uj metamodulet
    stable_metamodule_center_coordinates, neighbors, missing_neigbors, metamodules = searching_metamodules(min_x, max_x, min_y, max_y, occupied,
                                                                        left_over_robots, stable_metamodule_center_coordinates,
                                                                        neighbors, missing_neigbors, metamodules)
            

    return occupied

