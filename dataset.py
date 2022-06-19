import csv
from dataclasses import dataclass, field

@dataclass
class DataPoint:
    id: int = -1
    x: float = -1
    y: float = -1
    z: float = -1
    frame: int = -1

@dataclass
class DataObject:
    id: int = -1
    start_frame: int = -1
    end_frame: int = -1
    datapoints: list[DataPoint] = field(default_factory=list)
    duration: int = 0

    def get_frame(self, frame:int):
        return self.datapoints[frame - self.start_frame]

    def is_in_frame(self, frame:int):
        return frame > self.start_frame and frame < self.end_frame

    def remaining_frames(self, frame:int):
        return (self.start_frame + self.duration) - frame

class Dataset:
    def __init__(self, file_path) -> None:
        self.objects:dict[int, DataObject] = {}
        self.frames:list[list[DataObject]] = []
        self.load(file_path)
        pass
    
    def load(self, file_path):
        with open(file_path) as f:
            reader = csv.DictReader(f)
            for item in reader:
                frame = int(item["frame"])
                point_id = int(item["point_id"])
                x = float(item["x"])
                y = float(item["y"])
                z = float(item["z"])

                while len(self.frames) <= frame:
                    self.frames.append([])

                if point_id not in self.objects:
                    self.objects[point_id] = DataObject(id=point_id, start_frame=frame, end_frame=frame)
                else:
                    delta_since_last_frame = frame - self.objects[point_id].end_frame
                    if (delta_since_last_frame != 1): print("detected gap in frames")

                data_object = self.objects[point_id]
                data_point = DataPoint(id=point_id, x=x, y=y, z=z, frame=frame)

                self.frames[frame].append(data_object)

                self.objects[point_id].datapoints.append(data_point)

                self.objects[point_id].end_frame = frame
                self.objects[point_id].duration = frame - self.objects[point_id].start_frame

        print(f"loaded {len(self.objects)} objects across {len(self.frames)} frames")
