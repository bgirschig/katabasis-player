from argparse import Namespace
import time
from angles import look_at
from dataset import Dataset
import vlc
from rotation_animation import RotationAnimation
from utils import DEG_TO_RAD, RAD_TO_DEG, UP, DOWN, RIGHT, FORWARD, BACK

X, Y, Z, W = 0, 1, 2, 3

# Try AGAIN the lookat and interpolation thingies, manually
class ViewAnimator:
    def __init__(self, dataset:Dataset, config:Namespace) -> None:
        self.viewpoint = vlc.libvlc_video_new_viewpoint()

        self.rotation = look_at(FORWARD, UP)
        self.start_rotation = look_at(FORWARD, UP)
        self.target_rotation = look_at(UP, BACK)
        self.start_time = time.time()
        
        self.anim = RotationAnimation(self.start_rotation, self.target_rotation, time.time(), duration=4)

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

