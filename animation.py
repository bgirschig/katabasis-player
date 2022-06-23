import time
import math
from utils import clamp, lerp

class Animation:
    def __init__(self, start_value, end_value, start_time=None, end_time=None, duration=None) -> None:
        self.start_time = start_time or time.time()
        self.end_time = end_time or self.start_time + duration
        self.duration = duration or end_time - self.start_time
        
        self.start_value = start_value
        self.end_value = end_value
    
    def update_target(self, new_target):
        self.end_rotation = new_target

    def smooth_time(self,time):
        return math.cos((time-1)*math.pi)*0.5+0.5

    def get_value_at(self, time):
        lerp_time = (time - self.start_time) / self.duration
        lerp_time = clamp(lerp_time)
        lerp_time = self.smooth_time(lerp_time)

        return lerp(self.start_value, self.end_value, lerp_time)

    def is_done_at(self, time):
        return time >= self.end_time