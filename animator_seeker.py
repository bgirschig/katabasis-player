from argparse import Namespace
import math
import random
from angles import look_at, rotation_distance, make_slerp
from dataset import DataObject, Dataset
import vlc
from rotation_animation import RotationAnimation
from utils import clamp, remap_range
from scipy.spatial.transform import Rotation
from utils import DEG_TO_RAD, RAD_TO_DEG, UP, DOWN, RIGHT, FORWARD, BACK

class ViewAnimator:
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
                self.anim = RotationAnimation(self.rotation, target_rotation, now, duration=distance*6/180)

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
