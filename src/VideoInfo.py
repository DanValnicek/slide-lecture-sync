import json
import sys
from bisect import bisect
from pathlib import Path

from pypdf import PdfWriter, PdfReader
from pypdf.generic import ArrayObject, NameObject, DictionaryObject, NumberObject, TextStringObject

from src.PdfExtender import PdfExtender
from src.utils import ms_to_hms, hms_to_ms


class PresentationSlideIntervals:

    def __init__(self, pdf_path: Path | None = None):
        self.slide_intervals = dict()
        self.inverted_slide_intervals = list()
        if pdf_path is None:
            return
        pdf_reader = PdfReader(pdf_path.resolve())
        for slide in pdf_reader.pages:
            if PdfExtender.EXTENSION_NAME not in slide:
                continue
            if PdfExtender.INTERVALS_SUBKEY_NAME not in slide[PdfExtender.EXTENSION_NAME]:
                continue
            self.slide_intervals[slide.page_number] = slide[PdfExtender.EXTENSION_NAME][
                PdfExtender.INTERVALS_SUBKEY_NAME]

    def add_point_to_slides(self, slide_n, time_ms):
        if slide_n is None:
            return
        self.inverted_slide_intervals = []
        slide_int = self.slide_intervals.get(slide_n, [])
        for i, interval in enumerate(slide_int):
            start, end = interval
            if start <= time_ms <= end:
                return
            if abs(time_ms - end) <= 1000:
                slide_int[i][1] = time_ms
                return
            if abs(start - time_ms) <= 1000:
                slide_int[i][0] = time_ms
                return
        slide_int.append([time_ms, time_ms])
        self.slide_intervals[slide_n] = slide_int

    def are_empty(self):
        if self.slide_intervals is None or len(self.slide_intervals) == 0:
            return True
        return False

    def get_intervals(self, slide_number):
        intervals = self.slide_intervals.get(slide_number, [])
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

    def get_slide_from_position(self, position_msec):
        if self.inverted_slide_intervals is None or len(self.inverted_slide_intervals) == 0:
            self.inverted_slide_intervals = [
                (start, end, slide_id) for slide_id, interval_lists in self.slide_intervals.items()
                for start, end in interval_lists
            ]
            self.inverted_slide_intervals.sort(key=lambda x: x[0])
        i = bisect(self.inverted_slide_intervals, (position_msec, float('inf'), float('inf')))
        if i:
            candidate_slide = self.inverted_slide_intervals[i - 1]
            if candidate_slide[0] <= position_msec <= candidate_slide[1]:
                return candidate_slide[2]
        return None

    def compile_pdf_w_timestamps(self, original_pdf_path: Path, output_path: Path):
        writer = PdfWriter("new.pdf", original_pdf_path)
        PdfExtender.add_extension_info(writer)
        for i, intervals in self.slide_intervals.items():
            writer.pages[i][NameObject(PdfExtender.EXTENSION_NAME)] = DictionaryObject(
                {NameObject(PdfExtender.INTERVALS_SUBKEY_NAME): ArrayObject(
                    [ArrayObject([NumberObject(start), NumberObject(end)]) for start, end in intervals])}
            )
        with open(output_path, "wb") as f:
            writer.write(f)

    @staticmethod
    def from_JSON(json_str):
        data = json.load(json_str)  # Parse JSON
        intervals_serialized = data.get("intervals", {})
        slide_intervals = {
            int(key): [(hms_to_ms(t_s), hms_to_ms(t_e)) for t_s, t_e in value]
            for key, value in intervals_serialized.items()
        }
        presentation_intervals = PresentationSlideIntervals()
        presentation_intervals.slide_intervals = slide_intervals
        return presentation_intervals

    def to_JSON(self):
        intervals_serialized = {
            str(key): [[ms_to_hms(t_s), ms_to_hms(t_e)] for t_s, t_e in value] for key, value in
            self.slide_intervals.items()
        }
        data = {
            "intervals": intervals_serialized,
            # "presentation_hash": self.presentation_hash.hex()
        }
        return json.dumps(data)


if __name__ == '__main__':
    pdf_path = sys.argv[1]
    pres_intervals = PresentationSlideIntervals(Path(pdf_path))
    print(pres_intervals.to_JSON())
    pres_intervals.get_slide_from_position(0)
    readable_inverted = [(ms_to_hms(s), ms_to_hms(e), sl) for s, e, sl in pres_intervals.inverted_slide_intervals]
    print(readable_inverted)
