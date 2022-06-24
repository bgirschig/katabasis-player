# Plot values recorded during a session. Ideally, this would be part of main.py
# but pyplot doesn't seem to like being called after a KeyboardInterrupt

import sys
import numpy as np
from matplotlib import pyplot as plt

data = np.load(sys.argv[1])
labels = ['time', 'frame', 'yaw', 'pitch', 'roll', 'fov']

time = data[:,0]
frame = data[:,1]

values = data[:,2:]
plt.figure()
plt.plot(time, values, label=labels[2:])
plt.legend()

plt.figure()
plt.plot(time, values[:,3])

plt.show()
