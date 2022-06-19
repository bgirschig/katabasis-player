from math import atan2, sqrt
import math
import random
import time
from dataset import DataObject, Dataset
import vlc
from utils import remap_range

X, Y, Z = 0, 1, 2

class ViewAnimator:
    def __init__(self, dataset:Dataset) -> None:
        self.dataset = dataset
        self.current_object:DataObject = None

        self.yaw = 0
        self.pitch = 0
        self.roll = 0
        self.fov = 90

        self.current_lookat = [0, 0, 1]
        self.target_lookat = [0, 0, 1]

        self.prev_time = time.time()

    def get_viewpoint(self):
        return vlc.VideoViewpoint(self.yaw, self.pitch, self.roll, self.fov)

    def look_at(self, x, y, z):
        self.yaw = atan2(x, z) / math.pi * 180
        self.pitch = -atan2(y, sqrt(x**2 + z**2)) / math.pi * 180

    def animate_to_lookat(self, x, y, z):
        self.target_lookat = [x, y, z]

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
        now = time.time()
        delta_t = now - self.prev_time
        self.prev_time = now

        if (self.current_object is None or not self.current_object.is_in_frame(frame)):
            self.current_object = self.choose_next_object(frame)
        
        self.target_lookat[Y] -= delta_t * 1
        if (self.current_object):
            dataPoint = self.current_object.get_frame(frame)
            self.animate_to_lookat(dataPoint.x, dataPoint.y, dataPoint.z)

        # update the actual lookat
        self.current_lookat = lerp(self.current_lookat, self.target_lookat, 0.1)
        self.look_at(self.current_lookat[X], self.current_lookat[Y], self.current_lookat[Z])

        self.fov = remap_range(math.sin(now/10), -1, 1, 60, 140)
        self.roll += 4*delta_t

def lerp(vector_a, vector_b, time):
    output = []
    for idx in range(len(vector_a)):
        output.append(vector_a[idx] + (vector_b[idx]-vector_a[idx]) * time)
    return output