import random
from rotation_animation import RotationAnimation
from utils import clamp, lerp, rand_range_gauss, remap_range
from scipy.spatial.transform import Rotation, Slerp, RotationSpline
from dataset import DataObject, Dataset
from argparse import Namespace
from angles import look_at, make_slerp, rotation_distance
import vlc
from utils import DEG_TO_RAD, RAD_TO_DEG, UP, DOWN, RIGHT, FORWARD, BACK
import time

X, Y, Z, W = 0, 1, 2, 3

MIN_TRACKING_TIMEOUT_DURATION = 5
MAX_TRACKING_TIMEOUT_DURATION = 13
MIN_ANIM_DURATION = 1

class ViewAnimator:
    def __init__(self, dataset:Dataset, config:Namespace) -> None:
        self.dataset = dataset
        self.config = config

        self.rotation_speed = Rotation.from_euler('xyz', [config.yaw_speed, config.pitch_speed, config.roll_speed], degrees=True)

        self.viewpoint = vlc.libvlc_video_new_viewpoint()
        self.rotation = Rotation.random()

        # state
        self.frame = 0
        self.now = time.time()
        self.target_rotation = Rotation.identity()

        # object tracking
        self.current_object:DataObject = None
        self.tracking_timeout = None
        self.anim = None

        self.fov = config.min_fov

    def get_viewpoint(self):
        yaw, pitch, roll = self.rotation.as_euler('YXZ', degrees=True)

        self.viewpoint.contents.yaw = yaw
        self.viewpoint.contents.pitch = pitch
        self.viewpoint.contents.roll = roll
        self.viewpoint.contents.field_of_view = self.fov

        return self.viewpoint

    def update(self, frame:int, now:float, delta_time:float):
        self.now = now
        self.frame = frame

        self.current_up = self.target_rotation.apply(UP)
 
        # find objects that are not too far from our current heading
        if self.should_look_for_object():
            self.current_object = None
            candidates = self.find_trackable_objects(max_rotation_distance=self.fov * 0.5)
            if candidates:
                # Select an object
                self.current_object = random.choice(candidates)
                
                # Find the target rotation to get to that object
                data_point = self.current_object.get_frame(frame)
                anim_target_rotation = look_at(data_point.as_array(), self.current_up)
                distance = rotation_distance(self.rotation, anim_target_rotation)
                
                # Set the tracking timeout (Max duration to track this object) 
                timeout_duration = rand_range_gauss(MIN_TRACKING_TIMEOUT_DURATION, MAX_TRACKING_TIMEOUT_DURATION)
                self.tracking_timeout = now + timeout_duration

                # Compute the animation duration. Depends on fov to make the "visual speed" more consistent
                animation_duration = max(MIN_ANIM_DURATION, distance*10/self.fov)

                # log into and create the actual animation
                print(f"""
Chose new object {self.current_object.id} out of {len(candidates)} choices
    Distance: {distance}°
    Tracking will last at most {timeout_duration}s
    Animation duration: {animation_duration}s
""".strip())
                self.anim = RotationAnimation(self.rotation, anim_target_rotation, now, duration=distance*10/self.fov)

        if self.should_look_for_object():
            self.fov = lerp(self.fov, self.config.max_fov, 0.15*delta_time)
        else:
            self.fov = lerp(self.fov, self.config.min_fov, 0.15*delta_time)

        if self.anim:
            if self.current_object:
                data_point = self.current_object.get_frame(frame)
                new_anim_target = look_at(data_point.as_array(), self.current_up)
                self.anim.update_target(new_anim_target)
            self.target_rotation = self.anim.get_rotation_at(now)
            if self.anim.is_done_at(now):
                print("anim is done")
                self.anim = None

        elif self.current_object:
            data_point = self.current_object.get_frame(frame)
            self.target_rotation = look_at(data_point.as_array(), self.current_up)

        self.target_rotation = make_slerp(self.target_rotation, self.target_rotation*self.rotation_speed)(clamp(delta_time))
        self.rotation = make_slerp(self.rotation, self.target_rotation)(0.1)

    def find_trackable_objects(self, max_rotation_distance = 60, min_remaining_frames = 45, allow_current=False) -> list[DataObject]:
        candidates = []
        for obj in self.dataset.get_frame(self.frame, 'empty'):
            if not allow_current and obj == self.current_object:
                continue
            data_point = obj.get_frame(self.frame)
            rotation = look_at(data_point.as_array(), self.current_up)
            distance = rotation_distance(self.rotation, rotation)
            if distance <= max_rotation_distance and obj.remaining_frames(self.frame) >= min_remaining_frames:
                candidates.append(obj)
        return candidates

    def should_look_for_object(self):
        if self.anim:
            return False
        if self.current_object is None:
            return True
        if (self.tracking_timeout and self.now >= self.tracking_timeout):
            print("Reached tracking timeout. Looking for new object")
            self.tracking_timeout = None
            return True
        if (self.current_object.remaining_frames(self.frame) <= 0):
            print("Current tracked object is no longer present. Looking for new object")
            return True

        return False