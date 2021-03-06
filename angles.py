from scipy.spatial.transform import Rotation, Slerp
import numpy as np
from math import pi

X, Y, Z = 0,1,2
np.set_printoptions(suppress=True)

DEG_TO_RAD = pi / 180
RAD_TO_DEG = 180 / pi
UP = [0, 1, 0]
FORWARD = [0, 0, 1]

def main():
   pass

def look_at(target, up):
    z = norm(target)
    x = norm(np.cross(up, z))
    y = np.cross(z, x)

    rotation_matrix = np.array([
        [x[X], y[X], z[X]],
        [x[Y], y[Y], z[Y]],
        [x[Z], y[Z], z[Z]],
    ])

    return Rotation.from_matrix(rotation_matrix)

def norm(vector):
    return vector / np.linalg.norm(vector)

def rotation_distance(rot1:Rotation, rot2:Rotation) -> float:
    return (rot2 * rot1.inv()).magnitude() * RAD_TO_DEG

def make_slerp(rot1:Rotation, rot2:Rotation) -> Slerp:
    rots = Rotation.from_quat([
        rot1.as_quat(),
        rot2.as_quat(),
    ])
    return Slerp([0,1], rots)