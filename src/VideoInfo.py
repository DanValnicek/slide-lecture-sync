import hashlib
import json

from videohash2 import VideoHash
from pathlib import Path


class VideoInfo:
    def __init__(self, presentation_path, video_path):
        self.intervals: dict[tuple[int, int]] = dict()
        # self.video_hash = VideoHash(path=video_path, storage_path=Path(__file__).parent.__str__(), frame_interval=0.1)
        with open(presentation_path, 'rb') as f:
            self.presentation_hash = hashlib.sha256(f.read()).digest()

    def add_mapping_continuous(self, slide_id, timestamp_msec):
        slide_intervals = self.intervals.setdefault(slide_id, [])
        if slide_intervals == [] or timestamp_msec - slide_intervals[-1][1] > 1000:
            slide_intervals.append((timestamp_msec, timestamp_msec))
            return
        slide_intervals[-1] = (slide_intervals[-1][0], timestamp_msec)

    def toJSON(self):
        # Convert tuple keys to a string representation and bytes to hex.
        intervals_serialized = {
            str(key): value for key, value in self.intervals.items()
        }
        data = {
            "intervals": intervals_serialized,
            "presentation_hash": self.presentation_hash.hex()
        }
        return json.dumps(data)

    def simplify(self):
        intervals_copy = self.intervals.copy()
        while intervals_copy != {}:
            min_time = min([start_time[0] for start_time in intervals_copy.values()])
