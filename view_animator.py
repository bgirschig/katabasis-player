from math import atan2, sqrt
import math
import random
import time
from dataset import DataObject, Dataset
import vlc

from utils import remap_range

class ViewAnimator:
    def __init__(self, dataset:Dataset) -> None:
        self.dataset = dataset
        self.target = None
        self.current_object:DataObject = None

        self.yaw = 0
        self.pitch = 0
        self.roll = 0
        self.fov = 90

        self.prev_time = time.time()
        self.look_at(0,0,1)

    def get_viewpoint(self):
        return vlc.VideoViewpoint(self.yaw, self.pitch, self.roll, self.fov)

    def look_at(self, x, y, z):
        self.yaw = atan2(x, z) / math.pi * 180
        self.pitch = -atan2(y, sqrt(x**2 + z**2)) / math.pi * 180

    def choose_next_object(self, frame, min_frames=20):
        if frame > len(self.dataset.frames):
            return None

        objects = self.dataset.frames[frame]
        objects = [obj for obj in objects if obj.remaining_frames(frame) > min_frames]
        if objects:
            print("choosen next object")
            return random.choice(objects)
        
        return None

    def update(self, frame:int):
        if (self.current_object is None or not self.current_object.is_in_frame(frame)):
            self.current_object = self.choose_next_object(frame)
        
        if (self.current_object):
            dataPoint = self.current_object.get_frame(frame)
            self.look_at(dataPoint.x, dataPoint.y, dataPoint.z)

        now = time.time()
        delta_t = now - self.prev_time
        self.prev_time = now

        self.fov = remap_range(math.sin(now/10), -1, 1, 60, 140)
        self.roll += 2*delta_t