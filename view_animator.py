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

DEG_TO_RAD = pi / 180
RAD_TO_DEG = 180 / pi

X, Y, Z = 0,1,2

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
        yaw, pitch, roll = Rotation.as_euler(self.rotation, 'YXZ', degrees=True)

        self.viewpoint.contents.yaw = yaw
        self.viewpoint.contents.pitch = pitch
        self.viewpoint.contents.roll = roll
        self.viewpoint.contents.field_of_view = 110

        return self.viewpoint

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
        self.target += [0.1,0,0.1]
        self.rotation = look_at(self.target, [0,0,-1])

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


ViewAnimator = ViewAnimator3