from argparse import Namespace
from math import atan2, pi, sqrt
import math
from msilib import sequence
import random
import time
from angles import look_at
from dataset import DataObject, Dataset
import vlc
from utils import clamp, remap_range
from scipy.spatial.transform import Rotation, Slerp, RotationSpline
from scipy.spatial import geometric_slerp
import numpy as np
import quaternion

DEG_TO_RAD = pi / 180
RAD_TO_DEG = 180 / pi

X, Y, Z = 0,1,2

zero_one = np.array([0,1])

class ViewAnimator1:
    def __init__(self, dataset, config) -> None:
        self.config = config
        self.yaw = 0
        self.pitch = 0
        self.roll = 0

    def update(self, frame:int, now:float, delta_time:float):
        self.yaw += self.config.yaw_speed * delta_time
        self.pitch += self.config.pitch_speed * delta_time
        self.roll += self.config.roll_speed * delta_time

    def get_viewpoint(self):
        return vlc.VideoViewpoint(self.yaw, self.pitch, self.roll, self.config.min_fov)

class ViewAnimator2:
    def __init__(self, dataset, config) -> None:
        self.fov = 120
        self.rotation = Rotation.identity()
        self.rotation_speed = Rotation.from_euler('xyz', [
            config.yaw_speed,
            config.pitch_speed,
            config.roll_speed,
        ], degrees=True)

    def update(self, frame:int, now:float, delta_time:float):
        self.rotation = Rotation.from_quat(geometric_slerp(self.rotation.as_quat(), (self.rotation * self.rotation_speed).as_quat(), delta_time))

    def get_viewpoint(self):
        yaw, pitch, roll = Rotation.as_euler(self.rotation, 'xyz', degrees=True)
        return vlc.VideoViewpoint(yaw, pitch, roll, self.fov)

