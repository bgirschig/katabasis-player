from scipy.spatial.transform import Rotation
from scipy.spatial import geometric_slerp
from angles import FORWARD, look_at

# Z is forward, Y is up
X, Y, Z = 0, 1, 2
FORWARD = [0,0,1]
UP = [0,1,0]

# Should be the identity quaternion: Looking forward, up is up
rot1 = look_at([0, 0, 1], [0, 1, 0])

# Looking mostly up, with a bit of "back". Camera's "up" Should be mostly "back"
rot2 = look_at([0, 1, -0.05], [0, 0, -1])

# check our rotations
print("rotation 1:\n", rot1.apply([FORWARD, UP]).round(2))
print("rotation 2:\n", rot2.apply([FORWARD, UP]).round(2))

# interpolate!
step_count = 100
for step in range(0, step_count):
    time = step / step_count
    quaternion1 = rot1.as_quat()
    quaternion2 = rot2.as_quat()
    
    interp_quaternion = geometric_slerp(quaternion1, quaternion2, time)
    current_rotation = Rotation.from_quat(interp_quaternion)

    yaw, pitch, roll = current_rotation.as_euler('YXZ', degrees=True)
    
    print(*current_rotation.apply(FORWARD).round(4))
