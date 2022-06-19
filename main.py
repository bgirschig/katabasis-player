import logging
import math
import os
from dataset import Dataset
import argparse
from utils import seconds_to_string
from view_animator import ViewAnimator

try:
    o = os.add_dll_directory(r"C:/Program Files/VideoLAN/VLC")
except:
    print("could not add dll directory. Assuming it's not needed")

import vlc
import time

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument("media_path", help="the 360 video file")
parser.add_argument("dataset_path", help="the points dataset. Must contain the following columns: [frame,point_id,x,y,z]")
args = parser.parse_args()

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

    dataset = Dataset(args.dataset_path)
    viewAnimator = ViewAnimator(dataset)

    init_player()

def init_player():
    global media_duration, player, media_fps

    vlc_instance = vlc.Instance(['--video-on-top'])
    player = vlc_instance.media_player_new(args.media_path)
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
        print("reached end")
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