class ViewAnimator3:
    def __init__(self, dataset:Dataset, config:Namespace) -> None:
        self.dataset = dataset
        self.current_object:DataObject = None

        self.fov = config.min_fov

        self.rotation = Rotation.identity()
        self.rotation_speed = Rotation.from_euler('xyz', [
            config.yaw_speed,
            config.pitch_speed,
            config.roll_speed,
        ], degrees=True)

        self.config = config
        self.frame = 0
        self.val = 0

        self.viewpoint = vlc.libvlc_video_new_viewpoint()
        self.target = np.array([-20.0,-1.0,-10.0])

    def get_viewpoint(self):
        return self.viewpoint
        forward = self.rotation.apply([0,0,1])
        up = self.rotation.apply([0,1,0])

        yaw, pitch, roll = Rotation.as_euler(self.rotation, 'yzx', degrees=True)

        print("----", forward.round(2), up.round(2))
        print(yaw, pitch, roll)
        # print(
        #     np.array([
        #         # Rotation.as_euler(self.rotation, 'xyz', degrees=True),
        #         # Rotation.as_euler(self.rotation, 'xzy', degrees=True),
        #         # Rotation.as_euler(self.rotation, 'yxz', degrees=True),
        #         # Rotation.as_euler(self.rotation, 'yzx', degrees=True),
        #         # Rotation.as_euler(self.rotation, 'zyx', degrees=True),
        #         # Rotation.as_euler(self.rotation, 'zxy', degrees=True),
        #     ]).round(2)
        # )
        return vlc.VideoViewpoint(yaw, pitch, roll, self.fov)

        # x, y, z, w = self.rotation.as_quat()
        # yaw = atan2(2.0*(y*z + w*x), w*w - x*x - y*y + z*z)
        # pitch = math.asin(-2.0*(x*z - w*y))
        # roll = atan2(2.0*(x*y + w*z), w*w + x*x - y*y - z*z) * RAD_TO_DEG
        # yaw, pitch, roll = yaw*RAD_TO_DEG, pitch*RAD_TO_DEG, roll*RAD_TO_DEG

        forward = self.rotation.apply([0,0,1])
        up = self.rotation.apply([0,1,0])
        yaw = atan2(forward[X], forward[Z]) * RAD_TO_DEG
        pitch = math.asin(-forward[Y]) * RAD_TO_DEG

        planeRightX = math.sin(yaw)
        planeRightY = -math.cos(yaw)
        roll = math.asin(up[X] * planeRightX + up[Y] * planeRightY)
        if (up[Z] < 0):
            roll = (0.0 <= roll) - (roll < 0.0) * pi - roll
        # roll_2 = w*RAD_TO_DEG
        # roll_3 = (time.time()*10)%360

        yaw, pitch, roll = self.get_ypr(forward, up)
        yaw, pitch, roll = -90, -90, 0

        print(forward.round(2), up.round(2), np.round([yaw, pitch, roll], 2))

        return vlc.VideoViewpoint(yaw, pitch, roll, self.fov)

    # def update_rotation_target(self, x, y, z):
    #     yaw = atan2(x, z)
    #     pitch = -atan2(y, sqrt(x**2 + z**2))
    #     roll = quaternion.as_rotation_vector(self.rotation)[2]

    #     self.target_rotation = quaternion.from_rotation_vector([yaw, pitch, 0])

    # def animate_to_lookat(self, x, y, z, now, duration):
    #     self.update_rotation_target(x, y, z)
    #     self.start_rotation = self.rotation
    #     self.rotation_animation_start = now
    #     self.rotation_animation_end = now + duration


    def find_next_object(self, frame, min_frames=20):
        if frame > len(self.dataset.frames):
            return None

        objects = self.dataset.frames[frame]
        objects = [obj for obj in objects if obj.remaining_frames(frame) > min_frames]
        if objects:
            print("choosen next object")
            return random.choice(objects)
        
        return None

    def update(self, frame:int, now:float, delta_time:float):
        anim = (now*10)%360

        self.viewpoint.contents.yaw = 0
        self.viewpoint.contents.pitch = anim
        self.viewpoint.contents.roll = 0
        self.viewpoint.contents.field_of_view = 110
        return

        sequence = [
            [[0.2,0.2,111.1], [0.2,111.1,0.2]], # front
            [[0.2,0.2,-111.1], [0.2,111.1,0.2]], # back
            [[111.1,0.2,0.2], [0.2,111.1,0.2]], # right
            [[-111.1,0.2,0.2], [0.2,111.1,0.2]], # left
            [[0.2,111.1,0.2], [0.2,0.2,111.1]], # top
            [[0.2,-111.1,0.2], [0.2,0.2,111.1]], # bottom
            [[1, 1, 1], [0, 1, 0]], # corner
        ]
        self.frame+=1
        if self.frame % 300 == 0:
            self.val = (self.val + 1) % len(sequence)
            target, up = sequence[self.val]
            self.rotation = look_at(target, up)

            print(
                np.array([
                    Rotation.as_euler(self.rotation, 'xyz', degrees=True),
                    Rotation.as_euler(self.rotation, 'xzy', degrees=True),
                    Rotation.as_euler(self.rotation, 'yxz', degrees=True),
                    Rotation.as_euler(self.rotation, 'yzx', degrees=True),
                    Rotation.as_euler(self.rotation, 'zyx', degrees=True),
                    Rotation.as_euler(self.rotation, 'zxy', degrees=True),
                ]).round(2)
            )

            forward = self.rotation.apply([0,0,1])
            up = self.rotation.apply([0,1,0])

            pitch, yaw, roll = Rotation.as_rotvec(self.rotation)*RAD_TO_DEG
            yaw, pitch, roll = Rotation.as_euler(self.rotation, 'yxz', degrees=True)
            print("----", forward.round(2), up.round(2))
            print(round(yaw, 2), round(pitch, 2), round(roll, 2))
            
            self.viewpoint.contents.yaw = -90
            self.viewpoint.contents.pitch = 90
            self.viewpoint.contents.roll = 90
            self.viewpoint.contents.field_of_view = 110
            # self.viewpoint = vlc.libvlc_video_new_viewpoint(yaw, pitch, roll, 110)

        # self.rotation = Rotation.from_quat(geometric_slerp(self.rotation.as_quat(), (self.rotation * self.rotation_speed).as_quat(), delta_time))
        # self.rotation *= self.rotation_speed
        self.animate_fov(now)
        return

        if self.config.track_objects:
            if (self.needs_new_object(frame, now, delta_time)):
                self.current_object = self.find_next_object(frame)

            if self.current_object:
                dataPoint = self.current_object.get_frame(frame)
                self.look_at(dataPoint.x, dataPoint.y, dataPoint.z)
                # self.look_at(dataPoint.x, dataPoint.y, dataPoint.z)
                # self.rotation = quaternion.slerp(
                #     self.rotation, target_rotation,
                #     0, 1, 1)
                # self.update_rotation_target(dataPoint.x, dataPoint.y, dataPoint.z)

        #     if self.start_rotation and self.target_rotation:
        #         animation_time = clamp(now, self.rotation_animation_start, self.rotation_animation_end)
        #         # quaternion.minimal_rotation()
        #         # self.rotation = quaternion.slerp(
        #         #     self.rotation,
        #         #     self.target_rotation,
        #         #     0,
        #         #     1,
        #         #     delta_time)

    def animate_fov(self, now):
        if self.config.fov_speed == 0:
            self.fov = self.config.min_fov
        else:
            self.fov = remap_range(math.sin(now*1/self.config.fov_speed), -1, 1, self.config.min_fov, self.config.max_fov)

    def needs_new_object(self, frame, now, delta_time):
        if self.current_object is None: return True
        if self.current_object and now - self.rotation_animation_end > 5: return True
        if not self.current_object.is_in_frame(frame): return True

# def quaternion_to_lookat(x, y, z, roll=0):
#     yaw = atan2(x, z)
#     pitch = -atan2(y, sqrt(x**2 + z**2))

#     return quaternion.from_rotation_vector([yaw, pitch, roll])

# def lerp(vector_a, vector_b, time):
#     output = []
#     for idx in range(len(vector_a)):
#         output.append(vector_a[idx] + (vector_b[idx]-vector_a[idx]) * time)
#     return output


ViewAnimator = ViewAnimator3