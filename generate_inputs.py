import random
import os

def generate_input(module_num):
    for i in range(100):
        modules = []
        modules.append([4, 4])
        max_x = 0
        max_y = 0
        while len(modules) < module_num:
            module_idx = random.randrange(0, len(modules))
            module =  modules[module_idx]
        
            direction = random.randrange(1, 5)

            if direction == 1:
                new_module = [module[0]+1, module[1]]
            elif direction == 2:
                new_module = [module[0]-1, module[1]]
            elif direction == 3:
                new_module = [module[0], module[1]+1]
            elif direction == 4:
                new_module = [module[0], module[1]-1]

            if new_module[0] > max_x:
                max_x = new_module[0]

            if new_module[1] > max_y:
                max_y = new_module[1]

            if new_module not in modules and new_module[0] >= 0 and new_module[1] >= 0:
                modules.append(new_module)

        filename = 'configurations/input-' + str(i) + '.txt'
        os.remove(filename)
        with open(filename, 'x') as f:
            for y in range(max_y+1):
                line = ''
                for x in range(max_x+1):
                    module = [x, y]
                    if module in modules:
                        line = line + '1'
                    else:
                        line = line + '0'
                
                f.write(line + '\n')


