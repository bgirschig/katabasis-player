from scipy.spatial.transform import Rotation
import time
from angles import make_slerp, look_at
from utils import UP, FORWARD, clamp
import math

class RotationAnimation:
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

    def is_done_at(self, time):
        return time >= self.end_time

    def get_forward_at(self, time):
        rot = self.get_rotation_at(time)
        return rot.apply([0,0,1])