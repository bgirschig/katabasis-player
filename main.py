import logging
import math
import os
from dataset import Dataset

from utils import remap_range, seconds_to_string
from view_animator import ViewAnimator
os.add_dll_directory(r"C:/Program Files/VideoLAN/VLC")

import vlc
import time

media_path = "../../media/sample.mp4"
media_path = "../../media/360_video_meta.mp4"
media_path = "c:/Users/basti/Documents/projects/Katabasis/object_detection/yolov5/runs/detect/exp13_360model/equirect_360.mp4"
# media_path = "c:/Users/basti/Documents/projects/Katabasis/tools/test_cubemap/test_cubemap.mp4"

dataset_path = "./data/360_prepped_data.csv"

LOGLEVEL = os.environ.get('LOG_LEVEL', 'WARNING').upper()
logging.basicConfig(level=LOGLEVEL)

player:vlc.MediaPlayer = None
dataset:Dataset = None
viewAnimator:ViewAnimator = None

orientation = [0,-90,0]
video_time_offset = -1
media_duration = -1
end_reached = False
media_fps = -1

def init():
    global dataset, viewAnimator

    dataset = Dataset(dataset_path)
    viewAnimator = ViewAnimator(dataset)

    init_player()

def init_player():
    global media_duration, player, media_fps

    player = vlc.MediaPlayer(media_path)
    player.set_fullscreen(True)
    player.play()

    # Attach event(s) to ssynchronize with the video
    em = player.event_manager()
    em.event_attach(vlc.EventType.MediaPlayerTimeChanged, onTimeChange)
    em.event_attach(vlc.EventType.MediaPlayerEndReached, onEnd)

    # Get media duration
    media = player.get_media()
    media.parse()
    media_duration = media.get_duration()/1000
    media_fps = player.get_fps()

    # player.set_position(0.5)
    # player.set_position(0.99)
    # player.set_position(0.03)

def update():
    global video_time_offset, end_reached

    # In case we reach the end of the video (before resetting time to 0), we need to "reload" the video
    if end_reached:
        player.set_media(player.get_media())
        player.play()
        end_reached = False
        video_time_offset = -1

    # Wait for the video to be loaded
    if media_duration == -1 or video_time_offset == -1:
        return

    now = time.time()
    video_time = now - video_time_offset
    current_frame = math.floor(video_time * media_fps)
    viewAnimator.update(current_frame)

    # Do a manual loop to make it as seamless as possible
    time_to_end = (media_duration-video_time)
    if (time_to_end < 0.5):
        player.set_position(0)
        video_time_offset = now

    logging.info(f"{seconds_to_string(video_time/1000)} ({video_time/media_duration*100:.2f}%) tte: {time_to_end:.2f}")

    player.video_update_viewpoint(viewAnimator.get_viewpoint(), True)

    time.sleep(1/30)

def onTimeChange(evt):
    global video_time_offset

    video_time = player.get_time()
    video_time_offset = time.time() - video_time/1000

def onEnd(event):
    global end_reached
    end_reached = True

def main():
    init()

    try:
        while True: update()
    except KeyboardInterrupt:
        pass

    print("clean exit")

main()