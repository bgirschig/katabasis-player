from argparse import Namespace
from copyreg import constructor
from math import atan2, pi, sqrt
import math
from msilib import sequence
import random
import time
from turtle import forward
from angles import look_at, rotation_distance
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
DOWN = [0, -1, 0]
RIGHT = [1, 0, 0]
FORWARD = [0, 0, 1]
BACK = [0, 0, -1]

# Try AGAIN the lookat and interpolation thingies, manually
class ViewAnimator4:
    def __init__(self, dataset:Dataset, config:Namespace) -> None:
        self.viewpoint = vlc.libvlc_video_new_viewpoint()

        self.rotation = look_at(FORWARD, UP)
        self.start_rotation = look_at(FORWARD, UP)
        self.target_rotation = look_at(UP, BACK)
        self.start_time = time.time()
        
        self.anim = RotAnimation(self.start_rotation, self.target_rotation, time.time(), duration=4)

    def get_viewpoint(self):
        yaw, pitch, roll = self.rotation.as_euler('YXZ', degrees=True)

        self.viewpoint.contents.yaw = yaw
        self.viewpoint.contents.pitch = pitch
        self.viewpoint.contents.roll = roll
        self.viewpoint.contents.field_of_view = 110

        return self.viewpoint

    def update(self, frame:int, now:float, delta_time:float):
        # lerp_time = (time.time() - self.start_time - 1) / 10
        self.rotation = self.anim.get_rotation_at(time.time())

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

        self.target_anim = None
        self.target_up = [0.0, 1.0, 0.0]
        self.target_rotation = Rotation.identity()
        self.current_target_start_time = -1

        self.viewpoint = vlc.libvlc_video_new_viewpoint()

    def get_viewpoint(self):
        yaw, pitch, roll = self.rotation.as_euler('YXZ', degrees=True)

        self.viewpoint.contents.yaw = yaw
        self.viewpoint.contents.pitch = pitch
        self.viewpoint.contents.roll = roll
        self.viewpoint.contents.field_of_view = self.fov

        return self.viewpoint

    def find_next_object(self, frame, min_frames=20):
        if frame > len(self.dataset.frames):
            return None

        objects = self.dataset.frames[frame]
        objects = [obj for obj in objects if obj.remaining_frames(frame) > min_frames]
        if objects:
            new_obj = random.choice(objects)
            return new_obj
        return None

    def update(self, frame:int, now:float, delta_time:float):
        self.rotation = make_slerp(self.rotation, self.rotation*self.rotation_speed)(clamp(delta_time))

        if self.config.track_objects:
            self.update_object_tracker(frame, now, delta_time)

    def update_object_tracker(self, frame:int, now:float, delta_time:float):
        up = self.rotation.apply(UP)
        if (self.needs_new_object(frame, now, delta_time)):
            self.current_object = self.find_next_object(frame, min_frames=50)
            if self.current_object:
                print("chose next object: ", self.current_object.id)
                self.current_target_start_time = now

                dataPoint = self.current_object.get_frame(frame)
                target_rotation = look_at(dataPoint.as_array(), up)
                distance = rotation_distance(self.rotation, target_rotation)
                self.anim = RotAnimation(self.rotation, target_rotation, now, duration=distance*6/180)

        if self.current_object and self.anim:
            dataPoint = self.current_object.get_frame(frame)
            self.target_rotation = look_at(dataPoint.as_array(), up)
            
            self.anim.update_target(self.target_rotation)
            self.target_rotation = self.anim.get_rotation_at(now)
            # self.target_rotation = None

        if self.target_rotation is not None:
            lerp_time = 0.04
            slerp = make_slerp(self.rotation, self.target_rotation)
            self.rotation = slerp(lerp_time)

    def animate_fov(self, now):
        if self.config.fov_speed == 0:
            self.fov = self.config.min_fov
        else:
            self.fov = remap_range(math.sin(now*1/self.config.fov_speed), -1, 1, self.config.min_fov, self.config.max_fov)

    def needs_new_object(self, frame, now, delta_time):
        if self.current_object is None: return True
        if self.current_object and now - self.current_target_start_time > 6: return True
        if not self.current_object.is_in_frame(frame): return True
        return False

class RotAnimation:
    def __init__(self, start_rotation:Rotation, end_rotation:Rotation, start_time=None, end_time=None, duration=None) -> None:
        self.start_time = start_time or time.time()
        self.end_time = end_time or self.start_time + duration
        self.duration = duration or end_time - self.start_time
        
        self.start_rotation = start_rotation
        self.end_rotation = end_rotation

        self.slerp = make_slerp(start_rotation, end_rotation)
    
    def update_target(self, new_rotation:Rotation):
        self.end_rotation = new_rotation
        self.slerp = make_slerp(self.start_rotation, self.end_rotation)

    def update_target_forward(self, forward):
        self.end_rotation = look_at(forward, UP)
        self.slerp = make_slerp(self.start_rotation, self.end_rotation)

    def smooth_time(self,time):
        return math.cos((time-1)*math.pi)*0.5+0.5

    def get_rotation_at(self, time):
        lerp_time = (time - self.start_time) / self.duration
        lerp_time = clamp(lerp_time)
        lerp_time = self.smooth_time(lerp_time)

        return self.slerp(lerp_time)

    def get_forward_at(self, time):
        rot = self.get_rotation_at(time)
        return rot.apply([0,0,1])

def make_slerp(rot1:Rotation, rot2:Rotation) -> Slerp:
    rots = Rotation.from_quat([
        rot1.as_quat(),
        rot2.as_quat(),
    ])
    return Slerp([0,1], rots)

ViewAnimator = ViewAnimator3