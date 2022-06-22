import math
from turtle import forward
from scipy.spatial.transform import Rotation, Slerp, RotationSpline
import numpy as np
from math import asin, atan2, pi

X, Y, Z = 0,1,2
np.set_printoptions(suppress=True)

DEG_TO_RAD = pi / 180
RAD_TO_DEG = 180 / pi

def main():
    # rotation = Rotation.from_euler('xyz', [12, 45, 0], degrees=True)
    
    # forward, up  = rotation.apply([
    #     [0,0,1],
    #     [0,1,0],
    # ])
    # right = np.cross(up, forward)

    # # VERIFIED
    # new_rotation = Rotation.from_matrix([
    #     [right[X], up[X], forward[X]],
    #     [right[Y], up[Y], forward[Y]],
    #     [right[Z], up[Z], forward[Z]],
    # ])
    # print(rotation.as_euler("xyz", True).round(2))
    # print(new_rotation.as_euler("xyz", True).round(2))

    test_lookat([0,0,1])
    test_lookat([0,0,-1])
    test_lookat([1,0,0])
    test_lookat([-1,0,0])

def test_lookat(target, up=[0,1,0]):
    rotation = look_at(target, up)
    forward = [0,0,1]
    
    rotated_forward = rotation.apply(forward)
    print(target, up, rotated_forward.round(2))

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

def test():
    sequence = [
        [[0.2,0.2,111.1], [0.2,111.1,0.2], "front"],
        [[0.2,0.2,-111.1], [0.2,111.1,0.2], "back"],
        [[111.1,0.2,0.2], [0.2,111.1,0.2], "right"],
        [[-111.1,0.2,0.2], [0.2,111.1,0.2], "left"],
        [[0.2,111.1,0.2], [0.2,0.2,-111.1], "top"],
        [[0.2,-111.1,0.2], [0.2,0.2,-111.1], "bottom"],
    ]
    # sequence = [
    #     [[0,0,1], [0,1,0], "front"],
    #     [[0,0,-1], [0,1,0], "back"],
    #     [[1,0,0], [0,1,0], "right"],
    #     [[-1,0,0], [0,1,0], "left"],
    #     [[0,1,0], [0,0,1], "top"],
    #     [[0,-1,0], [0,0,1], "bottom"],
    # ]
    for target, up, label in sequence:
        rotation = look_at(target, up)
        
        new_forward = rotation.apply([0,0,1])
        new_up = rotation.apply([0,1,0])

        
        tests = np.array([
            Rotation.as_euler(rotation, 'xyz', degrees=True),
            Rotation.as_euler(rotation, 'xzy', degrees=True),
            Rotation.as_euler(rotation, 'yxz', degrees=True), #
            Rotation.as_euler(rotation, 'yzx', degrees=True), #
            Rotation.as_euler(rotation, 'zyx', degrees=True),
            Rotation.as_euler(rotation, 'zxy', degrees=True),
            Rotation.as_rotvec(rotation)*RAD_TO_DEG,
            get_YPR(rotation)*RAD_TO_DEG,
            Rotation.as_euler(rotation, 'zxz', degrees=True),
        ]).round(2)
        
        print("----")
        print(f"{label} {new_forward.round(2)} {new_up.round(2)}")
        print(tests)
        # print(rotation_to_axis_angle(rotation))
        # print(rotation_to_yaw_pitch_roll(rotation))
        # print(eulers)

def rotation_to_yaw_pitch_roll(rotation:Rotation):
    axis, angle = rotation_to_axis_angle(rotation)
    forward = rotation.apply([0,0,1])

    yaw = atan2(forward[X], forward[Z]) * RAD_TO_DEG
    pitch = asin(forward[Y]) * RAD_TO_DEG
    roll = angle

    return yaw, pitch, roll

def rotation_to_axis_angle(rotation:Rotation):
    q = rotation.as_quat()
    qx, qy, qz, qw = q
    # if w>1 acos and sqrt will produce errors, this cant happen if quaternion is normalised
    if (qw > 1):
        # q.normalise()
        pass

    angle = 2 * math.acos(qw)
    s = math.sqrt(1-qw*qw) # assuming quaternion normalised then w is less than 1, so term always positive.
    if (s < 0.001):
        return [qx, qy, qz], angle * RAD_TO_DEG
    else:
        return [qx / s, qy / s, qz / s], angle * RAD_TO_DEG

def get_YPR(rotation):
    k = getK(rotation)
    yaw = get_vector_yaw(k)
    pitch = get_vector_pitch(k)

    qX, qY, qZ, qW = rotation.as_quat()
    xx = qX * qX
    xy = qX * qY
    zz = qZ * qZ
    wz = qW * qZ
    roll = math.atan2(2 * (xy - wz), 1 - 2 * (xx + zz))

    return np.array([yaw, pitch, roll])

def getK(rotation:Rotation):
    qX, qY, qZ, qW = rotation.as_quat()
    xz = qX * qZ
    wy = qW * qY
    yz = qY * qZ
    wx = qW * qX
    xx = qX * qX
    yy = qY * qY

    return [
        2.0 * (xz - wy),
        2.0 * (yz + wx),
        1.0 - 2.0 * (xx + yy),
    ]

def get_vector_pitch(v):
    return -math.atan2(v[Y], math.sqrt(v[X] * v[X] + v[Z] * v[Z]))

def get_vector_yaw(v):
    return -math.atan2(v[X], v[Z])

# main()
test()