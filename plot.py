import matplotlib.pyplot as plt
import numpy as np

data = np.loadtxt('stats/step_counts.txt')
module_count = data[:, 1]
circumference = data[:, 2]
step_count = data[:, 3]
matrix_1 = data[:, 4]
matrix_2 = data[:, 5]
'''
# Find highest step count index for each unique circumference
unique_circumferences = np.unique(circumference)
highest_steps_indices = []
for c in unique_circumferences:
    indices = np.where(circumference == c)
    max_index = indices[0][np.argmax(step_count[indices])]
    highest_steps_indices.append(max_index)

# Plot all points
plt.scatter(circumference, step_count, label='Steps')

# Plot highest step counts with a different color
plt.scatter(circumference[highest_steps_indices], step_count[highest_steps_indices], color='red', label='Highest step count')

plt.xlabel('Kerület')
plt.ylabel('Lépésszám')
plt.title('Lépésszám')

'''
# Filter for module_count == 40
mask = module_count == 40
circ_40 = matrix_2[mask]

# Create histogram (recommended for continuous distribution)
plt.figure(figsize=(10, 6))
counts, bins, patches = plt.hist(circ_40, bins=100, edgecolor='black', alpha=0.7, rwidth=1.0, histtype='stepfilled')
plt.xlabel('Circumference')
plt.ylabel('Frequency')
plt.title('Circumference Distribution (module_count = 40)')
plt.grid(True, alpha=0.3)

plt.show()



