import json
from datetime import timedelta
from pathlib import Path
from pypdf import PdfWriter, PdfReader
from pypdf.generic import ArrayObject, NameObject, DictionaryObject, NumberObject

CUSTOM_EXTENSION_NAME = '/DANV_SlideVideoSync'
CUSTOM_INTERVALS_SUBKEY_NAME = "/SlideAppearanceIntervals"

class PresentationSlideIntervals:

    def __init__(self, pdf_path: Path | None = None):
        self.slide_intervals = dict()
        if pdf_path is None:
            return
        pdf_reader = PdfReader(pdf_path.resolve())
        for slide in pdf_reader.pages:
            if CUSTOM_EXTENSION_NAME not in slide:
                continue
            if CUSTOM_INTERVALS_SUBKEY_NAME not in slide[CUSTOM_EXTENSION_NAME]:
                continue
            self.slide_intervals[slide.page_number] = slide[CUSTOM_EXTENSION_NAME][CUSTOM_INTERVALS_SUBKEY_NAME]

    def add_point_to_slides(self, slide_n, time_ms):
        if slide_n is None:
            return
        slide_int = self.slide_intervals.get(slide_n, [])
        for i, interval in enumerate(slide_int):
            start, end = interval
            if abs(time_ms - end) <= 1000:
                slide_int[i][1] = time_ms
                return
            if abs(start - time_ms) <= 1000:
                slide_int[i][0] = time_ms
                return
            if start <= time_ms <= end:
                return
        slide_int.append([time_ms, time_ms])
        self.slide_intervals[slide_n] = slide_int

    def get_intervals(self, slide_number):
        intervals = self.slide_intervals[slide_number]
        intervals.sort(key=lambda x: x[0])
        i = 0
        while i < len(intervals) - 1:
            if intervals[i + 1][0] <= intervals[i][0] <= intervals[i + 1][1]:
                intervals[i][1] = intervals[i + 1][1]
                intervals.pop(i + 1)
            else:
                i += 1
        self.slide_intervals[slide_number] = intervals
        return intervals

    def compile_pdf_w_timestamps(self, original_pdf_path: Path, output_path: Path):
        writer = PdfWriter("new.pdf", original_pdf_path)
        for i, intervals in self.slide_intervals.items():
            writer.pages[i][NameObject("/DANV_SlideVideoSync")] = DictionaryObject(
                {NameObject(): ArrayObject(
                    [ArrayObject([NumberObject(start), NumberObject(end)]) for start, end in intervals])}
            )
        with open(output_path, "wb") as f:
            writer.write(f)

    def toJSON(self):
        intervals_serialized = {
            str(key): value for key, value in self.slide_intervals.items()
        }
        data = {
            "intervals": intervals_serialized,
            # "presentation_hash": self.presentation_hash.hex()
        }
        return json.dumps(data)

    @staticmethod
    def ms_to_hms(time_ms):
        return str(timedelta(milliseconds=time_ms))

    def to_json_human_readable(self):
        intervals_serialized = {
            str(key): [[self.ms_to_hms(t_s), self.ms_to_hms(t_e)] for t_s, t_e in value] for key, value in
            self.slide_intervals.items()
        }
        data = {
            "intervals": intervals_serialized,
            # "presentation_hash": self.presentation_hash.hex()
        }
        return json.dumps(data)
