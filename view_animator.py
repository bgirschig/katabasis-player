from argparse import Namespace
from math import atan2, pi, sqrt
import math
from msilib import sequence
import random
import time
from angles import look_at
from dataset import DataObject, Dataset
import vlc
from utils import clamp, lerp, remap_range
from scipy.spatial.transform import Rotation, Slerp, RotationSpline
from scipy.spatial import geometric_slerp
import numpy as np

DEG_TO_RAD = pi / 180
RAD_TO_DEG = 180 / pi

X, Y, Z, W = 0, 1, 2, 3
UP = [0, 1, 0]

class ViewAnimator3:
    def __init__(self, dataset:Dataset, config:Namespace) -> None:
        self.config = config
        self.dataset = dataset
        self.current_object:DataObject = None

        self.fov = config.min_fov

        self.rotation = Rotation.identity()
        self.rotation_speed = Rotation.from_euler('xyz', [
            config.yaw_speed,
            config.pitch_speed,
            config.roll_speed,
        ], degrees=True)

        self.target_up = [0.0, 1.0, 0.0]
        self.target_rotation = Rotation.identity()
        self.current_target_start_time = -1

        self.viewpoint = vlc.libvlc_video_new_viewpoint()

    def get_viewpoint(self):
        yaw, pitch, roll = self.rotation.as_euler('YXZ', degrees=True)
        
        forward, up = self.rotation.apply([[0,0,1], [0,1,0]])
        print("YPR", yaw, pitch, roll, "   ", forward, up)

        self.viewpoint.contents.yaw = yaw
        self.viewpoint.contents.pitch = pitch
        self.viewpoint.contents.roll = roll
        self.viewpoint.contents.field_of_view = self.fov

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
            new_obj = random.choice(objects)
            print("chose next object: ", new_obj.id)
            return new_obj
        return None

    def update(self, frame:int, now:float, delta_time:float):
        # self.rotation = Rotation.from_quat(geometric_slerp(self.rotation.as_quat(), (self.rotation * self.rotation_speed).as_quat(), clamp(delta_time)))
        # self.rotation = self.rotation * self.rotation_speed
        
        if self.config.track_objects:
            self.update_object_tracker(frame, now, delta_time)

    def update_object_tracker(self, frame:int, now:float, delta_time:float):
        if (self.needs_new_object(frame, now, delta_time)):
            self.current_object = self.find_next_object(frame)
            if self.current_object:
                self.current_target_start_time = now
                dataPoint = self.current_object.get_frame(frame)

        if self.current_object:
            target_up = self.rotation.apply(UP)
            dataPoint = self.current_object.get_frame(frame)
            self.target_rotation = look_at(dataPoint.as_array(), target_up)

        if self.target_rotation is not None:
            lerp_time = 0.00021 * self.fov

            quat = geometric_slerp(self.rotation.as_quat(), self.target_rotation.as_quat(), clamp(lerp_time))
            rot = Rotation.from_quat(quat)
            if len(quat.shape) == 2:
                rot = rot[0]
            self.rotation = rot

    def animate_fov(self, now):
        if self.config.fov_speed == 0:
            self.fov = self.config.min_fov
        else:
            self.fov = remap_range(math.sin(now*1/self.config.fov_speed), -1, 1, self.config.min_fov, self.config.max_fov)

    def needs_new_object(self, frame, now, delta_time):
        if self.current_object is None: return True
        if self.current_object and now - self.current_target_start_time > 5: return True
        if not self.current_object.is_in_frame(frame): return True


ViewAnimator = ViewAnimator3