from argparse import Namespace
from math import atan2, pi, sqrt
import math
import random
import time
from dataset import DataObject, Dataset
import vlc
from utils import clamp, remap_range
from scipy.spatial.transform import Rotation, Slerp
import numpy as np
import quaternion

DEG_TO_RAD = pi / 180
RAD_TO_DEG = 180 / pi

# rotation_speed = quaternion.from_rotation_vector([0,0,10*DEG_TO_RAD])
# current_rotation = quaternion.from_euler_angles([0,0,0])
# print(quaternion.as_rotation_vector(current_rotation)*RAD_TO_DEG)

X, Y, Z = 0, 1, 2

class ViewAnimator:
    def __init__(self, dataset:Dataset, config:Namespace) -> None:
        self.dataset = dataset
        self.current_object:DataObject = None

        self.fov = 90

        self.rotation = quaternion.from_rotation_vector([0,0,0])
        self.rotation_speed = quaternion.from_rotation_vector([
            config.yaw_speed * DEG_TO_RAD,
            config.pitch_speed * DEG_TO_RAD,
            config.roll_speed * DEG_TO_RAD
        ])

        self.start_rotation = None
        self.target_rotation = None
        self.rotation_animation_start = -1
        self.rotation_animation_end = -1

        self.config = config

    def get_viewpoint(self):
        yaw, pitch, roll = quaternion.as_rotation_vector(self.rotation) * RAD_TO_DEG
        return vlc.VideoViewpoint(yaw, pitch, roll, self.fov)

    def look_at(self, x, y, z):
        self.rotation = Rotation.align_vectors([0,0,1], [x, y, z])

    def update_rotation_target(self, x, y, z):
        yaw = atan2(x, z)
        pitch = -atan2(y, sqrt(x**2 + z**2))
        roll = quaternion.as_rotation_vector(self.rotation)[2]

        self.target_rotation = quaternion.from_rotation_vector([yaw, pitch, 0])

    def animate_to_lookat(self, x, y, z, now, duration):
        self.update_rotation_target(x, y, z)
        self.start_rotation = self.rotation
        self.rotation_animation_start = now
        self.rotation_animation_end = now + duration

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
        self.rotation = quaternion.slerp(self.rotation, self.rotation * self.rotation_speed, 0, 1, delta_time)

        self.animate_fov(now)

        if self.config.track_objects:
            if (self.should_look_for_object(frame, now, delta_time)):
                self.current_object = self.find_next_object(frame)
                if self.current_object:
                    dataPoint = self.current_object.get_frame(frame)
                    self.animate_to_lookat(dataPoint.x, dataPoint.y, dataPoint.z, now, duration=1)

            if self.current_object:
                dataPoint = self.current_object.get_frame(frame)
                self.update_rotation_target(dataPoint.x, dataPoint.y, dataPoint.z)

            if self.start_rotation and self.target_rotation:
                animation_time = clamp(now, self.rotation_animation_start, self.rotation_animation_end)
                self.rotation = quaternion.slerp(
                    self.start_rotation,
                    self.target_rotation,
                    self.rotation_animation_start,
                    self.rotation_animation_end,
                    animation_time)

    def animate_fov(self, now):
        if self.config.fov_speed == 0:
            self.fov = self.config.min_fov
        else:
            self.fov = remap_range(math.sin(now*1/self.config.fov_speed), -1, 1, self.config.min_fov, self.config.max_fov)

    def should_look_for_object(self, frame, now, delta_time):
        if self.current_object is None: return True
        if self.current_object and now - self.rotation_animation_end > 5: return True
        if not self.current_object.is_in_frame(frame): return True

def lerp(vector_a, vector_b, time):
    output = []
    for idx in range(len(vector_a)):
        output.append(vector_a[idx] + (vector_b[idx]-vector_a[idx]) * time)
    return output