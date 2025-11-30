from .module import Module, Move
from typing import Any, Callable, List, Optional, Sequence, Tuple
class SnakeSegment:
    module: Module
    segment_ahead: Module
    last_move: Move

    def __init__(self, module, segment_ahead):
        self.module = module
        self.segment_ahead = segment_ahead
        self.last_move = Move.SOUTH

class SnakeHead(SnakeSegment):
    facing: Move
    def __init__(self, module, facing, env):
        super().__init__(module, None)
        self.env = env
        self.facing = facing

    def calculate_next_move(self):
        scan_dict = {
            Move.SOUTH: {
                'right': [-1, -1],
                'left': [1, -1],
                'ahead': [0, -1],
                'far_ahead': [0, -2],
                'left_flank' : [1, 0]
            },
            Move.WEST: {
                'right': [-1, 1],
                'left': [-1, -1],
                'ahead': [-1, 0],
                'far_ahead': [-2, 0],
                'left_flank' : [0, -1]
            },
            Move.EAST: {
                'right': [1, -1],
                'left': [1, 1],
                'ahead': [1, 0],
                'far_ahead': [2, 0],
                'left_flank' : [0, 1]
            }
        }
        print('-------------------------------------------------------facing', self.facing)
        print(scan_dict[self.facing])
        print(self.module.pos)
        print(self.module.id)
        deltas = scan_dict[self.facing]
        right_module = self.env.find_module_at([self.module.pos[0] + deltas['right'][0], self.module.pos[1] + deltas['right'][1]], check_for_oob=True)
        left_module = self.env.find_module_at([self.module.pos[0] + deltas['left'][0], self.module.pos[1] + deltas['left'][1]], check_for_oob=True)
        ahead_module = self.env.find_module_at([self.module.pos[0] + deltas['ahead'][0], self.module.pos[1] + deltas['ahead'][1]], check_for_oob=True)
        far_ahead_module = self.env.find_module_at([self.module.pos[0] + deltas['far_ahead'][0], self.module.pos[1] + deltas['far_ahead'][1]], check_for_oob=True)
        left_flank_module = self.env.find_module_at([self.module.pos[0] + deltas['left_flank'][0], self.module.pos[1] + deltas['left_flank'][1]], check_for_oob=True)

        print('right:', type(right_module))
        print('left:', type(left_module))
        print('ahead:', type(ahead_module))
        print('far ahead:', type(far_ahead_module))
        print('left flank:', type(left_flank_module))

        # Based on where the snake head is facing, and if it wants to go ahead, turn left or turn right
        # the values are the move that this function has to return and the direction the head must be facing after the movement
        head_move_dict = {
            Move.SOUTH: {
                'ahead': [Move.SOUTH, Move.SOUTH],
                'diagonal_left': [Move.SOUTHEAST, Move.EAST],
                'diagonal_right': [Move.SOUTHWEST, Move.WEST],
                'just_left': [Move.EAST, Move.EAST]
            },
            Move.WEST: {
                'ahead': [Move.WEST, Move.WEST],
                'diagonal_left': [Move.SOUTHWEST, Move.SOUTH],
                'diagonal_right': None,
                'just_left': [Move.SOUTH, Move.SOUTH]
            },
            Move.EAST: {
                'ahead': [Move.EAST, Move.EAST],
                'diagonal_left': None,
                'diagonal_right': [Move.SOUTHEAST, Move.SOUTH],
                'just_left': None
            }
        }

        head_move = head_move_dict[self.facing]

        move = None
        new_facing = None

        # If the bounding box end is reached
        if ahead_module == 'oob':
            print('reached bounding box end, remaking snake')
            return 'done'

        # Turn right on convex corner, or turn right to fill dead end
        elif not isinstance(right_module, Module) and not isinstance(left_module, Module) and not isinstance(ahead_module, Module):
            print('turning right on convex corner or dead end')
            move = head_move['diagonal_right'][0]
            new_facing = head_move['diagonal_right'][1]

        # Go ahead along smooth wall
        elif not isinstance(left_module, Module) and not isinstance(ahead_module, Module) and not isinstance(far_ahead_module, Module) and isinstance(right_module, Module):
            print('going ahead along smooth wall')
            move = head_move['ahead'][0]
            new_facing = head_move['ahead'][1]
        
        # Turn left on concave corner
        elif not isinstance(left_module, Module) and not isinstance(ahead_module, Module) and isinstance(right_module, Module) and isinstance(far_ahead_module, Module):
            print('turning left on concave corner')
            move = head_move['diagonal_left'][0]
            new_facing = head_move['diagonal_right'][1]

        # Go deeper into dead end
        elif isinstance(left_module, Module) and isinstance(right_module, Module) and not isinstance(ahead_module, Module):
            print('going deeper into dead end')
            move = head_move['ahead'][0]
            new_facing = head_move['ahead'][1]

        # If reached the end of a dead end remake the snake with new head
        elif isinstance(left_module, Module) and isinstance(right_module, Module) and isinstance(ahead_module, Module) and isinstance(left_flank_module, Module):
            print('reached end of dead end, remaking snake')
            return 'remake_snake'
        
        #If after a right corner turn the snake runs into a corner, and has a left space to go into
        elif isinstance(right_module, Module) and isinstance(ahead_module, Module) and not isinstance(left_module, Module):
            print('after right corner turn, running into corner with left space to go into')
            move = head_move['diagonal_left'][0]
            new_facing = head_move['ahead'][1]

        #If after a right corner turn the snake runs into a corner, and has no left space to go into
        elif isinstance(left_module, Module) and isinstance(right_module, Module) and isinstance(ahead_module, Module) and not isinstance(left_flank_module, Module):
            print('after right corner turn, running into corner with no left space to go into')
            move = head_move['just_left'][0]
            new_facing = head_move['just_left'][1]
        
        if new_facing != None:
            self.facing = new_facing

        return move


class Snake:
    head: SnakeHead
    segments: List[SnakeSegment]

    def __init__(self, head, segments, env):
        self.head = head
        self.segments = segments
        self.env = env

    def movement_dict(self):
        movement_dict = {}
        move = self.head.calculate_next_move()
        if move == 'done':
            return 'done'
        if move == 'remake_snake':
            if len(self.segments) > 0:
                new_head_segment = self.segments.pop(0)
                new_head = SnakeHead(new_head_segment.module, self.head.facing, self.env)
                new_head.last_move = new_head_segment.last_move
                if len(self.segments) > 0:
                    self.segments[0].segment_ahead = new_head
                self.head = new_head
                print('||||||||||||||||||||||||||||||||||||||||||||||||||')
                return self.movement_dict()
            else:
                return None
        movement_dict[self.head.module.id] = move

        for segment in self.segments:
            movement_dict[segment.module.id] = segment.segment_ahead.last_move

            
        for segment in reversed(self.segments):
            segment.last_move = segment.segment_ahead.last_move
            
        self.head.last_move = move
        
        return movement_dict
