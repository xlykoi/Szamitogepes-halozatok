import matplotlib.pyplot as plt
import numpy as np

data = np.loadtxt('stats/step_counts.txt')
x = data[:, 1]
y = data[:, 2]

plt.scatter(x, y)  # Dots only, no lines
plt.xlabel('Extended bounding box kerülete')
plt.ylabel('Lépésszám')
plt.title('Algoritmus lépésszáma')
plt.show()