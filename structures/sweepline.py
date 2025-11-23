from dataclasses import dataclass
from typing import List
from .metamodule import MetaModule
from copy import deepcopy

@dataclass
class SweepLine:
    x: int = 0
    metamodules: List[MetaModule] = None

    def __init__(self, x, metamodules):
        
        print('Sweepline created at: ', x)
        self.x = x
        self.metamodules = metamodules

    """Check if this structure is a Sweepline."""
    def is_valid(self) -> bool:
        """Check if metamodules are aligned on the same x coordinate."""
        for metamodule in self.metamodules:
            if metamodule.x != self.x:
                return False
            
        """Check if all metamodules are valid."""
        for metamodule in self.metamodules:
            if not metamodule.is_valid():
                return False
            
        return True
            
    """Check if the Sweepline is a separator."""
    def is_separator(self, env) -> bool:
        """Check if all metamodules are separators."""
        for metamodule in self.metamodules:
            if not metamodule.is_separator(env):
                return False
        return True
    
    """Check if the Sweepline is solid."""
    def is_solid(self) -> bool:
        """Check if all metamodules are solid."""
        for metamodule in self.metamodules:
            if not metamodule.is_solid():
                return False
        return True
    
    """Check if the Sweepline is clean."""
    def is_clean(self) -> bool:
        """Check if all metamodules are clean."""
        for metamodule in self.metamodules:
            if not metamodule.is_clean():
                return False
        return True
    
    def full_diagnostic(self, env) -> None:
        print(f"SweepLine at x={self.x}:")
        print(f"  Valid: {self.is_valid()}")
        print(f"  Separator: {self.is_separator(env)}")
        print(f"  Solid: {self.is_solid()}")
        print(f"  Clean: {self.is_clean()}")
        for metamodule in self.metamodules:
            metamodule.full_diagnostic(env)

    def gather_east_strip(self, env, env_queue, i):
        movement_dict_queue = [{}]
        for metamodule in self.metamodules:
            metamodule.gather_east_strip(env, movement_dict_queue, i)

        for movement_dict in movement_dict_queue:
            if movement_dict != {}:
                env_queue.append(deepcopy(env.transformation(movement_dict)))

    def clean(self, env, env_queue) -> bool:
        done = True
        movement_dict_queue = [{}, {}]
        #Clean leading metamodules first
        for i, metamodule in enumerate(reversed(self.metamodules)):
            if i % 2 == 0:
                if not metamodule.clean(env, movement_dict_queue):
                    done = False
        for movement_dict in movement_dict_queue:
            if movement_dict != {}:
                env_queue.append(deepcopy(env.transformation(movement_dict)))
        
        movement_dict_queue = [{}, {}]
        #Clean trailing metamodules second
        for i, metamodule in enumerate(reversed(self.metamodules)):
            if i % 2 == 1:
                if not metamodule.clean(env, movement_dict_queue):
                    done = False
        for movement_dict in movement_dict_queue:
            if movement_dict != {}:
                env_queue.append(deepcopy(env.transformation(movement_dict)))

        return done


    def advance(self, env, env_queue) -> None:
        #Advance leading metamodules first
        movement_dict_queue = [{}, {}, {}, {}, {}]
        for i, metamodule in enumerate(self.metamodules):
            if i % 2 == 0:
                metamodule.advance(env, movement_dict_queue, True)

        for movement_dict in movement_dict_queue:
            if movement_dict != {}:
                env_queue.append(deepcopy(env.transformation(movement_dict)))

        #Advance trailing metamodules second
        movement_dict_queue = [{}, {}, {}, {}, {}]
        for i, metamodule in enumerate(self.metamodules):
            if i % 2 == 1:
                metamodule.advance(env, movement_dict_queue, False)

        for movement_dict in movement_dict_queue:
            if movement_dict != {}:
                env_queue.append(deepcopy(env.transformation(movement_dict)))