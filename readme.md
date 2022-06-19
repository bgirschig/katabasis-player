# katabasis player

A 360 video player that tracks objects in the video (points are pre-computed in a csv dataset)

## Install
```bash
# Recommended: Install dependencies in a virtual env
python3 -m venv env
source env/bin/activate

pip install -r requirements.txt
```

## Run
```bash
source env/bin/activate
python main.py path/to/video.mp4 path/to/data.csv
```

## Dataset format
name     | description
---------|------------
frame    | frame index of this point
point_id | object index of this point (allows identifying the same object across frames)
x        | x coordinate of the point
y        | y coordinate of the point
z        | z coordinate of the point